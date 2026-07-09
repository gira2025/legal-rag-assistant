# ⚖️ Legal RAG Assistant — 法律 RAG 智能助手

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

基于 **RAG（检索增强生成）** 架构的法律智能问答系统。将 2400+ 部中国法律条文向量化存储，结合大语言模型实现精准的法律条文检索与有据可循的智能问答。

> 🎯 **核心特点：每个回答都有法可依，杜绝 AI 幻觉。** 回答必须引用具体法律名称和条款号，用户可追溯原文验证。

---

## ✨ 功能特性

- 📚 **内置法律库**：自动从 GitHub 获取 `lawtext/laws`，涵盖 2400+ 部中国法律、行政法规、司法解释
- 🔍 **语义检索**：基于 BGE 中文嵌入模型的高精度法条检索，85,000+ 条条款
- 🤖 **智能问答**：结合检索结果与 DeepSeek LLM，生成有据可循的法律解答
- 📄 **多格式文档导入**：支持 PDF、Word、TXT 等自定义文档导入
- 🌐 **Web 界面**：Streamlit 可视化界面，适合演示和展示
- 🆓 **免费 Embedding**：本地 BGE 模型，无需 API Key，完全离线
- 🔌 **灵活切换**：一行配置即可切换 OpenAI/Gemini 等云端 Embedding API

---

## 🏗️ 技术架构

```
用户提问
    │
    ▼
┌─────────────────────────────────────┐
│  1. Embedding 编码                  │
│     BAAI/bge-small-zh-v1.5 (本地)   │
└──────────────┬──────────────────────┘
               ▼
┌─────────────────────────────────────┐
│  2. ChromaDB 向量检索               │
│     从 85,000+ 法条中召回 Top-K     │
└──────────────┬──────────────────────┘
               ▼
┌─────────────────────────────────────┐
│  3. LLM 生成回答（带来源引用）       │
│     DeepSeek Chat                   │
└──────────────┬──────────────────────┘
               ▼
┌─────────────────────────────────────┐
│  4. 返回答案 + 法条出处              │
└─────────────────────────────────────┘
```

**技术栈：**

| 层 | 技术 |
|----|------|
| LLM | DeepSeek Chat（兼容 OpenAI API） |
| RAG 框架 | LangChain |
| 向量数据库 | ChromaDB（本地持久化） |
| Embedding | BAAI/bge-small-zh-v1.5（本地，512 维） |
| 文档解析 | PyPDF / python-docx |
| Web UI | Streamlit |

---

## 🚀 快速启动

### 1. 环境要求

- Python 3.10+
- Git

### 2. 克隆项目

```bash
git clone https://github.com/GIRA2025/legal-rag-assistant.git
cd legal-rag-assistant
```

### 3. 创建虚拟环境

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

### 4. 安装依赖

```bash
pip install -r requirements.txt
```

### 5. 配置 API Key

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env，至少填入 LLM_API_KEY（DeepSeek 或其他）
# 详细配置说明见 .env.example 中的注释
```

### 6. 初始化知识库

```bash
# 自动下载法律库 + 构建向量索引（首次约 15-20 分钟）
python main.py init
```

### 7. 开始使用

**命令行：**

```bash
# 提问
python main.py ask "劳动合同到期不续签，公司需要赔偿吗？"

# 导入自定义文档
python main.py add data/custom/公司规章.pdf

# 查看状态
python main.py status
```

**Web 界面（推荐演示用）：**

```bash
streamlit run app.py
# 浏览器打开 http://localhost:8501
```

---

## 📁 项目结构

```
legal-rag-assistant/
├── src/
│   ├── config.py            # 配置中心（路径、API、模型参数）
│   ├── law_fetcher.py       # 法律库拉取 + Markdown 解析
│   ├── document_parser.py   # 用户文档解析（PDF/Word/TXT）
│   ├── embedder.py          # Embedding 客户端（本地/API 双模式）
│   ├── vector_store.py      # ChromaDB 向量存储
│   └── rag_pipeline.py      # RAG 核心管线（检索→生成）
├── data/
│   ├── laws/                # 法律库（Git 克隆，不入版本控制）
│   ├── chroma_db/           # 向量数据库（不入版本控制）
│   └── custom/              # 用户自定义文档
├── main.py                  # CLI 入口
├── app.py                   # Web UI（Streamlit）
├── requirements.txt         # Python 依赖
├── .env.example             # 环境变量模板
└── README.md
```

---

## 🔧 配置说明

`.env` 核心配置项：

| 变量 | 说明 | 示例 |
|------|------|------|
| `LLM_API_KEY` | LLM 的 API Key | `sk-xxx` |
| `LLM_BASE_URL` | LLM API 地址 | `https://api.deepseek.com/v1` |
| `LLM_MODEL` | LLM 模型名 | `deepseek-chat` |
| `EMBEDDING_PROVIDER` | Embedding 后端 | `local` 或 `openai` |
| `LOCAL_EMBEDDING_MODEL` | 本地模型名 | `BAAI/bge-small-zh-v1.5` |
| `TOP_K` | 检索返回条数 | `5` |

**切换 Embedding 后端为 API（一行配置）：**

```bash
EMBEDDING_PROVIDER=openai
EMBEDDING_API_KEY=sk-xxx
EMBEDDING_BASE_URL=https://api.openai.com/v1
EMBEDDING_MODEL=text-embedding-3-small
```

---

## 📊 数据说明

法律数据来自 [lawtext/laws](https://github.com/lawtext/laws)，原始文件来自[国家法律法规数据库](https://flk.npc.gov.cn)。数据处理流程：

1. Git clone 拉取 Markdown 文件（含 YAML 元数据）
2. 正则解析每条 `- **第X条**` 格式的条款
3. 每条条款生成一个 LangChain Document（含法律名、条款号、分类）
4. BGE 模型向量化后存入 ChromaDB

最终索引：**2,477 个法律文件 → 85,332 条条款**

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request。

---

## 📄 开源协议

MIT License · 法律数据来自国家法律法规数据库，根据《著作权法》第五条属于公有领域。

---

⭐ 如果这个项目对你有帮助，请给一个 Star！
