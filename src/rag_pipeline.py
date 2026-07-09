"""
RAG 问答管线 -- 整个系统的核心：检索 + 生成。

流程：
  用户提问 -> 向量检索 Top-K 法条 -> 拼装 Prompt -> LLM 生成回答

LLM 被约束只能基于检索到的法条作答，避免幻觉。
"""

from typing import List

from langchain_core.documents import Document
from langchain_openai import ChatOpenAI

from src.config import Config
from src.vector_store import VectorStore

# ============================================================
# 系统提示词 -- 约束 LLM 的行为
# ============================================================
_SYSTEM_PROMPT = """你是一位专业的中国法律助手。请严格根据以下提供的法律条文来回答用户的问题。

遵守以下规则：
1. 只能依据【提供的法律条文】作答，不要使用你自己的知识
2. 回答时，必须引用具体的法律名称和条款号（如：《劳动合同法》第四十六条）
3. 如果提供的条文不足以回答问题，请如实告知"根据现有法律库，我无法找到直接相关的条文"，并给出最接近的参考条文
4. 回答简洁专业，用中文"""


class RAGPipeline:
    """
    RAG 问答管线。

    用法:
        pipeline = RAGPipeline()
        answer = pipeline.ask("劳动合同到期不续签，公司需要赔偿吗？")
        print(answer)
    """

    def __init__(self):
        self._vector_store = VectorStore()
        self._llm = self._create_llm()

    # ============================================================
    # 公开方法
    # ============================================================

    def ask(self, question: str, top_k: int = None, verbose: bool = False) -> dict:
        """
        执行一次 RAG 问答。

        参数:
            question: 用户问题
            top_k:    检索多少条相关法条（默认用 Config.TOP_K）
            verbose:  是否打印检索到的法条详情

        返回:
            {
                "question": 用户问题,
                "answer":   LLM 回答,
                "sources":  [{"law_name": "xxx", "article": "第X条", "content": "..."}],
            }
        """
        if not self._vector_store.exists():
            return {
                "question": question,
                "answer": "[ERROR] 向量库为空，请先运行 python main.py init 构建法律知识库。",
                "sources": [],
            }

        # 1. 检索
        retrieved_docs = self._vector_store.search(question, top_k=top_k)

        if verbose:
            print(f"\n[检索] 找到 {len(retrieved_docs)} 条相关法条:")
            for i, doc in enumerate(retrieved_docs, 1):
                meta = doc.metadata
                print(f"   {i}. [{meta.get('law_name', '')}] "
                      f"{meta.get('article', '')}: {doc.page_content[:80]}...")

        # 2. 拼装上下文
        context = self._build_context(retrieved_docs)

        # 3. 调用 LLM
        answer = self._generate(context, question)

        # 4. 整理引用来源
        sources = self._extract_sources(retrieved_docs)

        return {
            "question": question,
            "answer": answer,
            "sources": sources,
        }

    # ============================================================
    # 内部方法
    # ============================================================

    @staticmethod
    def _create_llm() -> ChatOpenAI:
        """创建 LLM 客户端，使用独立的 LLM_API_KEY 和 LLM_BASE_URL"""
        kwargs = dict(
            model=Config.LLM_MODEL,
            openai_api_key=Config.LLM_API_KEY,
            temperature=0.3,   # 低温度，让回答更严谨
            max_tokens=2048,
        )
        if Config.LLM_BASE_URL:
            kwargs["openai_api_base"] = Config.LLM_BASE_URL
        return ChatOpenAI(**kwargs)

    def _build_context(self, docs: List[Document]) -> str:
        """把检索到的法条拼成一段上下文字符串，喂给 LLM"""
        if not docs:
            return "（未找到相关法律条文）"

        parts = []
        for i, doc in enumerate(docs, 1):
            meta = doc.metadata
            law = meta.get("law_name", "未知法律")
            article = meta.get("article", "")
            content = doc.page_content
            parts.append(f"[{i}] {law} {article}\n{content}")
        return "\n\n".join(parts)

    def _generate(self, context: str, question: str) -> str:
        """调用 LLM 生成回答"""
        from langchain_core.messages import HumanMessage, SystemMessage

        messages = [
            SystemMessage(content=_SYSTEM_PROMPT),
            HumanMessage(content=f"""【提供的法律条文】
{context}

【用户提问】
{question}

请根据以上法律条文回答问题："""),
        ]

        response = self._llm.invoke(messages)
        return response.content

    @staticmethod
    def _extract_sources(docs: List[Document]) -> List[dict]:
        """从检索到的 Document 中提取引用来源"""
        seen = set()
        sources = []
        for doc in docs:
            meta = doc.metadata
            # 用内容前 100 字符做去重，避免同名空条款的导入文档被合并
            key = (
                meta.get("law_name", ""),
                meta.get("article", ""),
                doc.page_content[:100],
            )
            if key not in seen:
                seen.add(key)
                sources.append({
                    "law_name": meta.get("law_name", ""),
                    "article": meta.get("article", ""),
                    "source_file": meta.get("source_file", ""),
                    "content": doc.page_content,
                })
        return sources
