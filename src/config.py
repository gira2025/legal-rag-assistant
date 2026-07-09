"""
配置中心 -- 所有路径、模型参数、API 设置统一在这里管理。
读取 .env 文件中的环境变量，没有的用默认值。

LLM 和 Embedding 可以使用不同的 API 提供商。
例如：LLM 用 DeepSeek，Embedding 用 Google Gemini（有免费额度）。
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# 加载项目根目录下的 .env 文件
load_dotenv()


class Config:
    """全局配置，所有属性都是类属性，直接用 Config.XXX 访问"""

    # ==================== 路径 ====================
    PROJECT_ROOT = Path(__file__).resolve().parent.parent  # 项目根目录
    DATA_DIR = PROJECT_ROOT / "data"
    LAWS_REPO_DIR = DATA_DIR / "laws"        # 法律库克隆到这里
    CUSTOM_DOCS_DIR = DATA_DIR / "custom"    # 用户自定义文档
    CHROMA_DB_DIR = DATA_DIR / "chroma_db"   # 向量数据库持久化目录

    # ==================== LLM 配置 ====================
    # 优先用 LLM_API_KEY，没有则回退到 OPENAI_API_KEY
    LLM_API_KEY = os.getenv("LLM_API_KEY", "") or os.getenv("OPENAI_API_KEY", "")
    LLM_BASE_URL = os.getenv("LLM_BASE_URL", "") or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-chat")

    # ==================== Embedding 配置 ====================
    # 后端选择: "local" = 本地 HuggingFace 模型（免费用）, "openai" = OpenAI 兼容 API
    EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "local")

    # 本地模型配置（EMBEDDING_PROVIDER=local 时生效）
    # bge-small-zh-v1.5: 24MB, 512维, 快速, 中文效果好
    # bge-large-zh-v1.5: 326MB, 1024维, 最佳中文检索质量
    LOCAL_EMBEDDING_MODEL = os.getenv("LOCAL_EMBEDDING_MODEL", "BAAI/bge-small-zh-v1.5")

    # API 模型配置（EMBEDDING_PROVIDER=openai 时生效）
    # 优先用 EMBEDDING_API_KEY，没有则回退到 OPENAI_API_KEY
    EMBEDDING_API_KEY = os.getenv("EMBEDDING_API_KEY", "") or os.getenv("OPENAI_API_KEY", "")
    EMBEDDING_BASE_URL = os.getenv("EMBEDDING_BASE_URL", "") or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

    # ==================== 文本切分 ====================
    CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "500"))        # 每个文本块最大字符数
    CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "50"))   # 相邻块的重叠字符数

    # ==================== 检索参数 ====================
    TOP_K = int(os.getenv("TOP_K", "5"))  # 每次检索返回最相关的 K 条法条

    # ==================== ChromaDB ====================
    CHROMA_COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "legal_knowledge")

    # ==================== 法律库 GitHub ====================
    LAWS_REPO_URL = "https://github.com/lawtext/laws.git"

    # ==================== 代理（VPN）====================
    HTTP_PROXY = os.getenv("HTTP_PROXY", "")
    HTTPS_PROXY = os.getenv("HTTPS_PROXY", "")

    @classmethod
    def ensure_dirs(cls) -> None:
        """确保所有数据目录都存在（首次运行自动创建）"""
        for d in [cls.DATA_DIR, cls.CUSTOM_DOCS_DIR, cls.CHROMA_DB_DIR]:
            d.mkdir(parents=True, exist_ok=True)

    @classmethod
    def validate(cls) -> bool:
        """检查必要配置是否齐全"""
        if not cls.LLM_API_KEY:
            print("[ERROR] 缺少 LLM_API_KEY，请在 .env 文件中配置")
            return False
        if cls.EMBEDDING_PROVIDER == "openai" and not cls.EMBEDDING_API_KEY:
            print("[ERROR] EMBEDDING_PROVIDER=openai 需要 EMBEDDING_API_KEY")
            return False
        return True

    @classmethod
    def summary(cls) -> str:
        """打印当前配置，方便调试"""
        llm_key = cls.LLM_API_KEY
        llm_key_masked = ("..." + llm_key[-6:]) if len(llm_key) > 6 else "***"

        return (
            f"LLM 模型: {cls.LLM_MODEL}\n"
            f"LLM 地址: {cls.LLM_BASE_URL}\n"
            f"LLM Key : {llm_key_masked}\n"
            f"Embedding: {cls.EMBEDDING_PROVIDER}"
            + (f" ({cls.LOCAL_EMBEDDING_MODEL})" if cls.EMBEDDING_PROVIDER == "local" else f" ({cls.EMBEDDING_MODEL})") + "\n"
            f"向量库路径: {cls.CHROMA_DB_DIR}\n"
            f"切块大小/重叠: {cls.CHUNK_SIZE}/{cls.CHUNK_OVERLAP}\n"
            f"检索 Top-K: {cls.TOP_K}"
        )
