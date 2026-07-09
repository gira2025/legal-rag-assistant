"""
向量存储模块 -- 基于 ChromaDB 的向量数据库操作。

核心操作：
  - build_index():   从零构建向量索引（清空旧数据）
  - add_documents(): 增量添加新文档
  - search():        语义相似度检索
"""

from pathlib import Path
from typing import List, Optional

from langchain_core.documents import Document
from langchain_chroma import Chroma

from src.config import Config
from src.embedder import create_embeddings


class VectorStore:
    """
    ChromaDB 向量存储封装。

    用法:
        store = VectorStore()
        store.build_index(docs)           # 首次构建
        store.add_documents(new_docs)     # 增量添加
        results = store.search("问题")    # 检索
    """

    def __init__(self):
        self._embeddings = None  # 延迟初始化，只在真正需要时才创建
        self._collection_name = Config.CHROMA_COLLECTION_NAME
        self._persist_dir = str(Config.CHROMA_DB_DIR)

    @property
    def embeddings(self):
        """延迟创建 Embedding 客户端，避免无 API Key 时初始化崩溃"""
        if self._embeddings is None:
            self._embeddings = create_embeddings()
        return self._embeddings

    # ============================================================
    # 公开方法
    # ============================================================

    def build_index(self, documents: List[Document]) -> None:
        """
        从零构建向量索引。
        WARNING: 会删除同名的旧 collection，重新创建。
        适合首次入库或完全重建时使用。
        """
        if not documents:
            print("[WARN] 文档列表为空，跳过索引构建")
            return

        total = len(documents)
        print(f"[BUILD] 正在构建向量索引，共 {total} 条文档...")
        print(f"       模型: {Config.EMBEDDING_MODEL}")
        print(f"       存储: {self._persist_dir}")

        # 分批处理，每批 2000 条，显示进度
        batch_size = 2000
        for i in range(0, total, batch_size):
            batch = documents[i:i + batch_size]
            end = min(i + batch_size, total)
            pct = end * 100 // total
            print(f"       进度: {end}/{total} ({pct}%)", flush=True)

            if i == 0:
                # 第一批：创建新 collection（覆盖旧的）
                Chroma.from_documents(
                    documents=batch,
                    embedding=self.embeddings,
                    collection_name=self._collection_name,
                    persist_directory=self._persist_dir,
                )
            else:
                # 后续批次：追加到已有 collection
                store = self._load()
                store.add_documents(batch)

        print(f"[OK] 向量索引构建完成，已持久化到 {self._persist_dir}")

    def add_documents(self, documents: List[Document]) -> None:
        """
        增量添加文档到已有 collection。
        不会删除已有数据，新文档会追加进去。
        """
        if not documents:
            print("[WARN] 文档列表为空，跳过")
            return

        store = self._load()
        store.add_documents(documents)
        print(f"[OK] 已添加 {len(documents)} 条文档到向量库")

    def search(self, query: str, top_k: int = None) -> List[Document]:
        """
        语义相似度检索。
        返回与 query 最相似的 top_k 条 Document，按相关度降序排列。
        """
        top_k = top_k or Config.TOP_K
        store = self._load()
        results = store.similarity_search(query, k=top_k)
        return results

    def search_with_scores(self, query: str, top_k: int = None) -> List[tuple]:
        """
        带相关度分数的检索。
        返回 [(Document, score), ...]，score 越小越相关（L2 距离）。
        """
        top_k = top_k or Config.TOP_K
        store = self._load()
        return store.similarity_search_with_relevance_scores(query, k=top_k)

    def count(self) -> int:
        """返回向量库中的文档总数"""
        try:
            store = self._load()
            return store._collection.count()
        except Exception:
            return 0

    def exists(self) -> bool:
        """检查是否已有向量索引"""
        return self.count() > 0

    def delete_imported(self) -> int:
        """删除所有用户导入的文档（source_type=imported），返回删除数量"""
        try:
            store = self._load()
            coll = store._collection
            # 先查出要删多少
            result = coll.get(where={"source_type": "imported"})
            count = len(result["ids"]) if result["ids"] else 0
            if count > 0:
                coll.delete(where={"source_type": "imported"})
            return count
        except Exception:
            return 0

    def count_imported(self) -> int:
        """返回导入文档数量"""
        try:
            store = self._load()
            result = store._collection.get(where={"source_type": "imported"})
            return len(result["ids"]) if result["ids"] else 0
        except Exception:
            return 0

    # ============================================================
    # 内部方法
    # ============================================================

    def _load(self) -> Chroma:
        """加载已有的 ChromaDB collection"""
        return Chroma(
            collection_name=self._collection_name,
            embedding_function=self.embeddings,
            persist_directory=self._persist_dir,
        )
