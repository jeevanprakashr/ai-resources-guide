import os
import re
from pathlib import Path
from typing import List

from ebooklib import epub
from bs4 import BeautifulSoup

from llama_index.core import (
    Settings,
    VectorStoreIndex,
    Document,
    StorageContext,
    load_index_from_storage
)
from llama_index.core.query_engine import BaseQueryEngine
from llama_index.core.node_parser import SentenceSplitter
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.ollama import OllamaEmbedding

from logger import get_logger
from indexer import get_index

LOG = get_logger()
INDEX_DIR = "./epub_index"
EPUB_FILES = sorted([os.path.join("./books", f.name) for f in Path("./books").glob("*.epub")])

def configure_ollama():
    Settings.llm = Ollama(
        model = "llama3.2",
        request_timeout = 120.0
    )
    Settings.embed_model = OllamaEmbedding(
        model_name = "nomic-embed-text",
    )
    # Chunk settings
    Settings.node_parser = SentenceSplitter(
        chunk_size = 32000,   # tokens per chunk
        chunk_overlap = 8000  # overlap to preserve context
    )
    LOG.info("Ollama LLM and embedding models configured.")

def ask(query_engine: BaseQueryEngine, question: str):
    """Ask a question and display the answer with source chapters."""
    print(f"\n{'─'*60}")
    print(f"❓ {question}")
    print(f"{'─'*60}")

    response = query_engine.query(question)
    print(f"💬 {response}\n")

    # Show source chunks used for the answer
    if hasattr(response, "source_nodes") and response.source_nodes:
        print("📎 Sources:")
        for i, node in enumerate(response.source_nodes, 1):
            meta = node.metadata
            score = node.score or 0
            print(f"  [{i}] '{meta.get('book_title', '?')}'"
                  f" — {meta.get('chapter', '?')}"
                  f"  (score: {score:.3f})")
    print()

if __name__ == "__main__":
    configure_ollama()
    index = get_index(EPUB_FILES)
    query_engine = index.as_query_engine(
        similarity_top_k = 5,   # retrieve top 4 relevant chunks
        streaming = False
    )
    # question = input("Enter your question about the books: ")
    # ask(query_engine, question)
    while True:
        try:
            user_input = input("\n❓ Your question: ").strip()
            if user_input.lower() in ("quit", "exit", "q"):
                break
            if user_input:
                ask(query_engine, user_input)
        except KeyboardInterrupt:
            break

    print("\n👋 Goodbye!")
