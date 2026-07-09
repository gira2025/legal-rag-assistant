# Changelog

## v0.1.1 (2025-07-09) — 功能增强与性能优化

### 新增功能

- **内置/导入文档分离**：ChromaDB 中新增 `source_type` 字段，标记每条索引来源（`builtin` / `imported`），为后续筛选和管理提供基础
- **数据来源筛选搜索**：Web UI 侧边栏新增 radio 按钮，可切换搜索范围——全部 / 仅内置法律 / 仅导入文档，检索时只命中指定来源
- **一键删除导入文档**：侧边栏「管理已导入文档」面板，支持一键清空所有用户导入的文档索引
- **侧边栏知识库统计**：实时显示索引法条总数，并拆分为「内置法律」与「导入文档」两部分

### 修复与优化

| 修复 | 说明 |
|------|------|
| 导入文档显示"未知来源" | 早期测试阶段导入的文档元数据不完整，重建 ChromaDB 后问题消失。根本原因是初版 `document_parser` 未写入 `source_file` 字段，后续版本已补齐 |
| 导入文档计数性能 | 将 `count_imported()` 结果缓存到 `session_state`，避免每次页面刷新都触发 ChromaDB 磁盘读取 |

### 工程改进

- 清理无用目录（`data/raw`、`data/processed`、`docs/`）
- 移除多余的 `.gitkeep` 文件
- 更新 README 项目结构说明
- 添加 PDF / DOCX 演示用测试文件

---

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

---

## v0.2.0 计划

### 待修复

| 问题 | 说明 |
|------|------|
| 相似内容重复检索 | 导入内容相同、仅空行不同的文档会产生多个冗余检索结果 |

### 计划功能

- [ ] **知识库浏览增强**：在 Web UI 中查看已导入文件的详细列表（文件名、条款数、导入时间），支持单个文件删除
- [ ] **相似内容去重**：检索结果按内容相似度聚合，避免重复展示相同条款
- [ ] **检索关键词高亮**：检索结果和 AI 回答中高亮显示匹配的关键词
- [ ] **一键导出问答记录**：支持导出当前问答结果为 Markdown / PDF
- [ ] **多轮对话**：支持追问和上下文记忆，实现连续法律咨询体验
- [ ] **文档管理面板**：独立的文档管理页面，查看/搜索/删除已导入文档
- [ ] **更多文档格式支持**：支持 CSV、HTML、Markdown 等格式导入
- [ ] **检索结果评分展示**：显示每条检索结果的相似度分数，增强可解释性
- [ ] **Docker 一键部署**：提供 Dockerfile 和 docker-compose，降低部署门槛
