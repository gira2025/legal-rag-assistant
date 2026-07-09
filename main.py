"""
Legal RAG Assistant 入口文件

用法：
    python main.py init              # 初始化：自动拉取法律库 + 构建向量索引
    python main.py ask "你的问题"     # 提问
    python main.py add <文件/目录>    # 导入用户自定义文档（PDF/Word/TXT）
    python main.py status            # 查看当前知识库状态
"""

import sys
from pathlib import Path

from src.config import Config
from src.law_fetcher import LawFetcher
from src.document_parser import parse_file, parse_directory
from src.vector_store import VectorStore
from src.rag_pipeline import RAGPipeline


def cmd_init() -> None:
    """
    初始化知识库：
      1. 从 GitHub 拉取法律数据（lawtext/laws）
      2. 逐条解析为 LangChain Document
      3. 向量化并存入 ChromaDB
    """
    print("=" * 60)
    print("Legal RAG Assistant -- 初始化")
    print("=" * 60)
    print()

    # 0. 检查配置
    if not Config.validate():
        print("[TIP] 复制 .env.example 为 .env，填入你的 API Key 后重试")
        return

    # 1. 确保目录存在
    Config.ensure_dirs()

    # 2. 拉取法律库
    print("[STEP] 1/2: 获取法律数据...")
    print()
    fetcher = LawFetcher()
    try:
        law_docs = fetcher.fetch()
    except Exception as e:
        print(f"[ERROR] 法律库下载失败: {e}")
        print("[TIP] 如果网络不通，请检查 VPN 代理是否开启 (127.0.0.1:7897)")
        return

    if not law_docs:
        print("[ERROR] 没有获取到任何法律条文")
        return

    print()

    # 3. 构建向量索引
    print("[STEP] 2/2: 构建向量索引...")
    store = VectorStore()
    try:
        store.build_index(law_docs)
    except Exception as e:
        print(f"[ERROR] 向量索引构建失败: {e}")
        print("[TIP] 请检查 .env 中的 API Key 和网络是否正常")
        return

    # 4. 同时解析用户自定义文档
    if Config.CUSTOM_DOCS_DIR.exists():
        custom_docs = parse_directory(Config.CUSTOM_DOCS_DIR)
        if custom_docs:
            store.add_documents(custom_docs)

    print()
    print("=" * 60)
    print("[OK] 初始化完成！现在可以提问了：")
    print()
    print('   python main.py ask "劳动合同到期不续签，公司需要赔偿吗？"')
    print("=" * 60)


def cmd_ask(question: str) -> None:
    """
    向知识库提问。
    先检索最相关的法条，再交给 LLM 生成有据可循的回答。
    """
    if not Config.validate():
        return

    pipeline = RAGPipeline()
    result = pipeline.ask(question, verbose=True)

    print()
    print("=" * 60)
    print("[ANSWER] 法律助手回答：")
    print("=" * 60)
    print()
    print(result["answer"])
    print()
    print("-" * 60)
    print("[SOURCES] 参考来源：")
    for i, src in enumerate(result["sources"], 1):
        law = src["law_name"]
        article = src["article"]
        print(f"   {i}. {law} {article}")
    print("=" * 60)


def cmd_add(path_str: str) -> None:
    """
    导入用户自定义的法律文档（PDF / Word / TXT）。
    可以是单个文件，也可以是整个目录。
    """
    target = Path(path_str)
    if not target.exists():
        print(f"[ERROR] 路径不存在: {target}")
        return

    # 收集文档
    if target.is_dir():
        docs = parse_directory(target)
    else:
        docs = parse_file(target)

    if not docs:
        print("[ERROR] 没有成功解析任何文档")
        return

    # 写入向量库
    store = VectorStore()
    if not store.exists():
        print("[INFO] 向量库尚未初始化，将新建...")
        store.build_index(docs)
    else:
        store.add_documents(docs)

    print(f"[OK] 已成功导入 {len(docs)} 个文本块到知识库")


def cmd_status() -> None:
    """查看知识库状态"""
    print("=" * 60)
    print("Legal RAG Assistant -- 知识库状态")
    print("=" * 60)
    print()
    print(Config.summary())
    print()

    fetcher = LawFetcher()
    if fetcher._has_data():
        md_count = len(list(Config.LAWS_REPO_DIR.rglob("*.md")))
        print(f"法律库: {md_count} 个法律文件")
    else:
        print("法律库: 未下载（请运行 python main.py init）")

    try:
        store = VectorStore()
        store_count = store.count()
        print(f"向量库: {store_count} 条索引记录")
    except Exception:
        print("向量库: 无法连接（请检查 API Key 配置）")

    if Config.CUSTOM_DOCS_DIR.exists():
        custom_files = list(Config.CUSTOM_DOCS_DIR.iterdir())
        print(f"自定义文档: {len(custom_files)} 个文件")
    print()


# ============================================================
# 主入口
# ============================================================
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法:")
        print("  python main.py init             初始化知识库")
        print('  python main.py ask "你的问题"    提问')
        print("  python main.py add <文件/目录>   导入自定义文档")
        print("  python main.py status           查看状态")
        print()
        print("[TIP] 首次使用请先运行: python main.py init")
        sys.exit(0)

    command = sys.argv[1]

    if command == "init":
        cmd_init()
    elif command == "ask":
        question = sys.argv[2] if len(sys.argv) > 2 else input("请输入问题: ")
        if not question.strip():
            print("[ERROR] 问题不能为空")
        else:
            cmd_ask(question)
    elif command == "add":
        if len(sys.argv) < 3:
            print("[ERROR] 请指定要导入的文件或目录路径")
            print("用法: python main.py add data/custom/file.pdf")
        else:
            cmd_add(sys.argv[2])
    elif command == "status":
        cmd_status()
    else:
        print(f"[ERROR] 未知命令: {command}")
        print("支持的命令: init, ask, add, status")
