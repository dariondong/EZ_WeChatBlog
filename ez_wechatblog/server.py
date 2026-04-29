import asyncio
import logging
from pathlib import Path

from flask import Flask, request, jsonify

from ez_wechatblog.assets.manager import AssetManager, HOST_REGISTRY, build_host_config
from ez_wechatblog.fetcher.factory import FetcherFactory
from ez_wechatblog.parser.wechat_parser import WeChatParser
from ez_wechatblog.plugin_engine.manager import create_manager
from ez_wechatblog.publishers.base import Article
from ez_wechatblog.templates.manager import create_manager as create_template_manager
from ez_wechatblog.utils import ensure_dir, validate_url

logger = logging.getLogger(__name__)

import ez_wechatblog.fetcher.playwright_fetcher  # noqa: register
import ez_wechatblog.fetcher.camoufox_fetcher  # noqa: register


def create_app(config: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config.update(config or {})

    @app.route("/")
    def index():
        return jsonify({
            "name": "EZ_WeChatBlog API",
            "version": "0.1.0",
            "endpoints": {
                "POST /convert": "Convert a WeChat article to Markdown/HTML",
                "GET /publishers": "List available publishers",
                "GET /fetchers": "List available fetchers",
                "GET /templates": "List available templates",
                "GET /health": "Health check",
            },
        })

    @app.route("/health")
    def health():
        return jsonify({"status": "ok"})

    @app.route("/publishers")
    def list_publishers():
        pm = create_manager()
        return jsonify({"publishers": pm.list_publishers()})

    @app.route("/fetchers")
    def list_fetchers():
        return jsonify({"fetchers": FetcherFactory.list()})

    @app.route("/templates")
    def list_templates():
        tm = create_template_manager()
        return jsonify({"templates": tm.list_templates()})

    @app.route("/convert", methods=["POST"])
    def convert():
        data = request.get_json(silent=True) or {}
        url = data.get("url")
        if not url:
            return jsonify({"error": "Missing required field: url"}), 400

        try:
            url = validate_url(url)
        except ValueError as e:
            return jsonify({"error": str(e)}), 400

        publisher_name = data.get("publisher", "local")
        fetcher_name = data.get("fetcher", "playwright")
        headless = data.get("headless", True)
        download_images = data.get("download_images", False)
        image_mode = data.get("image_mode", "local")
        image_host_type = data.get("image_host")
        image_host_config = data.get("image_host_config", {})
        template_name = data.get("template")
        template_dir = data.get("template_dir")
        output_dir = Path(data.get("output_dir", "./output"))

        result = asyncio.run(_do_convert(
            url=url,
            output_dir=output_dir,
            publisher_name=publisher_name,
            fetcher_name=fetcher_name,
            headless=headless,
            download_images=download_images,
            image_mode=image_mode,
            image_host_type=image_host_type,
            image_host_config=image_host_config,
            template_name=template_name,
            template_dir=Path(template_dir) if template_dir else None,
        ))

        if result.get("status") == "error":
            return jsonify(result), 500
        return jsonify(result)

    return app


async def _do_convert(url: str, output_dir: Path, publisher_name: str,
                      fetcher_name: str, headless: bool,
                      download_images: bool, image_mode: str,
                      image_host_type: str | None,
                      image_host_config: dict,
                      template_name: str | None = None,
                      template_dir: Path | None = None) -> dict:
    output_dir = ensure_dir(output_dir)

    logger.info("Fetching: %s", url)
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

    assets_dir = None
    if download_images and image_urls:
        try:
            host = None
            if image_mode == "remote" and image_host_type:
                host_config = build_host_config(image_host_type, cli_args=image_host_config)
                host_cls = HOST_REGISTRY[image_host_type]
                host = host_cls(**host_config)
            am = AssetManager(output_dir, assets_subdir="images", referer=url,
                              image_mode=image_mode, image_host=host)
            await am.download_all(image_urls)
            markdown_body = am.rewrite_markdown_images(markdown_body)
            assets_dir = am.assets_dir
        except Exception as e:
            logger.warning("Image processing failed: %s", e)

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
        return {"url": url, "status": "error", "error": f"Template error: {e}"}

    article = Article(markdown=rendered, metadata=meta.to_dict(),
                      assets_dir=assets_dir)

    pm = create_manager()
    try:
        result = pm.publish(article, publisher_name, config={
            "output_dir": str(output_dir),
        })
    except Exception as e:
        return {"url": url, "status": "error", "error": f"Publish failed: {e}"}

    return {
        "url": url,
        "status": "ok",
        "title": meta.title,
        "author": meta.author,
        "date": meta.date,
        "images_count": len(image_urls),
        "slug": result.get("slug", "?"),
        "path": result.get("path", "?"),
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="EZ_WeChatBlog API Server")
    parser.add_argument("--host", default="0.0.0.0", help="Bind host")
    parser.add_argument("--port", type=int, default=5000, help="Bind port")
    parser.add_argument("--debug", action="store_true", help="Debug mode")
    args = parser.parse_args()

    app = create_app()
    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()