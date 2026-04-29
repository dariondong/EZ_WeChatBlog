import asyncio
import logging
from pathlib import Path

import typer

from ez_wechatblog.assets.manager import AssetManager
from ez_wechatblog.fetcher.factory import FetcherFactory
from ez_wechatblog.parser.wechat_parser import WeChatParser
from ez_wechatblog.plugin_engine.manager import create_manager
from ez_wechatblog.publishers.base import Article
from ez_wechatblog.utils import ensure_dir

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
            help="发布器名称 (local/hugo/hexo/...)",
        ),
        headless: bool = typer.Option(
            True, "--headless/--show",
            help="是否使用无头浏览器",
        ),
        download_images: bool = typer.Option(
            True, "--images/--no-images",
            help="是否下载图片",
        ),
        verbose: bool = typer.Option(
            False, "-v", "--verbose",
            help="详细日志输出",
        ),
):
    """将微信公众号文章转换为 Markdown 并发布"""
    if verbose:
        logging.getLogger("ez_wechatblog").setLevel(logging.DEBUG)

    asyncio.run(_do_convert(
        url=url,
        output_dir=output,
        publisher_name=publisher,
        headless=headless,
        download_images=download_images,
    ))


async def _do_convert(url: str, output_dir: Path, publisher_name: str,
                      headless: bool, download_images: bool):
    output_dir = ensure_dir(output_dir)

    logger.info("Fetching article: %s", url)
    fetcher = FetcherFactory.create("playwright", headless=headless)
    try:
        html = await fetcher.fetch(url)
    finally:
        await fetcher.close()

    logger.info("Parsing HTML...")
    parser = WeChatParser()
    markdown_body, meta, image_urls = parser.parse(html, url=url)

    assets_dir = None
    if download_images and image_urls:
        logger.info("Downloading %d images...", len(image_urls))
        am = AssetManager(output_dir, assets_subdir="images", referer=url)
        await am.download_all(image_urls)
        markdown_body = am.rewrite_markdown_images(markdown_body)
        assets_dir = am.assets_dir
    elif image_urls:
        logger.info("Skipping image download (%d images found)", len(image_urls))

    full_md = parser.build_full_markdown(markdown_body, meta)
    article = Article(markdown=full_md, metadata=meta.to_dict(),
                      assets_dir=assets_dir)

    pm = create_manager()
    result = pm.publish(article, publisher_name, config={
        "output_dir": str(output_dir),
    })

    logger.info("Done! Published to: %s", result.get("path", "?"))


@app.command()
def list_publishers():
    """列出所有可用的发布器"""
    pm = create_manager()
    for name in pm.list_publishers():
        typer.echo(f"  - {name}")


if __name__ == "__main__":
    app()