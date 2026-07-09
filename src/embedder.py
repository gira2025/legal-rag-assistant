"""
Embedding 模块 -- 创建和管理文本向量化客户端。

支持两种后端，通过 .env 中的 EMBEDDING_PROVIDER 切换：
  - "local" : 本地 HuggingFace 模型（免费、离线、中文优化）
  - "openai" : OpenAI 兼容 API（Gemini / OpenAI / 通义千问等）
"""

# 抑制 HuggingFace Hub 的无认证警告
import os as _os
_os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

from langchain_openai import OpenAIEmbeddings

from src.config import Config


def create_embeddings():
    """
    创建一个 Embedding 客户端实例。
    自动根据 Config.EMBEDDING_PROVIDER 选择后端。

    用法：
        embeddings = create_embeddings()
        # 传给 ChromaDB：Chroma.from_documents(docs, embeddings)
    """
    provider = Config.EMBEDDING_PROVIDER

    if provider == "local":
        return _create_local_embeddings()
    elif provider == "openai":
        return _create_openai_embeddings()
    else:
        raise ValueError(
            f"不支持的 EMBEDDING_PROVIDER: {provider}，"
            f"可选: local, openai"
        )


# ============================================================
# 本地 HuggingFace 模型（推荐默认）
# ============================================================

def _create_local_embeddings():
    """
    使用本地 HuggingFace 模型做向量化。
    - 免费免 API Key
    - 中文优化（BGE 系列）
    - 首次运行自动下载模型到本地缓存
    - 后续完全离线运行
    """
    try:
        from langchain_huggingface import HuggingFaceEmbeddings
    except ImportError:
        raise ImportError(
            "本地模型需要 langchain-huggingface 和 sentence-transformers，"
            "请运行: pip install langchain-huggingface sentence-transformers"
        )

    model_name = Config.LOCAL_EMBEDDING_MODEL
    print(f"[EMBED] 加载本地模型: {model_name}")

    return HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs={"device": "cpu"},        # 用 CPU 跑（如需 GPU 改为 "cuda"）
        encode_kwargs={"normalize_embeddings": True},  # 归一化，提高检索精度
    )


# ============================================================
# OpenAI 兼容 API（Gemini / OpenAI / DeepSeek 等）
# ============================================================

def _create_openai_embeddings():
    """
    使用 OpenAI 兼容的 Embedding API。
    支持所有兼容 /v1/embeddings 端点的服务。
    通过 .env 配置 EMBEDDING_API_KEY, EMBEDDING_BASE_URL, EMBEDDING_MODEL 来切换。
    """
    kwargs = dict(
        model=Config.EMBEDDING_MODEL,
        openai_api_key=Config.EMBEDDING_API_KEY,
    )

    if Config.EMBEDDING_BASE_URL:
        kwargs["openai_api_base"] = Config.EMBEDDING_BASE_URL

    # 代理
    if Config.HTTP_PROXY or Config.HTTPS_PROXY:
        import httpx
        proxy_url = Config.HTTPS_PROXY or Config.HTTP_PROXY
        kwargs["http_client"] = httpx.Client(proxy=proxy_url)

    print(f"[EMBED] 使用 API: {Config.EMBEDDING_BASE_URL} / {Config.EMBEDDING_MODEL}")
    return OpenAIEmbeddings(**kwargs)
