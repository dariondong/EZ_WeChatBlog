# EZ_WeChatBlog — AI Agent Skill

> 适用于 Claude Code / Cursor / Copilot 等 AI 编程助手

## 项目概述

EZ_WeChatBlog 是一个 Python 工具链，将微信公众号文章转换为标准 Markdown / HTML，
支持多平台博客后端发布（Hugo / Hexo / Notion 等）。

## 架构

```
Input (URL) → Fetcher (Playwright/Camoufox) → Parser (BS4+html2text)
  → AssetManager (图片下载/三模式) → Publisher (local/hugo/hexo)
                                    → Template (Jinja2 自定义输出)
```

## 常用命令

```bash
# 安装
pip install -e ".[dev,fetcher]"

# 单篇转换
ez-wc convert "https://mp.weixin.qq.com/s/xxxxx" -o ./output

# 批量转换
ez-wc batch "url1" "url2" -o ./output -j 3

# 使用模板
ez-wc convert "url" -t html.html.j2 -o ./output

# 自定义模板目录
ez-wc convert "url" -t my_template.md.j2 --template-dir ./my_templates

# 列出可用资源
ez-wc list-publishers
ez-wc list-fetchers
ez-wc list-templates
```

## 关键文件

| 文件 | 职责 |
|------|------|
| `ez_wechatblog/cli.py` | Typer CLI 入口，4 个命令 |
| `ez_wechatblog/fetcher/` | 抓取层（Playwright / Camoufox） |
| `ez_wechatblog/parser/wechat_parser.py` | HTML → Markdown 解析 |
| `ez_wechatblog/parser/cleaners/` | 标签清洗（code/media/generic） |
| `ez_wechatblog/assets/manager.py` | 图片下载（local/base64/remote） |
| `ez_wechatblog/publishers/` | 发布器（local/hugo/hexo） |
| `ez_wechatblog/templates/` | Jinja2 模板引擎 + 内置模板 |
| `ez_wechatblog/plugin_engine/manager.py` | Pluggy 插件管理 |

## 开发约定

- Python 3.10+，异步优先（asyncio + aiohttp）
- 测试框架：pytest + pytest-asyncio
- 格式：2 空格缩进，无尾部逗号
- 类型注解：Python 3.10+ 风格（`list[str]`、`dict[str, str]`、`X | None`）

## 测试

```bash
pytest tests/ -v          # 全量测试
pytest tests/test_parser.py -v   # 单模块测试
pytest -x                  # 首次失败即停
```

## 扩展指南

### 新增发布器
1. 在 `ez_wechatblog/publishers/` 新建文件
2. 继承 `BasePublisher`，实现 `get_name()`、`get_slug()`、`publish()`
3. 在 `plugin_engine/manager.py` 的 `create_manager()` 中注册

### 新增抓取器
1. 在 `ez_wechatblog/fetcher/` 新建文件
2. 继承 `BaseFetcher`，实现 `fetch()`、`close()`
3. 用 `@FetcherFactory.register("name")` 装饰器注册

### 新增模板
1. 在 `ez_wechatblog/templates/builtin/` 新建 `.j2` 文件
2. 模板变量：`body`、`metadata`、`front_matter`、`footnotes`
3. 运行 `ez-wc list-templates` 验证

### 新增图床
1. 在 `ez_wechatblog/assets/manager.py` 继承 `ImageHost`
2. 实现 `get_name()` 和 `upload()`
3. 在 `HOST_REGISTRY` 中注册