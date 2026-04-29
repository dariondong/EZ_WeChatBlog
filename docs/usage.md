# EZ_WeChatBlog 使用文档

> 微信公众号文章 → 标准 Markdown / HTML / 多平台博客后端

---

## 目录

- [安装](#安装)
- [快速开始](#快速开始)
- [命令详解](#命令详解)
  - [convert — 单篇转换](#convert--单篇转换)
  - [batch — 批量转换](#batch--批量转换)
  - [list-publishers](#list-publishers)
  - [list-fetchers](#list-fetchers)
  - [list-templates](#list-templates)
- [图片处理](#图片处理)
  - [本地模式](#本地模式)
  - [Base64 模式](#base64-模式)
  - [图床模式](#图床模式)
- [模板引擎](#模板引擎)
  - [内置模板](#内置模板)
  - [自定义模板](#自定义模板)
  - [模板变量](#模板变量)
- [发布器](#发布器)
- [抓取器](#抓取器)
- [环境变量](#环境变量)
- [常见问题](#常见问题)

---

## 安装

### 基础安装

```bash
git clone https://github.com/dariondong/EZ_WeChatBlog.git
cd EZ_WeChatBlog
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/Mac
pip install -e ".[dev]"
```

### 安装抓取器

```bash
# Playwright（推荐）
pip install -e ".[fetcher]"
playwright install chromium

# Camoufox（更低检测率，可选）
pip install camoufox
camoufox fetch
```

### 验证安装

```bash
ez-wc --help
ez-wc list-fetchers
ez-wc list-publishers
ez-wc list-templates
```

---

## 快速开始

### 最简用法

```bash
ez-wc convert "https://mp.weixin.qq.com/s/xxxxx"
```

输出目录默认为 `./output/文章标题/index.md`。

### 指定输出目录

```bash
ez-wc convert "https://mp.weixin.qq.com/s/xxxxx" -o ./my_posts
```

### 生成 HTML

```bash
ez-wc convert "https://mp.weixin.qq.com/s/xxxxx" -t html.html.j2
```

### 发布到 Hugo

```bash
ez-wc convert "https://mp.weixin.qq.com/s/xxxxx" -p hugo -o ./my_hugo_site
```

### 批量转换

```bash
ez-wc batch "url1" "url2" "url3" -o ./output -j 3
```

---

## 命令详解

### convert — 单篇转换

```bash
ez-wc convert <URL> [选项]
```

**参数：**

| 参数 | 必填 | 说明 |
|------|------|------|
| `URL` | 是 | 微信公众号文章链接 |

**选项：**

| 选项 | 默认值 | 说明 |
|------|--------|------|
| `-o, --output` | `./output` | 输出目录 |
| `-p, --publisher` | `local` | 发布器（local / hugo / hexo） |
| `--fetcher` | `playwright` | 抓取器（playwright / camoufox） |
| `--headless` | 是 | 无头模式运行浏览器 |
| `--show` | - | 显示浏览器窗口（调试用） |
| `--images` | 是 | 下载图片 |
| `--no-images` | - | 跳过图片下载 |
| `--image-mode` | `local` | 图片处理模式（local / base64 / remote） |
| `--image-host` | - | 图床类型（oss / github / cloudinary） |
| `--image-config` | - | 图床配置（JSON 或 key=val） |
| `-t, --template` | - | 输出模板文件名 |
| `--template-dir` | - | 自定义模板目录 |
| `-v, --verbose` | - | 详细日志 |

**示例：**

```bash
# 基础转换
ez-wc convert "https://mp.weixin.qq.com/s/xxxxx"

# 指定输出目录和发布器
ez-wc convert "https://mp.weixin.qq.com/s/xxxxx" -o ./posts -p hugo

# 使用 Camoufox 抓取
ez-wc convert "https://mp.weixin.qq.com/s/xxxxx" --fetcher camoufox

# 显示浏览器（调试）
ez-wc convert "https://mp.weixin.qq.com/s/xxxxx" --show

# 跳过图片下载
ez-wc convert "https://mp.weixin.qq.com/s/xxxxx" --no-images

# 使用 HTML 模板
ez-wc convert "https://mp.weixin.qq.com/s/xxxxx" -t html_dark.html

# 详细日志
ez-wc convert "https://mp.weixin.qq.com/s/xxxxx" -v
```

---

### batch — 批量转换

```bash
ez-wc batch [URLs...] [选项]
```

**输入方式：**

```bash
# 方式 1：命令行直接传 URL
ez-wc batch "url1" "url2" "url3" -o ./output

# 方式 2：文本文件（每行一个 URL）
ez-wc batch -f urls.txt -o ./output

# 方式 3：JSON 文件
ez-wc batch -f urls.json -o ./output
```

**JSON 文件格式：**

```json
["url1", "url2", "url3"]
```

或：

```json
{"urls": ["url1", "url2", "url3"]}
```

**专有选项：**

| 选项 | 默认值 | 说明 |
|------|--------|------|
| `-f, --url-file` | - | URL 文件路径 |
| `-j, --max-concurrent` | 3 | 最大并发数 |

**示例：**

```bash
# 批量转换，5 并发
ez-wc batch -f urls.txt -o ./output -j 5

# 批量转换到 Hugo
ez-wc batch -f urls.txt -o ./my_hugo -p hugo

# 批量转 HTML
ez-wc batch "url1" "url2" -t html_modern.html -o ./output
```

---

### list-publishers

列出所有可用的发布器。

```bash
ez-wc list-publishers
# 输出：
#   - local
#   - hugo
#   - hexo
```

### list-fetchers

列出所有可用的抓取器。

```bash
ez-wc list-fetchers
# 输出：
#   - playwright
#   - camoufox
```

### list-templates

列出所有可用的输出模板。

```bash
ez-wc list-templates
# 输出：
#   - markdown            markdown.md.j2 [built-in]
#   - html                html.html.j2 [built-in]
#   - frontmatter_full    frontmatter_full.md.j2 [built-in]
#   - minimal             minimal.md.j2 [built-in]
#   - html_dark           html_dark.html [built-in]
#   - html_modern         html_modern.html [built-in]
#   - html_print          html_print.html [built-in]
```

---

## 图片处理

### 本地模式

默认模式。图片下载到 `./output/文章标题/images/`，Markdown 使用相对路径引用。

```bash
ez-wc convert "url" --image-mode local -o ./output
```

输出结构：
```
output/
└── 文章标题/
    ├── index.md
    └── images/
        ├── abc.png
        └── def.jpg
```

### Base64 模式

图片转为 Base64 编码内嵌到 Markdown 中。适合单文件归档或邮件发送。

```bash
ez-wc convert "url" --image-mode base64
```

输出的 Markdown 中图片格式：
```markdown
![图片](data:image/png;base64,iVBORw0KGgo...)
```

### 图床模式

图片上传到云端图床，替换为 CDN 链接。

```bash
ez-wc convert "url" --image-mode remote --image-host <类型> --image-config '<配置>'
```

#### 阿里云 OSS

```bash
ez-wc convert "url" --image-mode remote --image-host oss \
  --image-config '{
    "endpoint": "oss-cn-hangzhou.aliyuncs.com",
    "bucket": "my-bucket",
    "access_key": "LTAI5t...",
    "secret_key": "xxx..."
  }'
```

**必填参数：**
- `endpoint` — OSS 端点（如 `oss-cn-hangzhou.aliyuncs.com`）
- `bucket` — 存储桶名称
- `access_key` — AccessKey ID
- `secret_key` — AccessKey Secret

**可选参数：**
- `path_prefix` — 上传路径前缀（默认 `images`）

#### GitHub

```bash
ez-wc convert "url" --image-mode remote --image-host github \
  --image-config 'repo=user/repo,token=ghp_xxx'
```

**必填参数：**
- `repo` — GitHub 仓库（`user/repo` 格式）
- `token` — GitHub Personal Access Token

**可选参数：**
- `path_prefix` — 上传路径前缀（默认 `images`）

#### Cloudinary

```bash
# 签名模式（推荐）
ez-wc convert "url" --image-mode remote --image-host cloudinary \
  --image-config 'cloud_name=mycloud,api_key=123,api_secret=abc'

# 未签名上传
ez-wc convert "url" --image-mode remote --image-host cloudinary \
  --image-config 'cloud_name=mycloud,upload_preset=mypreset'
```

**必填参数：**
- `cloud_name` — Cloudinary 云名称

**可选参数：**
- `api_key` — API Key（签名模式）
- `api_secret` — API Secret（签名模式）
- `upload_preset` — 上传预设（未签名模式，默认 `unsigned`）

---

## 模板引擎

### 内置模板

| 模板名 | 格式 | 说明 |
|--------|------|------|
| `markdown` | Markdown | 默认模板，含 YAML front_matter |
| `frontmatter_full` | Markdown | 完整 YAML front_matter（含 tags） |
| `minimal` | Markdown | 极简模板，底部来源信息 |
| `html` | HTML | 标准亮色 HTML 页面 |
| `html_dark` | HTML | 暗色主题（Catppuccin 风格） |
| `html_modern` | HTML | 现代卡片式，标签高亮 |
| `html_print` | HTML | 衬线字体，打印优化 |

**使用：**

```bash
# Markdown 模板（默认）
ez-wc convert "url"

# HTML 暗色主题
ez-wc convert "url" -t html_dark.html

# 打印友好 HTML
ez-wc convert "url" -t html_print.html
```

### 自定义模板

创建 `.j2` 或 `.html` 模板文件，使用 Jinja2 语法。

**步骤：**

1. 创建模板目录：
```bash
mkdir my_templates
```

2. 创建模板文件 `my_templates/custom.html`：
```html
<!DOCTYPE html>
<html>
<head>
  <title>{{ metadata.title }}</title>
  <style>
    body { max-width: 800px; margin: 0 auto; padding: 2em; }
    h1 { color: #333; }
  </style>
</head>
<body>
  <h1>{{ metadata.title }}</h1>
  <p>作者：{{ metadata.author }} · {{ metadata.date }}</p>
  <hr>
  {{ body }}
</body>
</html>
```

3. 使用：
```bash
ez-wc convert "url" -t custom.html --template-dir ./my_templates
```

### 模板变量

模板中可用的 Jinja2 变量：

| 变量 | 类型 | 说明 |
|------|------|------|
| `body` | str | 文章正文（Markdown 或 HTML） |
| `metadata` | dict | 元数据字典 |
| `metadata.title` | str | 文章标题 |
| `metadata.author` | str | 作者名 |
| `metadata.date` | str | 发布日期（YYYY-MM-DD） |
| `metadata.tags` | list[str] | 标签列表 |
| `metadata.url` | str | 原文链接 |
| `front_matter` | str | YAML Front Matter 字符串 |
| `footnotes` | str | 脚注内容 |

**Jinja2 过滤器：**

```python
# 字符串加引号
{{ metadata.title | wrap('"') }}  → "文章标题"

# 截断
{{ body | truncate(100) }}  → 前100个字符...

# 列表拼接
{{ metadata.tags | join(', ') }}  → python, blog

# 列表加引号拼接
{{ metadata.tags | map('wrap', '"') | join(', ') }}
```

**模板示例 — Hugo Front Matter：**

```markdown
---
title: "{{ metadata.title }}"
date: {{ metadata.date }}
author: "{{ metadata.author }}"
tags: [{{ metadata.tags | map('wrap', '"') | join(', ') }}]
draft: false
---

{{ body }}
```

**模板示例 — 带目录的 HTML：**

```html
<!DOCTYPE html>
<html>
<head><title>{{ metadata.title }}</title></head>
<body>
  <nav>
    <a href="{{ metadata.url }}">原文</a>
  </nav>
  <article>
    <h1>{{ metadata.title }}</h1>
    <time>{{ metadata.date }}</time>
    {{ body }}
  </article>
</body>
</html>
```

---

## 发布器

| 发布器 | 输出路径 | 说明 |
|--------|---------|------|
| `local` | `output/<slug>/index.md` | 本地文件系统 |
| `hugo` | `output/content/posts/<slug>/index.md` | Hugo 博客 |
| `hexo` | `output/source/_posts/<slug>.md` | Hexo 博客 |

```bash
# 本地（默认）
ez-wc convert "url" -p local

# Hugo
ez-wc convert "url" -p hugo -o ./my_hugo_site

# Hexo
ez-wc convert "url" -p hexo -o ./my_hexo_site
```

---

## 抓取器

| 抓取器 | 说明 | 依赖 |
|--------|------|------|
| `playwright` | Chromium 无头浏览器（默认） | `pip install playwright` |
| `camoufox` | Firefox 隐形浏览器，更低检测率 | `pip install camoufox` |

```bash
# 使用 Playwright（默认）
ez-wc convert "url"

# 使用 Camoufox
ez-wc convert "url" --fetcher camoufox

# 显示浏览器窗口（调试）
ez-wc convert "url" --show
```

---

## 环境变量

图床配置可通过环境变量传入，避免在命令行中暴露密钥。

**命名规则：** `EZ_WC_IMG_<HOST>_<KEY>`

| 环境变量 | 说明 |
|----------|------|
| `EZ_WC_IMG_OSS_ENDPOINT` | OSS 端点 |
| `EZ_WC_IMG_OSS_BUCKET` | OSS 存储桶 |
| `EZ_WC_IMG_OSS_ACCESS_KEY` | OSS AccessKey |
| `EZ_WC_IMG_OSS_SECRET_KEY` | OSS SecretKey |
| `EZ_WC_IMG_OSS_PATH_PREFIX` | OSS 路径前缀 |
| `EZ_WC_IMG_GITHUB_REPO` | GitHub 仓库 |
| `EZ_WC_IMG_GITHUB_TOKEN` | GitHub Token |
| `EZ_WC_IMG_GITHUB_PATH_PREFIX` | GitHub 路径前缀 |
| `EZ_WC_IMG_CLOUDINARY_CLOUD_NAME` | Cloudinary 云名称 |
| `EZ_WC_IMG_CLOUDINARY_API_KEY` | Cloudinary API Key |
| `EZ_WC_IMG_CLOUDINARY_API_SECRET` | Cloudinary API Secret |
| `EZ_WC_IMG_CLOUDINARY_UPLOAD_PRESET` | Cloudinary 上传预设 |

**示例：**

```bash
# 设置环境变量
export EZ_WC_IMG_OSS_ENDPOINT=oss-cn-hangzhou.aliyuncs.com
export EZ_WC_IMG_OSS_BUCKET=my-bucket
export EZ_WC_IMG_OSS_ACCESS_KEY=LTAI5t...
export EZ_WC_IMG_OSS_SECRET_KEY=xxx...

# 使用（无需 --image-config）
ez-wc convert "url" --image-mode remote --image-host oss
```

---

## 常见问题

### Q: 抓取失败，提示 Playwright 未安装？

```bash
pip install playwright
playwright install chromium
```

### Q: 微信文章抓取不到内容？

1. 确认 URL 格式正确：`https://mp.weixin.qq.com/s/xxxxx`
2. 尝试使用 Camoufox：`--fetcher camoufox`
3. 尝试显示浏览器调试：`--show`

### Q: 图片下载失败？

1. 检查网络连接
2. 微信图片有防盗链，工具已自动处理 `Referer` 头
3. 使用 `--no-images` 跳过图片下载

### Q: 如何自定义输出格式？

创建自定义 Jinja2 模板，参考 [自定义模板](#自定义模板) 章节。

### Q: 批量转换时如何控制速度？

使用 `-j` 参数控制并发数：

```bash
# 降低并发，减少被封风险
ez-wc batch -f urls.txt -j 1

# 提高并发，加快速度
ez-wc batch -f urls.txt -j 5
```

### Q: 如何在 CI/CD 中使用？

参考 `.github/workflows/release.yml`，推送 tag 即可自动发布：

```bash
git tag v0.2.0
git push origin v0.2.0
```