import os
import re
from pathlib import Path
from typing import List

from llama_index.core import Document
from ebooklib import epub, ITEM_DOCUMENT
from bs4 import BeautifulSoup

from logger import get_logger

LOG = get_logger("epub_parser")

def clean_html(html_content: bytes) -> str:
    """Strip HTML tags and clean whitespace from epub chapter HTML."""
    soup = BeautifulSoup(html_content, "html.parser")

    # Remove script/style tags
    for tag in soup(["script", "style", "head"]):
        tag.decompose()
    text = soup.get_text(separator="\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def parse_epub(epub_path: str) -> List[Document]:
    """
    Parse an epub file into a list of LlamaIndex Documents.
    Each chapter becomes one Document with metadata.
    """
    book = epub.read_epub(epub_path)
    book_title = book.title or Path(epub_path).stem
    documents = []
    chapter_num = 0

    LOG.info(f"Parsing: '{book_title}' ({epub_path})")

    for item in book.get_items():
        # Only process HTML/XHTML document items (actual chapters)
        if item.get_type() != ITEM_DOCUMENT:
            continue
        content = item.get_content()
        text = clean_html(content)
        if (len(text) < 100):  # Skip very short chapters
            continue
        chapter_num += 1
        chapter_name = item.get_name() or f"Chapter {chapter_num}"
        doc = Document(
            text = text,
            metadata = {
                "source": os.path.basename(epub_path),
                "book_title": book_title,
                "chapter": chapter_name,
                "chapter_num": chapter_num
            }
        )
        documents.append(doc)
    return documents

def load_epubs(epub_paths: List[str]) -> List[Document]:
    """Load and parse multiple epub files."""
    all_documents = []
    for path in epub_paths:
        if not os.path.exists(path):
            LOG.error(f"File not found: {path}")
            continue
        all_documents.extend(parse_epub(path))
    LOG.info(f"Total documents parsed from all epubs: {len(all_documents)}")
    return all_documents