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


# ==================== 初始化 ====================
@st.cache_resource
def get_pipeline():
    return RAGPipeline()


def reload_count():
    """重新读取向量库文档数"""
    store = VectorStore()
    return store.count()


# ==================== 侧边栏 ====================
with st.sidebar:
    st.title("⚖️ Legal RAG")
    st.subheader("法律 RAG 智能助手")
    st.markdown("---")

    # 知识库状态
    if "doc_count" not in st.session_state:
        st.session_state.doc_count = reload_count()

    st.metric("📚 索引法条数", f"{st.session_state.doc_count:,} 条")
    st.metric("🤖 LLM", Config.LLM_MODEL)
    st.metric("🔤 Embedding", Config.EMBEDDING_MODEL)

    st.markdown("---")
    st.caption("技术栈: LangChain + ChromaDB + BGE + DeepSeek")
    st.caption(f"法律库: lawtext/laws (2400+ 部法律)")

    st.markdown("---")
    top_k = st.slider("检索法条数", 3, 10, Config.TOP_K)

    # ========== 导入文档 ==========
    st.markdown("---")
    st.subheader("📄 导入文档")

    uploaded_file = st.file_uploader(
        "上传 PDF / Word / TXT",
        type=["pdf", "docx", "doc", "txt", "md"],
        help="支持 PDF、Word、TXT 格式，导入后会自动加入知识库",
    )

    if uploaded_file is not None:
        with st.spinner(f"正在处理 {uploaded_file.name} ..."):
            # 保存到临时文件
            suffix = Path(uploaded_file.name).suffix
            with tempfile.NamedTemporaryFile(
                delete=False, suffix=suffix
            ) as tmp:
                tmp.write(uploaded_file.getbuffer())
                tmp_path = Path(tmp.name)

            try:
                # 解析文档
                docs = parse_file(tmp_path)
                if docs:
                    # 写入向量库
                    store = VectorStore()
                    store.add_documents(docs)
                    st.session_state.doc_count = reload_count()
                    st.success(
                        f"✅ 已导入 {uploaded_file.name}"
                        f"（{len(docs)} 个文本块）"
                    )
                else:
                    st.error(f"❌ 未能从 {uploaded_file.name} 中提取内容")
            except Exception as e:
                st.error(f"❌ 导入失败: {e}")
            finally:
                tmp_path.unlink(missing_ok=True)


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
    pipeline = get_pipeline()
    with st.spinner("正在检索相关法条..."):
        result = pipeline.ask(question, top_k=top_k, verbose=False)

    # ==================== 检索结果 ====================
    st.markdown("---")
    st.subheader("📚 检索到的相关法条")

    cols = st.columns(min(len(result["sources"]), 3))
    for i, src in enumerate(result["sources"]):
        col = cols[i % 3]
        with col:
            with st.container(border=True):
                st.markdown(f"**{src['law_name']}**")
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
    for i, src in enumerate(result["sources"], 1):
        st.markdown(f"**{i}. {src['law_name']}** {src['article']}")


# ==================== 底部 ====================
st.markdown("---")
st.caption(
    "Legal RAG Assistant ·"
    " 数据来源: 国家法律法规数据库 (flk.npc.gov.cn)"
    " · 仅供学习研究使用"
)
