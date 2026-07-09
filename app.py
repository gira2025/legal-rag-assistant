"""
Legal RAG Assistant - Web UI
启动方式: streamlit run app.py
"""

import tempfile
from pathlib import Path

import streamlit as st
from src.config import Config
from src.rag_pipeline import RAGPipeline
from src.document_parser import parse_file
from src.vector_store import VectorStore


# ==================== 页面配置 ====================
st.set_page_config(
    page_title="Legal RAG Assistant",
    page_icon="⚖️",
    layout="wide",
)


# ==================== 缓存初始化（避免每次交互都重新加载模型）====================
@st.cache_resource
def get_pipeline():
    """缓存 RAG 管线和向量存储，模型只加载一次"""
    return RAGPipeline()


@st.cache_resource
def get_store():
    """缓存向量库连接"""
    return VectorStore()


def cached_count():
    """从缓存 store 读取文档数，避免重复创建连接"""
    return get_store().count()


def cached_search(query, top_k):
    """缓存检索结果，相同 query+top_k 不重复检索"""
    pipeline = get_pipeline()
    return pipeline.ask(query, top_k=top_k, verbose=False)


# ==================== 初始化 session state ====================
if "doc_count" not in st.session_state:
    st.session_state.doc_count = cached_count()

if "import_key" not in st.session_state:
    st.session_state.import_key = 0

if "import_msg" not in st.session_state:
    st.session_state.import_msg = None  # (type, text) e.g. ("success", "...")


# ==================== 侧边栏 ====================
with st.sidebar:
    st.title("⚖️ Legal RAG")
    st.subheader("法律 RAG 智能助手")
    st.markdown("---")

    # 知识库状态（计数缓存在 session_state，避免每次刷新读硬盘）
    if "import_count" not in st.session_state:
        st.session_state.import_count = get_store().count_imported()
    import_count = st.session_state.import_count
    builtin_count = st.session_state.doc_count - import_count
    st.metric("📚 索引法条数", f"{st.session_state.doc_count:,} 条")
    st.caption(f"  内置法律 {builtin_count:,} 条 | 导入文档 {import_count:,} 条")
    st.metric("🤖 LLM", Config.LLM_MODEL)
    st.metric("🔤 Embedding", Config.EMBEDDING_MODEL)

    st.markdown("---")
    st.caption("技术栈: LangChain + ChromaDB + BGE + DeepSeek")
    st.caption(f"法律库: lawtext/laws (2400+ 部法律)")

    st.markdown("---")
    top_k = st.slider("检索法条数", 3, 10, Config.TOP_K, key="top_k_slider")

    source_filter = st.radio(
        "数据来源筛选",
        ["全部", "仅内置法律", "仅导入文档"],
        horizontal=True,
    )
    source_type_map = {"全部": None, "仅内置法律": "builtin", "仅导入文档": "imported"}
    source_type = source_type_map[source_filter]

    # ========== 导入文档 ==========
    st.markdown("---")
    st.subheader("📄 导入文档")

    uploaded_file = st.file_uploader(
        "上传 PDF / Word / TXT",
        type=["pdf", "docx", "doc", "txt", "md"],
        help="支持 PDF、Word、TXT 格式，导入后会自动加入知识库",
        key=f"uploader_{st.session_state.import_key}",
    )

    if uploaded_file is not None:
        original_name = uploaded_file.name
        with st.spinner(f"正在处理 {original_name} ..."):
            suffix = Path(original_name).suffix
            with tempfile.NamedTemporaryFile(
                delete=False, suffix=suffix
            ) as tmp:
                tmp.write(uploaded_file.getbuffer())
                tmp_path = Path(tmp.name)

            try:
                docs = parse_file(tmp_path)
                if docs:
                    # 修正元数据：标注来源类型，用原始文件名
                    for doc in docs:
                        doc.metadata["source_file"] = original_name
                        doc.metadata["law_name"] = original_name
                        doc.metadata["article"] = ""
                        doc.metadata["source_type"] = "imported"

                    store = get_store()
                    store.add_documents(docs)
                    st.session_state.doc_count = cached_count()
                    st.session_state.import_count = get_store().count_imported()
                    get_pipeline.clear()

                    # 保存成功消息到 session_state，增加 key 重置上传组件
                    st.session_state.import_msg = (
                        "success",
                        f"已导入 {original_name}（{len(docs)} 个文本块）",
                    )
                    st.session_state.import_key += 1
                    st.rerun()
                else:
                    st.session_state.import_msg = (
                        "error",
                        f"未能从 {original_name} 中提取内容",
                    )
                    st.session_state.import_key += 1
                    st.rerun()
            except Exception as e:
                st.session_state.import_msg = (
                    "error",
                    f"导入失败: {e}",
                )
                st.session_state.import_key += 1
                st.rerun()
            finally:
                tmp_path.unlink(missing_ok=True)

    # 显示上次导入的结果消息（rerun 后依然可见）
    if st.session_state.import_msg is not None:
        msg_type, msg_text = st.session_state.import_msg
        if msg_type == "success":
            st.success(f"✅ {msg_text}")
        else:
            st.error(f"❌ {msg_text}")
        st.session_state.import_msg = None

    # 删除已导入文档
    if import_count > 0:
        st.markdown("---")
        with st.expander("🗑️ 管理已导入文档"):
            st.caption(f"当前有 {import_count} 条导入文档的索引")
            if st.button("删除所有导入文档", type="secondary"):
                deleted = get_store().delete_imported()
                st.session_state.doc_count = cached_count()
                st.session_state.import_count = 0
                st.session_state.import_key += 1
                get_pipeline.clear()
                st.session_state.import_msg = (
                    "success",
                    f"已删除 {deleted} 条导入文档",
                )
                st.rerun()


# ==================== 主页面 ====================
st.title("⚖️ 法律 RAG 智能助手")
st.caption(
    "基于检索增强生成（RAG）+"
    f" {st.session_state.doc_count:,} 条法律条文"
    " · 每个回答都有法可依"
)

st.markdown("---")

# 输入框
question = st.text_input(
    "💬 请输入你的法律问题",
    placeholder="例如：劳动合同到期不续签，公司需要赔偿吗？",
)

if st.button("🔍 查询", type="primary", disabled=not question):
    with st.spinner("正在检索相关法条..."):
        result = get_pipeline().ask(question, top_k=top_k, source_type=source_type)

    sources = result["sources"]
    actual_count = len(sources)

    # ==================== 检索结果 ====================
    st.markdown("---")
    if actual_count < top_k:
        st.subheader(f"📚 检索到的相关法条（共 {actual_count} 条，少于请求的 {top_k} 条）")
    else:
        st.subheader(f"📚 检索到的相关法条（{actual_count} 条）")

    cols = st.columns(min(actual_count, 3))
    for i, src in enumerate(sources):
        col = cols[i % 3]
        with col:
            with st.container(border=True):
                label = src["law_name"] or src.get("source_file", "未知来源")
                st.markdown(f"**{label}**")
                if src["article"]:
                    st.markdown(f"*{src['article']}*")
                text = src["content"]
                st.text_area(
                    "内容",
                    text[:200] + "..." if len(text) > 200 else text,
                    height=120,
                    key=f"src_{i}",
                    label_visibility="collapsed",
                )

    # ==================== AI 回答 ====================
    st.markdown("---")
    st.subheader("🤖 AI 回答")

    st.markdown(
        f"""<div style="
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 12px;
            padding: 24px;
            color: white;
            font-size: 16px;
            line-height: 1.8;
        ">{result['answer'].replace(chr(10), '<br>')}</div>""",
        unsafe_allow_html=True,
    )

    # ==================== 来源引用 ====================
    st.markdown("---")
    st.subheader("📖 参考来源")
    for i, src in enumerate(sources, 1):
        label = src["law_name"] or src.get("source_file", "未知来源")
        article = src["article"]
        if article:
            st.markdown(f"**{i}. {label}** {article}")
        else:
            st.markdown(f"**{i}. {label}**")


# ==================== 底部 ====================
st.markdown("---")
st.caption(
    "Legal RAG Assistant ·"
    " 数据来源: 国家法律法规数据库 (flk.npc.gov.cn)"
    " · 仅供学习研究使用"
)
