# EZ_WeChatBlog

> **阶段**: MVP — 112 个测试全部通过  
> **目标**: 微信公众号文章 → 标准 Markdown / HTML / 多平台博客后端

## 关于

EZ_WeChatBlog 是一个开源 Python 工具链，解决微信公众号内容难以被标准博客生态复用的问题。

**核心能力：**
- 微信公众号文章 URL → 标准 Markdown / HTML
- 三种图片处理模式：本地下载 / Base64 内嵌 / 图床上传（OSS / GitHub / Cloudinary）
- 7 个内置模板：4 Markdown + 3 HTML（亮色 / 暗色 / 打印友好 / 现代卡片）
- 自定义 Jinja2 模板引擎，支持 `.j2` 和 `.html` 模板文件
- 插件化发布器：Local / Hugo / Hexo，可扩展
- 两种抓取器：Playwright / Camoufox（低检测率）
- 批量转换，支持并发控制
- **Flask HTTP API 服务器**，支持远程调用
- **浏览器插件**（Chrome/Edge），一键抓取微信文章
- GitHub Actions 自动发布（tag → 版本更新 → PyPI → Release）

---

## 安装

```bash
git clone https://github.com/dariondong/EZ_WeChatBlog.git
cd EZ_WeChatBlog
python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate  # Linux/Mac

# 安装项目（开发模式 + 抓取器）
pip install -e ".[dev,fetcher]"

# 安装 Playwright 浏览器
playwright install chromium

# 可选：安装 Camoufox（更低检测率）
pip install camoufox
camoufox fetch
```

---

## 快速开始

```bash
# 单篇文章转换
ez-wc convert "https://mp.weixin.qq.com/s/xxxxx" -o ./output

# 生成 HTML（暗色主题）
ez-wc convert "url" -t html_dark.html

# 批量转换
ez-wc batch "url1" "url2" "url3" -o ./output

# 启动 HTTP API 服务器
ez-wc serve --port 5000

# 上传到 GitHub 图床
ez-wc convert "url" --image-mode remote --image-host github \
  --image-config 'repo=user/repo,token=ghp_xxx'
```

---

## CLI 命令

| 命令 | 说明 |
|------|------|
| `ez-wc convert <url>` | 单篇文章转换 |
| `ez-wc batch [urls...]` | 批量转换 |
| `ez-wc serve` | 启动 HTTP API 服务器 |
| `ez-wc list-publishers` | 列出可用发布器 |
| `ez-wc list-fetchers` | 列出可用抓取器 |
| `ez-wc list-templates` | 列出可用模板 |

### convert / batch 公共选项

| 选项 | 默认值 | 说明 |
|------|--------|------|
| `-o, --output` | `./output` | 输出目录 |
| `-p, --publisher` | `local` | 发布器（local / hugo / hexo） |
| `--fetcher` | `playwright` | 抓取器（playwright / camoufox） |
| `--headless/--show` | headless | 是否显示浏览器窗口 |
| `--images/--no-images` | images | 是否下载图片 |
| `--image-mode` | `local` | 图片模式（local / base64 / remote） |
| `--image-host` | - | 图床类型（oss / github / cloudinary） |
| `--image-config` | - | 图床配置（JSON 或 key=val） |
| `-t, --template` | - | 输出模板文件名 |
| `--template-dir` | - | 自定义模板目录 |
| `-v, --verbose` | - | 详细日志 |

### serve 选项

| 选项 | 默认值 | 说明 |
|------|--------|------|
| `--host` | `0.0.0.0` | 绑定地址 |
| `--port` | `5000` | 绑定端口 |
| `--debug` | - | 调试模式 |

---

## HTTP API 服务器

启动服务器后，可通过 HTTP 调用转换功能：

```bash
# 启动服务器
ez-wc serve --port 5000

# 转换文章
curl -X POST http://localhost:5000/convert \
  -H "Content-Type: application/json" \
  -d '{"url": "https://mp.weixin.qq.com/s/xxxxx"}'

# 列出可用资源
curl http://localhost:5000/publishers
curl http://localhost:5000/fetchers
curl http://localhost:5000/templates
curl http://localhost:5000/health
```

### API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/` | API 信息 |
| `GET` | `/health` | 健康检查 |
| `GET` | `/publishers` | 列出发布器 |
| `GET` | `/fetchers` | 列出抓取器 |
| `GET` | `/templates` | 列出模板 |
| `POST` | `/convert` | 转换文章 |

### POST /convert 请求体

```json
{
  "url": "https://mp.weixin.qq.com/s/xxxxx",
  "publisher": "local",
  "fetcher": "playwright",
  "headless": true,
  "download_images": false,
  "image_mode": "local",
  "template": "html_dark.html",
  "output_dir": "./output"
}
```

---

## 浏览器插件

Chrome/Edge 浏览器插件，一键抓取微信公众号文章。

### 安装

1. 打开 Chrome/Edge，访问 `chrome://extensions/`
2. 开启「开发者模式」
3. 点击「加载已解压的扩展程序」
4. 选择 `browser_extension/` 目录

### 使用

1. 启动 API 服务器：`ez-wc serve`
2. 打开微信公众号文章页面
3. 点击页面上的「📝 转为 Markdown」按钮
4. 或点击浏览器工具栏图标，选择输出格式后点击「转换文章」

### 功能

- 自动检测微信公众号文章页面
- 页面内一键转换按钮
- Popup 弹窗支持选择输出格式和发布器
- 自定义服务器地址
- 转换状态实时反馈

---

## 模板引擎

内置 7 个模板，支持 `.j2` 和 `.html` 两种格式：

### Markdown 模板

| 模板 | 说明 |
|------|------|
| `markdown` | 默认，含 YAML front_matter |
| `frontmatter_full` | 完整 YAML Front Matter（含 tags） |
| `minimal` | 极简，底部来源信息 |

### HTML 模板

| 模板 | 说明 |
|------|------|
| `html` | 标准亮色页面 |
| `html_dark` | 暗色主题（Catppuccin 风格） |
| `html_modern` | 现代卡片式，标签高亮 |
| `html_print` | 衬线字体，打印优化 |

```bash
# 使用内置模板
ez-wc convert "url" -t html_dark.html

# 自定义模板目录
ez-wc convert "url" -t my_tpl.html --template-dir ./my_templates

# 查看所有模板
ez-wc list-templates
```

### 自定义模板

创建 `.j2` 或 `.html` 文件，使用 Jinja2 语法：

```html
<!DOCTYPE html>
<html>
<head><title>{{ metadata.title }}</title></head>
<body>
  <h1>{{ metadata.title }}</h1>
  <p>{{ metadata.author }} · {{ metadata.date }}</p>
  {{ body }}
</body>
</html>
```

**可用变量：** `body`、`metadata.title`、`metadata.author`、`metadata.date`、`metadata.tags`、`metadata.url`、`front_matter`、`footnotes`

详见 [使用文档](docs/usage.md)。

---

## 图片处理

| 模式 | 说明 | 适用场景 |
|------|------|---------|
| `local` | 下载到 `./images/`，相对路径 | 静态博客（Hugo / Hexo） |
| `base64` | 转为 Base64 data URI 内嵌 | 单文件归档、邮件发送 |
| `remote` | 上传到图床，替换为 CDN 链接 | 在线发布 |

### 图床配置

```bash
# 阿里云 OSS
ez-wc convert "url" --image-mode remote --image-host oss \
  --image-config '{"endpoint":"oss-cn-hangzhou.aliyuncs.com","bucket":"my-bucket","access_key":"xxx","secret_key":"xxx"}'

# GitHub
ez-wc convert "url" --image-mode remote --image-host github \
  --image-config 'repo=user/repo,token=ghp_xxx'

# Cloudinary
ez-wc convert "url" --image-mode remote --image-host cloudinary \
  --image-config 'cloud_name=mycloud,api_key=123,api_secret=abc'

# 环境变量（避免暴露密钥）
export EZ_WC_IMG_OSS_ENDPOINT=oss-cn-hangzhou.aliyuncs.com
export EZ_WC_IMG_OSS_BUCKET=my-bucket
export EZ_WC_IMG_OSS_ACCESS_KEY=LTAI5t...
export EZ_WC_IMG_OSS_SECRET_KEY=xxx...
ez-wc convert "url" --image-mode remote --image-host oss
```

---

## 项目结构

```
EZ_WeChatBlog/
├── ez_wechatblog/
│   ├── cli.py                      # Typer CLI 入口
│   ├── server.py                   # Flask HTTP API 服务器
│   ├── __main__.py                 # python -m ez_wechatblog
│   ├── utils.py                    # 工具函数
│   ├── fetcher/                    # 抓取模块
│   │   ├── base.py                 #   抽象基类
│   │   ├── factory.py              #   工厂模式注册
│   │   ├── playwright_fetcher.py   #   Playwright 实现
│   │   └── camoufox_fetcher.py     #   Camoufox 实现
│   ├── parser/                     # 解析模块
│   │   ├── wechat_parser.py        #   HTML → Markdown
│   │   └── cleaners/               #   标签清洗器
│   │       ├── code_snippet.py     #     代码块处理
│   │       ├── media_tag.py        #     视频/音频/图片
│   │       └── generic.py          #     通用清洗
│   ├── assets/                     # 资源管理
│   │   └── manager.py              #   图片三模式 + 图床上传
│   ├── publishers/                 # 发布器
│   │   ├── base.py                 #   抽象基类
│   │   ├── local.py                #   本地文件
│   │   ├── hugo.py                 #   Hugo
│   │   └── hexo.py                 #   Hexo
│   ├── templates/                  # 模板引擎
│   │   ├── manager.py              #   Jinja2 管理
│   │   └── builtin/                #   内置模板 (7 个)
│   │       ├── markdown.md.j2
│   │       ├── html.html.j2
│   │       ├── html_dark.html
│   │       ├── html_modern.html
│   │       ├── html_print.html
│   │       ├── frontmatter_full.md.j2
│   │       └── minimal.md.j2
│   └── plugin_engine/              # 插件引擎
│       └── manager.py              #   Pluggy 管理
├── browser_extension/              # Chrome/Edge 浏览器插件
│   ├── manifest.json
│   ├── popup.html
│   ├── popup.js
│   ├── content.js
│   ├── content.css
│   └── icons/
├── tests/                          # 测试 (112 个)
├── skills/
│   └── SKILL.md                    # AI Agent 技能定义
├── .github/workflows/
│   ├── ci.yml                      # CI：PR/push 自动测试
│   └── release.yml                 # Release：tag 自动发布
├── docs/
│   ├── architecture.md             # 架构设计
│   └── usage.md                    # 使用文档
├── pyproject.toml
└── README.md
```

---

## 开发

```bash
# 安装开发依赖
pip install -e ".[dev,fetcher]"

# 运行全部测试
pytest tests/ -v

# 运行单模块测试
pytest tests/test_parser.py -v

# 首次失败即停
pytest -x

# 查看帮助
ez-wc --help
ez-wc convert --help
ez-wc batch --help
ez-wc serve --help
```

### 发布新版本

```bash
# 推送 tag，GitHub Actions 自动：
# 1. 运行测试
# 2. 更新 pyproject.toml 版本号
# 3. 构建并发布到 PyPI
# 4. 创建 GitHub Release
git tag v0.2.0
git push origin v0.2.0
```

---

## 扩展

### 新增发布器

```python
# ez_wechatblog/publishers/wordpress.py
from ez_wechatblog.publishers.base import Article, BasePublisher

class WordPressPublisher(BasePublisher):
    def get_name(self) -> str:
        return "wordpress"
    def get_slug(self, article: Article) -> str:
        return article.metadata.get("title", "untitled")
    def publish(self, article: Article, config: dict) -> dict:
        # 调用 WordPress REST API
        ...
```

在 `plugin_engine/manager.py` 的 `create_manager()` 中注册即可。

### 新增图床

```python
class S3ImageHost(ImageHost):
    def get_name(self) -> str: return "s3"
    async def upload(self, image_data, filename, session): ...

HOST_REGISTRY["s3"] = S3ImageHost
```

### 新增抓取器

```python
@FetcherFactory.register("httpx")
class HttpxFetcher(BaseFetcher):
    async def fetch(self, url: str) -> str: ...
    async def close(self): ...
```

---

## 测试

-  核心链路 MVP，112 个测试 ✅

---

## 文档

- [使用文档](docs/usage.md) — 完整使用指南
- [架构设计](docs/architecture.md) — 模块详解
- [AI Agent 技能](skills/SKILL.md) — Claude Code / Cursor 集成

---

## 灵感来源

2026.04.28 跟 Kuang Zheng [https://github.com/kz2006a] 讨论 Blog 问题，想到快速实现微信公众号文章转为 Blog 文章发布问题，于是制作了这个工具链。

---

## 鸣谢

- 感谢各位开发者提供的开源库
- 感谢 VS Code 提供开发环境
- 感谢 Opencode 提供的 AI 驱动环境
- 感谢 DeepSeek 的 AI 能力驱动
- 感谢 Xiaomi Mimo 的 AI 能力驱动
- 感谢 Xiaomi MiMo Orbit 百万亿 Token 创造者激励计划

---

## 许可证

MIT © 2026 THEEZ EZ_WeChatBlog DarionDong Contributors