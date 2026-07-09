"""
法律库拉取模块 -- 从 GitHub 上的 lawtext/laws 仓库自动获取中国法律文本。

数据源：https://github.com/lawtext/laws
格式：Markdown（含 YAML front matter），每条款用 "- **第X条**" 标记
总量：2400+ 法律文件，涵盖法律、行政法规、司法解释、宪法等
"""

import re
import subprocess
from pathlib import Path
from typing import List, Optional

from langchain_core.documents import Document

from src.config import Config

# 匹配 YAML front matter 中的 title 字段
_TITLE_PATTERN = re.compile(r"^title:\s*(.+)$", re.MULTILINE)

# 匹配文章条款: "- **第X条**  content"（支持全角空格、多行内容）
# 一个条款从 "- **第X条**" 开始，到下一个 "- **第X条**" 或 "## " 或文件末尾结束
_ARTICLE_START = re.compile(r"^- \*\*第(.+?)条\*\*[\s　]*(.*)", re.MULTILINE)

# 法律库的 GitHub 地址（纯文本，不使用 LFS）
_LAWS_REPO_URL = "https://github.com/lawtext/laws.git"


class LawFetcher:
    """
    法律库拉取器。
    用法:
        fetcher = LawFetcher()
        docs = fetcher.fetch()            # 首次下载
        docs = fetcher.load_documents()   # 直接从本地加载
    """

    def __init__(self, local_dir: Path = None):
        self.repo_url = Config.LAWS_REPO_URL
        self.local_dir = local_dir or Config.LAWS_REPO_DIR

    # ============================================================
    # 公开方法
    # ============================================================

    def fetch(self) -> List[Document]:
        """
        完整拉取流程：如果本地已有则跳过，没有则 git clone。
        返回解析后的 Document 列表。
        """
        if self._has_data():
            print(f"[INFO] 已存在法律库，如需更新请手动 git pull")
            return self.load_documents()

        print(f"[INFO] 正在从 GitHub 下载法律库（lawtext/laws，2400+ 部法律）...")
        self._git_clone()
        return self.load_documents()

    def load_documents(self) -> List[Document]:
        """
        从本地 laws 目录递归读取所有 .md 法律文件，
        解析为 LangChain Document 列表（每条条款一个 Document）。
        """
        if not self._has_data():
            raise RuntimeError(
                f"法律库目录不存在或无数据: {self.local_dir}\n"
                f"请先运行 python main.py init 自动下载"
            )

        # 收集所有法律 .md 文件（排除 _index.md）
        md_files = [
            f for f in self.local_dir.rglob("*.md")
            if f.name != "_index.md"
        ]

        print(f"[INFO] 正在解析 {len(md_files)} 个法律文件...")

        all_docs: List[Document] = []
        for md_file in md_files:
            docs = self._parse_markdown_law(md_file)
            all_docs.extend(docs)

        print(f"[OK] 共解析出 {len(all_docs)} 条法律条款")
        return all_docs

    # ============================================================
    # Git 操作
    # ============================================================

    def _has_data(self) -> bool:
        """检查本地是否已有法律数据"""
        if not self.local_dir.exists():
            return False
        if (self.local_dir / ".git").exists():
            return True
        # 检查是否有 .md 文件
        if list(self.local_dir.rglob("*.md")):
            return True
        return False

    def _git_clone(self) -> None:
        """git clone 法律库到本地"""
        self.local_dir.parent.mkdir(parents=True, exist_ok=True)
        self._run_git([
            "clone", "--depth", "1",
            self.repo_url, str(self.local_dir),
        ], description="git clone")

    @staticmethod
    def _run_git(args: List[str], cwd: str = None, description: str = "git") -> None:
        """执行 git 命令，出错时抛出异常"""
        cmd = ["git"] + args
        result = subprocess.run(
            cmd, cwd=cwd,
            capture_output=True, text=True, encoding="utf-8",
            timeout=300,
        )
        if result.returncode != 0:
            stderr = result.stderr.strip()
            raise RuntimeError(f"{description} 失败:\n{stderr}")
        if result.stdout:
            print(result.stdout.strip())

    # ============================================================
    # Markdown 法律文件解析
    # ============================================================

    def _parse_markdown_law(self, md_file: Path) -> List[Document]:
        """
        解析单个 Markdown 法律文件。

        格式：
          ---
          title: 中华人民共和国XXX法
          categories: [法律, ...]
          keywords: [...]
          ---
          正文内容...
          - **第一条**　　条款内容
          - **第二条**　　条款内容

        每条条款生成一个 Document，metadata 包含法律名、条款号、分类、关键词。
        """
        docs: List[Document] = []

        try:
            text = md_file.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return docs

        # 分离 front matter 和正文
        body = text
        law_name = md_file.stem  # 默认用文件名

        # 提取 YAML front matter 中的 title
        if text.startswith("---"):
            parts = text.split("---", 2)
            if len(parts) >= 3:
                front_matter = parts[1]
                body = parts[2]

                # 提取法律名
                title_match = _TITLE_PATTERN.search(front_matter)
                if title_match:
                    law_name = title_match.group(1).strip()

        # 如果 body 为空，跳过
        if not body.strip():
            return docs

        # 用正则切分出每个条款
        # 策略：找到所有 "- **第X条**" 的位置，然后切分
        article_matches = list(_ARTICLE_START.finditer(body))

        if not article_matches:
            # 没有找到条款格式的内容，可能整篇就是一条（如宪法序言等）
            # 跳过，不做整篇索引
            return docs

        for i, match in enumerate(article_matches):
            article_num = match.group(1)       # 条款号（如 "一"、"1"、"十二"）
            article_start = match.group(2)     # 该条款第一行内容

            # 确定条款内容结束位置：到下一个条款开始，或到 "## " 标题，或到文件末尾
            content_start = match.start()
            if i + 1 < len(article_matches):
                content_end = article_matches[i + 1].start()
            else:
                # 找到下一个 "## " 的位置
                next_section = re.search(r"\n## ", body[content_start:])
                if next_section:
                    content_end = content_start + next_section.start()
                else:
                    content_end = len(body)

            # 提取完整条款文本
            full_article_text = body[content_start:content_end].strip()

            # 清理：把第一行的 "- **第X条**" 替换为更干净的格式
            clean_text = re.sub(
                r"^- \*\*第.+?条\*\*[\s　]*",
                f"《{law_name}》第{article_num}条规定，",
                full_article_text
            )

            docs.append(Document(
                page_content=clean_text,
                metadata={
                    "law_name": law_name,
                    "article": f"第{article_num}条",
                    "source_file": md_file.name,
                    "law_category": self._get_category(md_file),
                },
            ))

        return docs

    @staticmethod
    def _get_category(md_file: Path) -> str:
        """根据文件路径判断法律分类"""
        path_str = str(md_file)
        if "法律" in path_str:
            return "法律"
        elif "行政法规" in path_str:
            return "行政法规"
        elif "司法解释" in path_str:
            return "司法解释"
        elif "宪法" in path_str:
            return "宪法"
        elif "监察法规" in path_str:
            return "监察法规"
        return "其他"
