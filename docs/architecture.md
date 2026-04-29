# EZ_WeChatBlog 架构设计

## 总体架构

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Input     │────▶│   Fetcher   │────▶│   Parser    │────▶│   Assets    │
│  (URL/List) │     │ (Playwright/│     │(BS4+html2   │     │(Img Localize│
│             │     │  Camoufox)  │     │    text)    │     │   + Rewrite)│
└─────────────┘     └─────────────┘     └──────┬──────┘     └──────┬──────┘
                                                │                    │
                                                ▼                    ▼
                                       ┌─────────────────────────────────┐
                                       │         Template Engine         │
                                       │    (Jinja2: MD/HTML/自定义)      │
                                       └─────────────────┬───────────────┘
                                                         │
                              ┌──────────────────────────┼──────────────────────────┐
                              │                          │                          │
                              ▼                          ▼                          ▼
                        ┌─────────┐               ┌─────────┐               ┌─────────┐
                        │  Local  │               │  Static │               │  CMS    │
                        │   MD    │               │  Site   │               │  API    │
                        │  File   │               │(Hugo/   │               │(Notion/ │
                        │         │               │ Hexo...)│               │WP/...)  │
                        └─────────┘               └─────────┘               └─────────┘
```

## 模块详解

### Fetcher 层

| 模块 | 技术选型 | 职责 |
|------|---------|------|
| `playwright_fetcher.py` | Playwright + Chromium | 隐形浏览器抓取，绕过反爬 |
| `camoufox_fetcher.py` | Camoufox | Firefox 隐形浏览器，更低检测率 |
| `factory.py` | 工厂模式 | 统一创建接口，支持扩展 |

所有 Fetcher 继承 `BaseFetcher`，通过 `@FetcherFactory.register("name")` 注册。

### Parser 层

`wechat_parser.py` 负责：
1. 提取 `#js_content` 正文区域
2. 调用 cleaners 清洗微信专属标签
3. `html2text` / `markdownify` 转换为 Markdown
4. 提取元数据（title/author/date）
5. 提取图片清单

**Cleaners 子模块：**
- `code_snippet.py` — `<code-snippet>` → `<pre><code>`
- `media_tag.py` — `<mpvideo>`/`<mpvoice>`/`<img>` 处理
- `generic.py` — 内联样式、data 属性、空白标签、section unwrap

### Assets 层

`manager.py` 支持三种图片处理模式：

| 模式 | 说明 |
|------|------|
| `local` | 下载到本地，相对路径 |
| `base64` | 转为 Base64 data URI |
| `remote` | 上传到图床（OSS/GitHub/Cloudinary） |

图床通过 `ImageHost` 抽象类扩展，配置通过 `build_host_config()` 从 CLI 参数或环境变量读取。

### Publisher 层

所有 Publisher 继承 `BasePublisher`，实现 `get_name()`、`get_slug()`、`publish()`。

| Publisher | 输出路径 |
|-----------|---------|
| `local` | `output/<slug>/index.md` |
| `hugo` | `output/content/posts/<slug>/index.md` |
| `hexo` | `output/source/_posts/<slug>.md` |

### Template 层

`templates/manager.py` 基于 Jinja2：
- 内置模板目录：`templates/builtin/`
- 支持自定义模板目录
- 模板变量：`body`、`metadata`、`front_matter`、`footnotes`

### Plugin Engine 层

`plugin_engine/manager.py` 基于 Pluggy：
- 注册内置 Publisher
- 统一发布接口
- 未来支持外部插件发现

## 数据流

```
URL
 │
 ▼
[Fetcher] → raw HTML
 │
 ▼
[Parser] → (markdown_body, meta, image_urls)
 │
 ├─ [Assets] → 下载图片 → rewrite_markdown_images()
 │
 ├─ [Template] → rendered content (MD/HTML)
 │
 ▼
[Publisher] → output files
```

## 扩展点

| 扩展点 | 接口 | 注册方式 |
|--------|------|---------|
| 抓取器 | `BaseFetcher` | `@FetcherFactory.register()` |
| 发布器 | `BasePublisher` | `PluginManager.register_builtin()` |
| 图床 | `ImageHost` | `HOST_REGISTRY` 字典 |
| 模板 | `.j2` 文件 | `templates/builtin/` 或自定义目录 |
| 清洗器 | 函数 | `wechat_parser.py` 中调用 |