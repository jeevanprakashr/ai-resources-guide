import os
from typing import List, cast

from llama_index.core import (
    VectorStoreIndex,
    Document,
    StorageContext,
    load_index_from_storage
)

from logger import get_logger
from epub_parser import load_epubs

LOG = get_logger("indexer")
INDEX_DIR = "./epub_index"

def build_index(documents: List[Document]) -> VectorStoreIndex:
    """Build vector index from documents and persist to disk."""
    LOG.info(f"Building index with {len(documents)} documents...")
    index = VectorStoreIndex.from_documents(
        documents,
        show_progress = True
    )
    index.storage_context.persist(persist_dir = INDEX_DIR)
    LOG.info(f"Index built and saved to '{INDEX_DIR}'")
    return index

def load_index() -> VectorStoreIndex:
    """Load a previously saved index from disk."""
    LOG.info(f"Loading index from '{INDEX_DIR}'...")
    storage_context = StorageContext.from_defaults(persist_dir = INDEX_DIR)
    index = load_index_from_storage(storage_context)
    LOG.info("Index loaded successfully.")
    return cast(VectorStoreIndex, index)

def get_index(epub_paths: List[str], force_rebuild: bool = False) -> VectorStoreIndex:
    """Build index if not cached, otherwise load from disk."""
    if not force_rebuild and os.path.exists(INDEX_DIR):
        return load_index()
    documents = load_epubs(epub_paths)
    return build_index(documents)