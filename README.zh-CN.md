# Rekall

```
        ██████╗ ███████╗██╗  ██╗ █████╗ ██╗     ██╗
        ██╔══██╗██╔════╝██║ ██╔╝██╔══██╗██║     ██║
        ██████╔╝█████╗  █████╔╝ ███████║██║     ██║
        ██╔══██╗██╔══╝  ██╔═██╗ ██╔══██║██║     ██║
        ██║  ██║███████╗██║  ██╗██║  ██║███████╗███████╗
        ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚══════╝
```

> *"Get your ass to Mars. Quaid... crush those bugs"*

**停止丢失知识。开始记忆。**

Rekall 是一个为开发者设计的知识管理系统，具有**认知记忆**和**语义搜索**功能。它不仅存储你的知识——还能帮助你像大脑一样*记住*和*找到*它。

[![Version](https://img.shields.io/badge/version-0.3.0-blue.svg)](CHANGELOG.md)
[![Python](https://img.shields.io/badge/python-3.9+-green.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-brightgreen.svg)](LICENSE)

**翻译：** [English](README.md) | [Français](README.fr.md) | [Español](README.es.md) | [Deutsch](README.de.md)

---

## 为什么选择 Rekall？

```
你（3个月前）               你（今天）
     │                           │
     ▼                           ▼
┌─────────────┐           ┌─────────────┐
│ 修复 Bug X  │           │ 同样的 Bug  │
│ 研究2小时   │           │ 从头开始... │
│ 找到了！    │           │             │
└─────────────┘           └─────────────┘
     │                           │
     ▼                           ▼
   (丢失)                    (又花2小时)
```

**你已经解决过这个问题了。** 但那个解决方案在哪里？

使用 Rekall：

```
┌─────────────────────────────────────────┐
│ $ rekall search "循环导入"               │
│                                         │
│ [1] bug: 修复: models 中的循环导入       │
│     得分: ████████░░ 85%                │
│     情况: user.py 和 profile.py 之间    │
│           存在导入循环                   │
│     解决方案: 将共享类型提取到           │
│               types/common.py           │
└─────────────────────────────────────────┘
```

**5秒内找到。无需云服务。无需订阅。**

---

## 功能特性

| 功能 | 描述 |
|------|------|
| **语义搜索** | 按含义搜索，而不仅仅是关键词 |
| **结构化上下文** | 捕获情况、解决方案和关键词 |
| **知识图谱** | 链接相关条目 |
| **认知记忆** | 区分事件和模式 |
| **间隔重复** | 按最佳间隔复习 |
| **MCP 服务器** | AI 助手集成（Claude 等） |
| **100% 本地** | 你的数据永远不会离开你的机器 |
| **TUI 界面** | 使用 Textual 的美观终端 UI |

---

## 安装

```bash
# 使用 uv（推荐）
uv tool install git+https://github.com/guthubrx/rekall.git

# 使用 pipx
pipx install git+https://github.com/guthubrx/rekall.git

# 验证安装
rekall version
```

---

## 快速开始

### 1. 捕获带上下文的知识

```bash
# 简单条目
rekall add bug "修复: models 中的循环导入" -t python,import

# 带结构化上下文（推荐）
rekall add bug "修复: 循环导入" --context-interactive
# > 情况: user.py 和 profile.py 之间存在导入循环
# > 解决方案: 将共享类型提取到 types/common.py
# > 关键词: 循环, 导入, 依赖, 重构
```

### 2. 语义搜索

```bash
# 文本搜索
rekall search "循环导入"

# 语义搜索（找到相关概念）
rekall search "模块依赖循环" --semantic

# 按关键词搜索
rekall search --keywords "import,cycle"
```

### 3. 在 TUI 中探索

```bash
rekall          # 启动交互界面
```

---

## 结构化上下文

每个条目都可以有丰富的上下文，使其更容易找到：

```bash
rekall add bug "Safari 上的 CORS 错误" --context-json '{
  "situation": "Safari 阻止跨域请求，即使有 CORS 头",
  "solution": "添加 credentials: include 和正确的 Access-Control 头",
  "trigger_keywords": ["cors", "safari", "cross-origin", "credentials"]
}'
```

或使用交互模式：

```bash
rekall add bug "Safari 上的 CORS 错误" --context-interactive
```

---

## 语义搜索

Rekall 使用本地嵌入按含义搜索：

```bash
# 启用语义搜索
rekall embeddings --status      # 检查状态
rekall embeddings --migrate     # 为现有条目生成嵌入

# 按含义搜索
rekall search "认证超时" --semantic
```

搜索组合：
- **全文搜索** (50%) - 精确关键词匹配
- **语义相似度** (30%) - 基于含义的匹配
- **关键词匹配** (20%) - 结构化上下文关键词

---

## 知识图谱

连接相关条目以构建知识网络：

```bash
rekall link 01HXYZ 01HABC                      # 创建链接
rekall link 01HXYZ 01HABC --type supersedes    # 带关系类型
rekall related 01HXYZ                          # 显示连接
rekall graph 01HXYZ                            # ASCII 可视化
```

**链接类型：** `related`（相关）、`supersedes`（取代）、`derived_from`（衍生自）、`contradicts`（矛盾）

---

## 认知记忆

像你的大脑一样，Rekall 区分两种类型的记忆：

### 情景记忆（发生了什么）
```bash
rekall add bug "生产 API 认证超时 15/12" --memory-type episodic
```

### 语义记忆（你学到了什么）
```bash
rekall add pattern "外部 API 总是添加重试退避" --memory-type semantic
```

### 泛化
```bash
rekall generalize 01HA 01HB 01HC --title "超时重试模式"
```

---

## 间隔重复

使用 SM-2 算法按最佳间隔复习知识：

```bash
rekall review              # 开始复习会话
rekall review --limit 10   # 复习 10 个条目
rekall stale               # 找到被遗忘的知识（30+ 天）
```

---

## MCP 服务器（AI 集成）

Rekall 包含用于 AI 助手集成的 MCP 服务器：

```bash
rekall mcp    # 启动 MCP 服务器
```

**可用工具：**
- `rekall_search` - 搜索知识库
- `rekall_add` - 添加条目
- `rekall_show` - 获取条目详情
- `rekall_link` - 连接条目
- `rekall_suggest` - 基于嵌入获取建议

---

## IDE 集成

```bash
rekall install claude     # Claude Code
rekall install cursor     # Cursor AI
rekall install copilot    # GitHub Copilot
rekall install windsurf   # Windsurf
rekall install cline      # Cline
rekall install zed        # Zed
```

---

## 迁移和维护

```bash
rekall version             # 显示版本 + 架构信息
rekall changelog           # 显示版本历史
rekall migrate             # 升级数据库架构（带备份）
rekall migrate --dry-run   # 预览更改
```

---

## 条目类型

| 类型 | 用途 | 示例 |
|------|------|------|
| `bug` | 修复的 Bug | "修复: Safari 上的 CORS 错误" |
| `pattern` | 最佳实践 | "模式: 数据库仓库模式" |
| `decision` | 架构决策 | "决策: 使用 Redis 作为会话" |
| `pitfall` | 要避免的错误 | "陷阱: 不要使用 SELECT *" |
| `config` | 配置技巧 | "配置: VS Code 调试 Python" |
| `reference` | 外部文档 | "参考: React Hooks 文档" |
| `snippet` | 代码块 | "代码片段: 防抖函数" |
| `til` | 快速学习 | "今日学习: Git rebase -i 用于 squash" |

---

## 数据和隐私

**100% 本地。零云端。**

| 平台 | 位置 |
|------|------|
| Linux | `~/.local/share/rekall/` |
| macOS | `~/Library/Application Support/rekall/` |
| Windows | `%APPDATA%\rekall\` |

---

## 要求

- Python 3.9+
- 无外部服务
- 无需互联网（除了可选的嵌入模型下载）
- 无需账户

---

## 许可证

MIT

---

**停止丢失知识。开始记忆。**

```bash
uv tool install git+https://github.com/guthubrx/rekall.git
rekall
```
