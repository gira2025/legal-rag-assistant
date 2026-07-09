# Changelog

## v0.1.0 (2025-07-09) — 首次可用版本

### 核心功能

- **法律库自动拉取**：从 `lawtext/laws` 自动下载 2,477 个法律文件，解析为 85,332 条法条
- **RAG 问答**：基于 LangChain + ChromaDB + DeepSeek，检索法条后由 LLM 生成有据可循的回答
- **双 Embedding 后端**：本地 BGE 模型（免费）和 OpenAI 兼容 API 一键切换
- **CLI 入口**：`python main.py init|ask|add|status`
- **Web UI**：Streamlit 界面，含问题输入、检索结果展示、AI 回答、来源引用
- **自定义文档导入**：支持通过 Web UI 上传 PDF / Word / TXT

### v0.1.0 修复记录

| 修复 | 说明 |
|------|------|
| 模块导入兼容 | 适配 LangChain 新版 API（`langchain_core.documents`、`langchain_text_splitters`、`langchain_chroma`） |
| Windows 终端兼容 | 移除所有 emoji，避免 GBK 编码报错 |
| 法律库数据源切换 | 从 `Chinese-Laws-folk`（Git LFS 预算超限）切换到 `lawtext/laws`（纯文本） |
| Markdown 法律解析 | 适配新数据源的 YAML front matter + 条款格式 |
| 分批索引 + 进度条 | 85k 法条分 43 批索引，实时显示百分比 |
| 导入成功提示消失 | 使用 `session_state` 持久化提示消息，rerun 后仍可见 |
| 模型重复加载 | Streamlit 添加 `@st.cache_resource`，BGE 模型只加载一次 |
| 导入文档元数据 | 上传文件使用原始文件名，不再显示临时文件路径 |
| 空 API Key 崩溃 | `status` 命令在无 Key 时不崩溃，优雅显示 |
| 低配 Windows 兼容 | HF Hub 警告抑制、目录不存在时的容错处理 |
| 配置分离 | LLM / Embedding 使用独立 API Key 和 Base URL |

### 已知问题（计划 v0.2.0 修复）

| 问题 | 说明 |
|------|------|
| 检索结果出现"未知来源" | 部分自定义导入文档的元数据在某些路径下未正确传递，显示为"未知来源" |
| 相似内容重复检索 | 导入内容相同、仅空行不同的文档会产生多个冗余检索结果 |

### v0.2.0 计划

- [ ] 知识库浏览功能：在 Web UI 中查看已导入的文件列表和已有法条目录
- [ ] 修复"未知来源"显示问题
- [ ] 修复相似内容去重，检索结果不再重复展示相同条款
- [ ] 支持从 Web UI 删除已导入的文档
- [ ] 检索结果高亮显示匹配关键词
- [ ] 一键导出问答记录
