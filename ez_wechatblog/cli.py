import asyncio
import json
import logging
from pathlib import Path

import typer

import ez_wechatblog.fetcher.playwright_fetcher  # noqa: register
import ez_wechatblog.fetcher.camoufox_fetcher  # noqa: register
from ez_wechatblog.assets.manager import (
    AssetManager, HOST_REGISTRY, build_host_config,
)
from ez_wechatblog.fetcher.factory import FetcherFactory
from ez_wechatblog.parser.wechat_parser import WeChatParser
from ez_wechatblog.plugin_engine.manager import create_manager
from ez_wechatblog.publishers.base import Article
from ez_wechatblog.templates.manager import create_manager as create_template_manager
from ez_wechatblog.utils import ensure_dir, validate_url

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

app = typer.Typer(
    name="ez-wc",
    help="EZ_WeChatBlog — 微信公众号文章转 Markdown 工具",
    no_args_is_help=True,
)


def _parse_image_config(raw: str | None) -> dict:
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        config = {}
        for pair in raw.split(","):
            if "=" in pair:
                k, v = pair.split("=", 1)
                config[k.strip()] = v.strip()
        if not config:
            logger.warning("Failed to parse --image-config: %s", raw[:100])
        return config


def _build_image_host(host_type: str, config: dict):
    if host_type not in HOST_REGISTRY:
        available = list(HOST_REGISTRY.keys())
        raise ValueError(f"Unknown image host '{host_type}'. Available: {available}")
    host_config = build_host_config(host_type, cli_args=config)
    host_cls = HOST_REGISTRY[host_type]
    return host_cls(**host_config)


async def _convert_single(url: str, output_dir: Path, publisher_name: str,
                          fetcher_name: str, headless: bool,
                          download_images: bool, image_mode: str,
                          image_host_type: str | None,
                          image_host_config: dict | None,
                          template_name: str | None = None,
                          template_dir: Path | None = None) -> dict:
    try:
        url = validate_url(url)
    except ValueError as e:
        return {"url": url, "status": "error", "error": str(e)}

    output_dir = ensure_dir(output_dir)

    logger.info("Fetching article: %s", url)
    try:
        fetcher = FetcherFactory.create(fetcher_name, headless=headless)
    except Exception as e:
        return {"url": url, "status": "error", "error": f"Fetcher error: {e}"}
    try:
        html = await fetcher.fetch(url)
    except ImportError as e:
        return {"url": url, "status": "error", "error": f"Fetcher not available: {e}"}
    except Exception as e:
        return {"url": url, "status": "error", "error": f"Fetch failed: {e}"}
    finally:
        try:
            await fetcher.close()
        except Exception:
            pass

    logger.info("Parsing HTML...")
    parser = WeChatParser()
    try:
        markdown_body, meta, image_urls, raw_html = parser.parse(html, url=url)
    except ValueError as e:
        return {"url": url, "status": "error", "error": f"Parse failed: {e}"}
    except Exception as e:
        return {"url": url, "status": "error", "error": f"Parse error: {e}"}

    assets_dir = None
    if download_images and image_urls:
        logger.info("Processing %d images (mode: %s)...", len(image_urls), image_mode)
        try:
            host = None
            if image_mode == "remote" and image_host_type:
                host = _build_image_host(image_host_type, image_host_config or {})
            am = AssetManager(output_dir, assets_subdir="images", referer=url,
                              image_mode=image_mode, image_host=host)
            await am.download_all(image_urls)
            markdown_body = am.rewrite_markdown_images(markdown_body)
            assets_dir = am.assets_dir
        except Exception as e:
            logger.warning("Image processing failed: %s", e)
    elif image_urls:
        logger.info("Skipping image download (%d images found)", len(image_urls))

    try:
        if template_name:
            custom_dirs = [template_dir] if template_dir else None
            tm = create_template_manager(custom_dirs)
            if template_name.endswith(".html"):
                rendered = tm.render(template_name, raw_html, meta.to_dict())
            else:
                rendered = tm.render(template_name, markdown_body, meta.to_dict())
        else:
            rendered = parser.build_full_markdown(markdown_body, meta)
    except Exception as e:
        return {"url": url, "status": "error", "error": f"Template render failed: {e}"}

    article = Article(markdown=rendered, metadata=meta.to_dict(),
                      assets_dir=assets_dir)

    pm = create_manager()
    try:
        result = pm.publish(article, publisher_name, config={
            "output_dir": str(output_dir),
        })
    except Exception as e:
        return {"url": url, "status": "error", "error": f"Publish failed: {e}"}

    slug = result.get("slug", "?")
    path = result.get("path", "?")
    logger.info("Done: %s -> %s", slug, path)
    return {"url": url, "status": "ok", "slug": slug, "path": path}


@app.command()
def convert(
        url: str = typer.Argument(..., help="微信公众号文章 URL"),
        output: Path = typer.Option(
            "./output", "-o", "--output",
            help="输出目录",
            file_okay=False, dir_okay=True,
        ),
        publisher: str = typer.Option(
            "local", "-p", "--publisher",
            help="发布器名称 (local/hugo/hexo)",
        ),
        fetcher: str = typer.Option(
            "playwright", "--fetcher",
            help="抓取器 (playwright/camoufox)",
        ),
        headless: bool = typer.Option(
            True, "--headless/--show",
            help="是否使用无头浏览器",
        ),
        download_images: bool = typer.Option(
            True, "--images/--no-images",
            help="是否下载图片",
        ),
        image_mode: str = typer.Option(
            "local", "--image-mode",
            help="图片模式 (local/base64/remote)",
        ),
        image_host: str = typer.Option(
            None, "--image-host",
            help="图床类型 (oss/github/cloudinary)",
        ),
        image_config: str = typer.Option(
            None, "--image-config",
            help='图床配置 JSON 或 key=val',
        ),
        template: str = typer.Option(
            None, "-t", "--template",
            help="输出模板文件名",
        ),
        template_dir: Path = typer.Option(
            None, "--template-dir",
            help="自定义模板目录",
            file_okay=False, dir_okay=True,
        ),
        verbose: bool = typer.Option(
            False, "-v", "--verbose",
            help="详细日志输出",
        ),
):
    """将单篇微信公众号文章转换为 Markdown 并发布"""
    if verbose:
        logging.getLogger("ez_wechatblog").setLevel(logging.DEBUG)

    if image_mode == "remote" and not image_host:
        typer.echo("Error: --image-host is required when --image-mode=remote", err=True)
        raise typer.Exit(1)

    result = asyncio.run(_convert_single(
        url=url, output_dir=output, publisher_name=publisher,
        fetcher_name=fetcher, headless=headless,
        download_images=download_images, image_mode=image_mode,
        image_host_type=image_host,
        image_host_config=_parse_image_config(image_config),
        template_name=template, template_dir=template_dir,
    ))
    if result.get("status") == "error":
        typer.echo(f"Error: {result['error']}", err=True)
        raise typer.Exit(1)


@app.command()
def batch(
        urls: list[str] = typer.Argument(None, help="URL 列表或文件路径"),
        url_file: Path = typer.Option(
            None, "-f", "--url-file",
            help="URL 文件（每行一个 URL 或 JSON 数组）",
            exists=True, file_okay=True, dir_okay=False,
        ),
        output: Path = typer.Option(
            "./output", "-o", "--output",
            help="输出目录",
            file_okay=False, dir_okay=True,
        ),
        publisher: str = typer.Option(
            "local", "-p", "--publisher",
            help="发布器名称 (local/hugo/hexo)",
        ),
        fetcher: str = typer.Option(
            "playwright", "--fetcher",
            help="抓取器 (playwright/camoufox)",
        ),
        headless: bool = typer.Option(
            True, "--headless/--show",
            help="是否使用无头浏览器",
        ),
        download_images: bool = typer.Option(
            True, "--images/--no-images",
            help="是否下载图片",
        ),
        image_mode: str = typer.Option(
            "local", "--image-mode",
            help="图片模式 (local/base64/remote)",
        ),
        image_host: str = typer.Option(
            None, "--image-host",
            help="图床类型 (oss/github/cloudinary)",
        ),
        image_config: str = typer.Option(
            None, "--image-config",
            help="图床配置 JSON 或 key=val",
        ),
        template: str = typer.Option(
            None, "-t", "--template",
            help="输出模板文件名",
        ),
        template_dir: Path = typer.Option(
            None, "--template-dir",
            help="自定义模板目录",
            file_okay=False, dir_okay=True,
        ),
        max_concurrent: int = typer.Option(
            3, "-j", "--max-concurrent",
            help="最大并发数",
            min=1,
        ),
        verbose: bool = typer.Option(
            False, "-v", "--verbose",
            help="详细日志输出",
        ),
):
    """批量转换多篇微信公众号文章"""
    if verbose:
        logging.getLogger("ez_wechatblog").setLevel(logging.DEBUG)

    if image_mode == "remote" and not image_host:
        typer.echo("Error: --image-host is required when --image-mode=remote", err=True)
        raise typer.Exit(1)

    all_urls: list[str] = []
    if urls:
        all_urls.extend(urls)
    if url_file:
        content = url_file.read_text(encoding="utf-8")
        try:
            parsed = json.loads(content)
            if isinstance(parsed, list):
                all_urls.extend(parsed)
            elif isinstance(parsed, dict) and "urls" in parsed:
                all_urls.extend(parsed["urls"])
        except json.JSONDecodeError:
            all_urls.extend(line.strip() for line in content.splitlines() if line.strip())

    if not all_urls:
        typer.echo("Error: No URLs provided. Pass URLs as arguments or use -f/--url-file", err=True)
        raise typer.Exit(1)

    typer.echo(f"Converting {len(all_urls)} articles (max {max_concurrent} concurrent)...")

    sem = asyncio.Semaphore(max_concurrent)

    async def limited_convert(url: str) -> dict:
        async with sem:
            return await _convert_single(
                url=url, output_dir=output, publisher_name=publisher,
                fetcher_name=fetcher, headless=headless,
                download_images=download_images, image_mode=image_mode,
                image_host_type=image_host,
                image_host_config=_parse_image_config(image_config),
                template_name=template, template_dir=template_dir,
            )

    async def run_all():
        tasks = [limited_convert(url) for url in all_urls]
        return await asyncio.gather(*tasks, return_exceptions=True)

    results = asyncio.run(run_all())

    ok = []
    failed = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            failed.append({"url": all_urls[i], "error": str(result)})
        elif isinstance(result, dict) and result.get("status") == "ok":
            ok.append(result)
        else:
            failed.append(result if isinstance(result, dict) else {"url": all_urls[i], "error": str(result)})

    typer.echo(f"\nDone: {len(ok)} succeeded, {len(failed)} failed")
    for r in failed:
        typer.echo(f"  FAIL: {r.get('url', '?')} - {r.get('error', 'unknown')}")


@app.command("list-templates")
def list_templates_cmd():
    """列出所有可用的输出模板"""
    tm = create_template_manager()
    for t in tm.list_templates():
        tag = " [built-in]" if t["builtin"] else ""
        typer.echo(f"  - {t['name']:<25} {t['file']}{tag}")


@app.command()
def list_publishers():
    """列出所有可用的发布器"""
    pm = create_manager()
    for name in pm.list_publishers():
        typer.echo(f"  - {name}")


@app.command()
def list_fetchers():
    """列出所有可用的抓取器"""
    for name in FetcherFactory.list():
        typer.echo(f"  - {name}")


@app.command()
def serve(
        host: str = typer.Option(
            "0.0.0.0", "--host",
            help="绑定地址",
        ),
        port: int = typer.Option(
            5000, "--port",
            help="绑定端口",
        ),
        debug: bool = typer.Option(
            False, "--debug",
            help="调试模式",
        ),
):
    """启动 HTTP API 服务器"""
    from ez_wechatblog.server import create_app
    typer.echo(f"Starting EZ_WeChatBlog API server on {host}:{port}")
    typer.echo(f"API docs: http://{host}:{port}/")
    app = create_app()
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    app()