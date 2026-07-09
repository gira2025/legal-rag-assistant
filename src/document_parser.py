"""
文档解析模块 -- 把用户拖入的 PDF / Word / TXT 文件转成可索引的文本块。

因为用户文档不像法律库那样每行一条，所以需要：
  1. 提取原始文本
  2. 用 RecursiveCharacterTextSplitter 切成适合 Embedding 的小块
"""

from pathlib import Path
from typing import List

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.config import Config


def parse_file(file_path: Path) -> List[Document]:
    """
    解析单个文件，自动识别类型（PDF / DOCX / TXT），
    切块后返回 LangChain Document 列表。
    """
    suffix = file_path.suffix.lower()
    if suffix == ".pdf":
        text = _parse_pdf(file_path)
    elif suffix in (".docx", ".doc"):
        text = _parse_docx(file_path)
    elif suffix in (".txt", ".md", ".text"):
        text = _parse_txt(file_path)
    else:
        print(f"[WARN] 不支持的文件类型: {suffix}，跳过 {file_path.name}")
        return []

    if not text or not text.strip():
        print(f"[WARN] 文件内容为空: {file_path.name}")
        return []

    # 切块
    splitter = _create_splitter()
    chunks = splitter.create_documents(
        texts=[text],
        metadatas=[{"source_file": file_path.name, "file_path": str(file_path)}],
    )
    print(f"   {file_path.name}: 提取 {len(text)} 字符 -> {len(chunks)} 个文本块")
    return chunks


def parse_directory(dir_path: Path) -> List[Document]:
    """
    批量解析整个目录，支持 PDF / DOCX / TXT。
    返回所有文件的 Document 列表汇总。
    """
    if not dir_path.exists():
        print(f"[WARN] 目录不存在: {dir_path}")
        return []

    supported = {".pdf", ".docx", ".doc", ".txt", ".md", ".text"}
    files = [f for f in dir_path.iterdir()
             if f.is_file() and f.suffix.lower() in supported]

    if not files:
        print(f"[WARN] 在 {dir_path} 中没有找到支持的文档")
        return []

    print(f"[INFO] 在 {dir_path} 发现 {len(files)} 个文档")
    all_docs: List[Document] = []
    for f in files:
        all_docs.extend(parse_file(f))
    return all_docs


# ============================================================
# 内部实现
# ============================================================

def _create_splitter() -> RecursiveCharacterTextSplitter:
    """
    创建中文友好的文本切分器。
    分割优先级：段落换行 > 句号 > 分号 > 逗号 > 空格 > 单字
    """
    return RecursiveCharacterTextSplitter(
        chunk_size=Config.CHUNK_SIZE,
        chunk_overlap=Config.CHUNK_OVERLAP,
        separators=["\n\n", "\n", "。", "；", "，", " ", ""],
        keep_separator=True,  # 保留标点，保持句子完整
    )


def _parse_pdf(file_path: Path) -> str:
    """用 pypdf 提取 PDF 文本"""
    from pypdf import PdfReader
    reader = PdfReader(str(file_path))
    parts: List[str] = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if text:
            parts.append(text)
    return "\n".join(parts)


def _parse_docx(file_path: Path) -> str:
    """用 python-docx 提取 Word 文本"""
    from docx import Document as DocxDocument
    doc = DocxDocument(str(file_path))
    parts: List[str] = []
    for para in doc.paragraphs:
        if para.text.strip():
            parts.append(para.text)
    return "\n".join(parts)


def _parse_txt(file_path: Path) -> str:
    """读取纯文本，自动处理 UTF-8 / GBK 编码"""
    try:
        return file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return file_path.read_text(encoding="gbk")
