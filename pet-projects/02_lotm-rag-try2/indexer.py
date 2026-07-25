import re
from pathlib import Path
from typing import cast
from llama_index.core import (
    SimpleDirectoryReader,
    VectorStoreIndex,
    StorageContext,
    load_index_from_storage
)

from logger import get_logger

BOOKS_DIR = "./books"
STORAGE_DIR = "./bookbuddy_index"
LOG = get_logger("indexer")

def check_and_build_index(force_rebuild: bool = False):
    if (not force_rebuild) and Path(STORAGE_DIR).exists():
        return
    print("Building index from EPUB files. This may take a moment...")
    LOG.info(f"📖 Reading EPUBs from '{BOOKS_DIR}' ...")
    reader = SimpleDirectoryReader(
        input_dir = BOOKS_DIR,
        required_exts = [".epub"],
        recursive = True
    )
    documents = reader.load_data()
    LOG.info(f"Loaded {len(documents)} document chunks.")

    # Add metadata so the LLM knows which book a chunk is from
    for doc in documents:
        file_name = doc.metadata.get("file_name", "unknown")
        book_name = file_name.replace(".epub", "")
        idx = book_name.find("(")
        if idx != -1:
            book_name = book_name[:idx].strip()
        doc.metadata["book_full_name"] = book_name
        doc.metadata["novel_series_name"] = "Lord of Mysteries"
        match = re.search(r"Volume\s+(\d+)\s([A-Za-z\s]+)", book_name, re.IGNORECASE)
        if match:
            volume = int(match.group(1))
            title = match.group(2).strip()
            doc.metadata["volume"] = volume
            doc.metadata["title"] = title
    LOG.info("Building vector index...")
    index = VectorStoreIndex.from_documents(documents, show_progress = True)
    # Persist the index to disk so that we can avoid re-indexing every time
    index.storage_context.persist(persist_dir = STORAGE_DIR)
    print("Index built successfully!")
    LOG.info(f"Index built and saved to '{STORAGE_DIR}'")

def get_index(force_rebuild: bool = False) -> VectorStoreIndex:
    """Load index from disk, or build it if it doesn't exist."""
    check_and_build_index(force_rebuild)
    LOG.info(f"Loading index from '{STORAGE_DIR}'...")
    storage_context = StorageContext.from_defaults(persist_dir = STORAGE_DIR)
    index = load_index_from_storage(storage_context)
    LOG.info("Index loaded successfully.")
    return cast(VectorStoreIndex, index)