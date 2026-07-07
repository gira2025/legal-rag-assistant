# Legal RAG Assistant (法律 RAG 智能助手)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)

基于 **RAG（检索增强生成）** 架构的法律智能问答助手。通过将法律文档向量化存储，结合大语言模型（LLM）实现精准的法律条文检索与智能问答。

## ✨ 功能特性

- 📄 **多格式文档解析**：支持 PDF、Word、TXT 等常见法律文档格式
- 🔍 **语义检索**：基于向量相似度的高精度法律条文检索
- 🤖 **智能问答**：结合检索结果与 LLM，生成有据可循的法律解答
- 🇨🇳 **中文优化**：集成 jieba 分词，优化中文法律文本处理
- 🔒 **本地化部署**：数据与模型均可本地运行，保障数据安全

## 🏗️ 技术架构

```
┌─────────────────────────────────────────────────┐
│                    用户提问                       │
└─────────────────┬───────────────────────────────┘
                  ▼
┌─────────────────────────────────────────────────┐
│              Embedding 模型编码                   │
└─────────────────┬───────────────────────────────┘
                  ▼
┌─────────────────────────────────────────────────┐
│           ChromaDB 向量数据库检索                 │
│         （相似法律条文 Top-K 召回）                │
└─────────────────┬───────────────────────────────┘
                  ▼
┌─────────────────────────────────────────────────┐
│             LLM 生成回答（带来源引用）             │
└─────────────────┬───────────────────────────────┘
                  ▼
┌─────────────────────────────────────────────────┐
│              返回最终答案 + 引用来源               │
└─────────────────────────────────────────────────┘
```

**技术栈：**
- **LLM**：OpenAI API / 兼容接口（支持通义千问、DeepSeek 等国产模型）
- **RAG 框架**：LangChain
- **向量数据库**：ChromaDB
- **嵌入模型**：text-embedding-3-small
- **文档解析**：PyPDF / python-docx / Unstructured

## 🚀 快速启动

### 1. 环境要求

- Python 3.10+
- pip 包管理器

### 2. 克隆项目

```bash
git clone https://github.com/GIRA2025/legal-rag-assistant.git
cd legal-rag-assistant
```

### 3. 创建虚拟环境

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python -m venv .venv
source .venv/bin/activate
```

### 4. 安装依赖

```bash
pip install -r requirements.txt
```

### 5. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 填入你的 API Key
# OPENAI_API_KEY=sk-your-api-key-here
```

### 6. 运行项目

```bash
python main.py
```

## 📁 项目结构

```
legal-rag-assistant/
├── src/                    # 源代码
│   └── __init__.py
├── data/                   # 数据目录（本地）
│   ├── raw/                # 原始文档
│   ├── processed/          # 处理后的数据
│   └── chroma_db/          # 向量数据库持久化
├── docs/                   # 文档
├── tests/                  # 单元测试
├── main.py                 # 入口文件
├── requirements.txt        # 项目依赖
├── .env.example            # 环境变量模板
├── .gitignore              # Git 忽略规则
├── LICENSE                 # MIT 开源协议
└── README.md               # 项目说明
```

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## 📄 开源协议

本项目基于 MIT License 开源，详见 [LICENSE](LICENSE) 文件。

---

⭐ 如果这个项目对你有帮助，请给一个 Star！
