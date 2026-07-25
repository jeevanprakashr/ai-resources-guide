import logging

from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.llms import ollama
from llama_index.core.settings import Settings
from llama_index.embeddings.ollama import OllamaEmbedding

HTTP_CLIENT_LOG_FILE = "http_client.log"


def configure_logging(http_client_log_file=None):
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    for logger_name in ("httpx", "httpcore"):
        logger = logging.getLogger(logger_name)
        logger.handlers.clear()
        logger.propagate = False

        if http_client_log_file:
            handler = logging.FileHandler(http_client_log_file)
            handler.setLevel(logging.INFO)
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        else:
            logger.addHandler(logging.NullHandler())
            logger.setLevel(logging.WARNING)

def configure_ollama():
    llm_model = "qwen2.5:1.5b"
    embed_model = "nomic-embed-text"
    base_url = "http://localhost:11434"
    timeout = 120.0
    llm = ollama.Ollama(
        model = llm_model,
        base_url = base_url,
        request_timeout = timeout
    )
    embed_model = OllamaEmbedding(
        model_name = embed_model,
        base_url = base_url
    )
    Settings.llm = llm
    Settings.embed_model = embed_model
    Settings.chunk_size = 512


configure_logging(HTTP_CLIENT_LOG_FILE)
configure_ollama()
documents = SimpleDirectoryReader(input_files=["data.md"]).load_data()
index = VectorStoreIndex.from_documents(documents)
query_engine = index.as_query_engine()
while True:
    user_input = input("Enter your question: ")
    if (user_input.lower() == "exit"):
        break
    response = query_engine.query(user_input)
    print("Bot response:", response)