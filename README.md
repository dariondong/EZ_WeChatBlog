# EZ_WeChatBlog

> **Status**: 🚧 Design & Prototype Phase — 架构设计与核心模块验证中  
> **Goal**: 微信公众号文章 → 通用 Markdown / 多平台博客后端，插件化、可扩展、AI-Agent 友好

---

## 项目定位

EZ_WeChatBlog 是一个**开源 Python 工具链**，解决微信公众号内容难以被标准博客生态复用的问题：

- **输入**：微信公众号文章 URL（单篇 / 批量 / 公众号历史）
- **处理**：穿透反爬 → 解析正文 → 清洗 HTML → 提取元数据 → 下载图片
- **输出**：标准 Markdown（含 Front Matter）+ 本地化图片资源
- **扩展**：通过插件化架构一键同步到 Hugo / Hexo / Notion / WordPress 等后端

---

## 核心架构

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Input     │────▶│   Fetcher   │────▶│   Parser    │────▶│   Assets    │
│  (URL/List) │     │ (Camoufox/  │     │(BS4+html2   │     │(Img Localize│
│             │     │  Playwright)│     │    text)    │     │   + Rewrite)│
└─────────────┘     └─────────────┘     └──────┬──────┘     └──────┬──────┘
                                                │                    │
                                                ▼                    ▼
                                       ┌─────────────────────────────────┐
                                       │         Markdown + Meta         │
                                       │    (title/author/date/tags)     │
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

### 模块职责

| 模块 | 技术选型 | 职责 |
|------|---------|------|
| **Fetcher** | `Camoufox` / `Playwright` + stealth | 隐形浏览器抓取，绕过微信反爬与 JS 挑战 |
| **Parser** | `BeautifulSoup4` + `html2text` | 清洗微信专属标签（`code-snippet`、`mpvideo` 等），提取 Front Matter |
| **AssetManager** | `aiohttp` + `aiofiles` | 异步下载图片，带 `Referer` 头破解防盗链，重写 Markdown 图片路径 |
| **Publisher Hub** | `Pluggy` 插件系统 | 标准化发布接口，社区可扩展任意博客后端 |
| **CLI / API** | `Typer` + `FastAPI` | 本地命令行与 HTTP 服务两种交互方式 |

---

## 关键技术决策

### 1. 抓取层：为什么选 Camoufox？

微信公众号有严格的 bot 检测（TLS 指纹、JS 挑战、行为分析）。直接 `requests` 几乎不可行。

- **方案 A**（推荐）：`Camoufox` — 基于 Firefox 的隐形浏览器，原生绕过 bot 检测，支持异步批量 [参考实现](https://github.com/dairoot/ChatGPT-Proxy)
- **方案 B**：`Playwright` + `playwright-stealth` — 社区成熟，但检测率略低于 Camoufox
- **方案 C**（有后台权限时）：直接调用 `mp.weixin.qq.com/cgi-bin/appmsgpublish` 接口获取历史列表，再抓取公开页

### 2. 解析层：微信 HTML 的特殊处理

微信正文包裹在 `#js_content` 中，包含大量内联样式和专属标签，需要预处理：

```python
# 微信代码块 → 标准 Markdown code fence
<code-snippet data-lang="python">...</code-snippet>

# 微信视频 → 占位链接
<mpvideo data-vid="xxx">...</mpvideo>

# 图片防盗链 URL
<img data-src="https://mmbiz.qpic.cn/...?wx_fmt=png">
```

解析器需完成：
1. 预处理专属标签 → 标准 HTML
2. `html2text` 转换 → Markdown
3. 提取图片清单（`data-src` 优先于 `src`）
4. 组装 YAML Front Matter

### 3. 图片处理：三种模式

| 模式 | 说明 | 适用场景 |
|------|------|---------|
| `local` | 下载到 `./images/`，Markdown 使用相对路径 | 静态博客（Hugo/Hexo） |
| `remote` | 下载后上传至图床（OSS/GitHub/Cloudinary），替换为 CDN 链接 | 在线发布 |
| `base64` | 转为 Base64 内嵌 | 单文件归档、邮件发送 |

### 4. 插件化发布：Pluggy 架构

```python
# 标准化接口（发布器只需实现两个方法）
class PublisherSpec:
    def get_name(self) -> str: ...
    def publish(self, article: dict, config: dict) -> dict: ...

# article 结构
{
    "markdown": "# 标题\n\n正文...",
    "metadata": {"title": "...", "author": "...", "date": "..."},
    "assets_dir": Path("./output/文章标题/")
}
```

内置发布器：
- `local` — 写入本地文件系统
- `hugo` — 按 `content/posts/<slug>/index.md` 组织
- `hexo` — 按 `source/_posts/<slug>.md` 组织
- `notion` — 调用 Notion API 创建 Page
- `wordpress` — 通过 REST API 发布

---

## 项目结构（建议）

```
EZ_WeChatBlog/
├── ez_wechatblog/
│   ├── __init__.py
│   ├── cli.py                 # Typer CLI 入口
│   ├── api.py                 # FastAPI 服务（可选）
│   ├── fetcher/
│   │   ├── __init__.py
│   │   ├── camoufox_fetcher.py
│   │   └── playwright_fetcher.py
│   ├── parser/
│   │   ├── __init__.py
│   │   ├── wechat_parser.py
│   │   └── cleaners/
│   │       ├── code_snippet.py
│   │       └── media_tag.py
│   ├── assets/
│   │   ├── __init__.py
│   │   └── manager.py
│   ├── publishers/
│   │   ├── __init__.py
│   │   ├── local.py
│   │   ├── hugo.py
│   │   ├── hexo.py
│   │   ├── notion.py
│   │   └── wordpress.py
│   ├── plugin_manager.py      # Pluggy 注册与调度
│   └── utils.py
├── skills/
│   └── SKILL.md               # Claude Code / Cursor Agent 技能定义
├── tests/
│   ├── test_fetcher.py
│   ├── test_parser.py
│   └── test_publishers.py
├── docs/
│   └── architecture.md
├── pyproject.toml             # Poetry / uv / pdm
├── README.md
└── LICENSE (MIT)
```

---

## 实现路线图

### Phase 1 — 核心链路跑通（MVP）
- [ ] `Fetcher`：基于 Playwright 的单篇文章抓取
- [ ] `Parser`：微信 HTML → Markdown 基础转换
- [ ] `AssetManager`：图片下载 + 路径重写
- [ ] `CLI`：Typer 基础命令 `convert`

### Phase 2 — 稳定性与批量
- [ ] 切换至 `Camoufox` 降低检测率
- [ ] Cookie Pool 与请求频率控制
- [ ] 批量抓取（URL 列表 + 公众号历史接口）
- [ ] 增量同步（SQLite 记录已抓文章）

### Phase 3 — 插件生态
- [ ] `Pluggy` 插件系统落地
- [ ] 内置发布器：Hugo / Hexo / VitePress
- [ ] 社区插件：Notion / WordPress / Ghost
- [ ] 图床上传插件（OSS / GitHub / Cloudinary）

### Phase 4 — AI 与自动化
- [ ] `SKILL.md` 编写，支持 Claude Code / Cursor 调用
- [ ] 接入本地 LLM（Ollama）自动生成标签、摘要、分类
- [ ] GitHub Actions 模板：定时同步公众号到静态博客

---

## 本地开发

```bash
# 1. 克隆仓库
git clone https://github.com/yourname/EZ_WeChatBlog.git
cd EZ_WeChatBlog

# 2. 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3. 安装依赖（开发模式）
pip install -e ".[dev]"

# 4. 运行测试
pytest tests/ -v

# 5. 本地试运行（需先安装 Playwright）
playwright install chromium
python -m ez_wechatblog.cli convert "https://mp.weixin.qq.com/s/xxxxx" -o ./test_output
```

---

## 为什么需要这个项目？

现有工具的问题：
- 在线转换网站：不稳定、有广告、无法批量、图片易失效
- 浏览器插件：功能单一，难以对接自动化流程
- 其他开源工具：大多只解决"单篇转 Markdown"，缺乏**批量能力**和**发布闭环**

EZ_WeChatBlog 的目标是成为**微信内容生态与标准博客生态之间的桥梁**，既面向开发者（插件扩展），也面向 AI Agent（Skill 化调用）。

---

## 贡献指南

欢迎提交 Issue 和 PR！优先需要：

1. 更稳定的微信抓取方案（绕过反爬）
2. 微信专属标签的清洗规则补充
3. 新的 Publisher 插件
4. 测试用例（提供脱敏的微信 HTML 样本）

---

## 许可证

[MIT License](LICENSE) © 2026 EZ_WeChatBlog Contributors
