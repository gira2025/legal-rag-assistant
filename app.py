"""
Legal RAG Assistant - Web UI
启动方式: streamlit run app.py
"""

import streamlit as st
from src.config import Config
from src.rag_pipeline import RAGPipeline


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


# ==================== 侧边栏 ====================
with st.sidebar:
    st.title("⚖️ Legal RAG")
    st.subheader("法律 RAG 智能助手")
    st.markdown("---")

    # 知识库状态
    pipeline = get_pipeline()
    doc_count = pipeline._vector_store.count()
    st.metric("📚 索引法条数", f"{doc_count:,} 条")
    st.metric("🤖 LLM", Config.LLM_MODEL)
    st.metric("🔤 Embedding", Config.EMBEDDING_MODEL)

    st.markdown("---")
    st.caption("技术栈: LangChain + ChromaDB + BGE + DeepSeek")
    st.caption(f"法律库: lawtext/laws (2400+ 部法律)")

    st.markdown("---")
    top_k = st.slider("检索法条数", 3, 10, Config.TOP_K)


# ==================== 主页面 ====================
st.title("⚖️ 法律 RAG 智能助手")
st.caption("基于检索增强生成（RAG）+ 8.5 万条法律条文 · 每个回答都有法可依")

st.markdown("---")

# 输入框
question = st.text_input(
    "💬 请输入你的法律问题",
    placeholder="例如：劳动合同到期不续签，公司需要赔偿吗？",
)

if st.button("🔍 查询", type="primary", disabled=not question):
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
                st.text_area(
                    "内容",
                    src["content"][:200] + "..." if len(src["content"]) > 200 else src["content"],
                    height=120,
                    key=f"src_{i}",
                    label_visibility="collapsed",
                )

    # ==================== AI 回答 ====================
    st.markdown("---")
    st.subheader("🤖 AI 回答")

    # 用卡片样式显示回答
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
st.caption("Legal RAG Assistant · 数据来源: 国家法律法规数据库 (flk.npc.gov.cn) · 仅供学习研究使用")
