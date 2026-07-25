import os
import logging
from pathlib import Path
from llama_index.core import Settings
from llama_index.core.chat_engine.types import ChatMode, BaseChatEngine
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.llms.ollama import Ollama

from logger import get_logger
from indexer import get_index, check_and_build_index

# Suppress llama_index (and httpx) console output
logging.getLogger("llama_index").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

# ── System prompt — the personality of BookBuddy ────────
SYSTEM_PROMPT = """\
You are **BookBuddy** 🧙‍♂️ — a friendly, enthusiastic companion who has \
read every book in the user's collection cover to cover.

Rules:
- Talk like a fellow fan / friend, not a formal assistant.
- When answering, reference specific events, chapters, or quotes from the \
  books using the context provided.
- If you're unsure or the context doesn't contain the answer, say so honestly \
  instead of making things up.
- Avoid spoilers unless the user explicitly asks.
- Feel free to use emojis and have fun!
"""

def configure_ollama():
    Settings.llm = Ollama(
        model = "llama3.2:1b",
        request_timeout = 120
    )
    Settings.embed_model = OllamaEmbedding(
        model_name = "nomic-embed-text",
    )
    Settings.chunk_size = 1024 # 1536
    Settings.chunk_overlap = 256

def load_chat_engine() -> BaseChatEngine:
    """Load persisted index and return a chat engine."""
    index = get_index()
    chat_engine = index.as_chat_engine(
        chat_mode = ChatMode.CONDENSE_PLUS_CONTEXT, # reformulates + retrieves
        system_prompt = SYSTEM_PROMPT,
        similarity_top_k = 8,    # retrieve top 8 relevant chunks
        verbose = False
    )
    return chat_engine

def main():
    configure_ollama()
    engine = load_chat_engine()
    print("=" * 60)
    print("  📚 BookBuddy — Your AI Reading Companion")
    print("  Type 'quit' to exit  |  'reset' to clear history")
    print("=" * 60)
    while True:
        user_input = input("\n🧑 You: ").strip()
        if not user_input:
            continue
        if user_input.lower() == "quit":
            print("👋 Goodbye! Happy reading!")
            break
        if user_input.lower() == "reset":
            engine.reset()
            print("🔄 Conversation history cleared.")
            continue

        response = engine.chat(user_input)
        print(f"\n🧙 BookBuddy: {response}\n")

    os._exit(0)

if __name__ == "__main__":
    main()
    # check_and_build_index()