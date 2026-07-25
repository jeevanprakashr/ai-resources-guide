"""
LlamaIndex + Ollama (No OpenAI API Key Required)
==================================================
LLM       : llama3.2        (via Ollama - local)
Embeddings: nomic-embed-text (via Ollama - local)
Use Cases :
  1. Basic LLM Chat
  2. Text-to-SQL         (DuckDB in-memory)
  3. Document Q&A        (VectorStoreIndex)
  4. Simple Q&A          (No documents)
"""

from llama_index.core import Settings, SQLDatabase, VectorStoreIndex, Document
from llama_index.core.query_engine import NLSQLTableQueryEngine
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.ollama import OllamaEmbedding
from sqlalchemy import create_engine, text


# ══════════════════════════════════════════════════════════
# STEP 1 — Configure Ollama as the Global LLM & Embeddings
#           (Replaces the default OpenAI requirement)
# ══════════════════════════════════════════════════════════
def configure_ollama(
    llm_model   : str = "llama3.2",
    embed_model : str = "nomic-embed-text",
    base_url    : str = "http://localhost:11434",
    timeout     : float = 120.0,
):
    """
    Globally configure LlamaIndex to use Ollama
    instead of OpenAI for both LLM and Embeddings.
    """
    llm = Ollama(
        model          = llm_model,
        base_url       = base_url,
        request_timeout= timeout,
    )

    embed = OllamaEmbedding(
        model_name = embed_model,
        base_url   = base_url,
    )

    # ── Set globally so ALL LlamaIndex components use Ollama ──
    Settings.llm         = llm
    Settings.embed_model = embed

    print(f"✅ LLM        : Ollama ({llm_model})")
    print(f"✅ Embeddings : Ollama ({embed_model})")
    print(f"✅ Base URL   : {base_url}")
    print(f"✅ No OpenAI API Key needed!\n")

    return llm, embed


# ══════════════════════════════════════════════════════════
# USE CASE 1 — Basic LLM Chat
# ══════════════════════════════════════════════════════════
def demo_basic_chat(llm: Ollama):
    print("=" * 55)
    print("  USE CASE 1 : Basic LLM Chat")
    print("=" * 55)

    questions = [
        "What is DuckDB in one sentence?",
        "What is the difference between RAG and fine-tuning?",
    ]

    for question in questions:
        response = llm.complete(question)
        print(f"\n❓ {question}")
        print(f"💬 {response.text.strip()}")

    print()


# ══════════════════════════════════════════════════════════
# USE CASE 2 — Text-to-SQL with DuckDB In-Memory
# ══════════════════════════════════════════════════════════
def demo_text_to_sql():
    print("=" * 55)
    print("  USE CASE 2 : Text-to-SQL (DuckDB In-Memory)")
    print("=" * 55)

    # ── Setup DuckDB ──────────────────────────────────────
    engine = create_engine("duckdb:///:memory:")

    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE employees (
                id         INTEGER,
                name       VARCHAR,
                department VARCHAR,
                salary     DOUBLE,
                hire_year  INTEGER
            )
        """))
        conn.execute(text("""
            INSERT INTO employees VALUES
                (1, 'Alice',   'Engineering', 95000, 2019),
                (2, 'Bob',     'Marketing',   72000, 2020),
                (3, 'Carol',   'Engineering', 105000,2018),
                (4, 'David',   'HR',          60000, 2021),
                (5, 'Eva',     'Engineering', 98000, 2019),
                (6, 'Frank',   'Marketing',   68000, 2022),
                (7, 'Grace',   'Finance',     88000, 2020),
                (8, 'Henry',   'HR',          62000, 2023),
                (9, 'Isla',    'Finance',     91000, 2017),
                (10,'Jack',    'Engineering', 112000,2016)
        """))
        conn.commit()

    # ── LlamaIndex SQL Setup ──────────────────────────────
    sql_database = SQLDatabase(
        engine,
        include_tables=["employees"]
    )

    query_engine = NLSQLTableQueryEngine(
        sql_database = sql_database,
        verbose      = True,       # prints generated SQL
    )

    # ── Natural Language Queries ──────────────────────────
    questions = [
        "How many employees are in each department?",
        "What is the highest salary in Engineering?",
        "Who was hired before 2019?",
    ]

    for question in questions:
        print(f"\n❓ {question}")
        response = query_engine.query(question)
        print(f"💬 {response}")

    print()


# ══════════════════════════════════════════════════════════
# USE CASE 3 — Document Q&A (RAG with VectorStoreIndex)
# ══════════════════════════════════════════════════════════
def demo_document_qa():
    print("=" * 55)
    print("  USE CASE 3 : Document Q&A (RAG)")
    print("=" * 55)

    # ── Sample Documents (your knowledge base) ────────────
    documents = [
        Document(text="""
            LlamaIndex is a data framework for LLM applications.
            It provides tools to ingest, structure, and retrieve
            data for use with large language models. It supports
            vector stores, SQL databases, and many other data sources.
            LlamaIndex was formerly known as GPT Index.
        """),
        Document(text="""
            DuckDB is an in-process SQL OLAP database management system.
            It is designed to support analytical query workloads.
            DuckDB can run entirely in-memory without any setup.
            It supports standard SQL and integrates well with Python
            via SQLAlchemy and its native Python client.
        """),
        Document(text="""
            Ollama is a tool that lets you run large language models
            locally on your own machine. It supports models like
            LLaMA, Mistral, Gemma, and many others. Ollama provides
            a REST API server at localhost:11434 by default.
            It uses GGUF model format for efficient inference.
        """),
        Document(text="""
            RAG stands for Retrieval Augmented Generation. It is a
            technique that combines a retrieval system with a generative
            model. First, relevant documents are retrieved using
            embeddings and vector similarity. Then the LLM generates
            an answer using those retrieved documents as context.
        """),
    ]

    # ── Build VectorStore Index (uses OllamaEmbedding) ───
    print("📚 Building vector index from documents...")
    index = VectorStoreIndex.from_documents(documents)

    # ── Create Query Engine ────────────────────────────────
    query_engine = index.as_query_engine(
        similarity_top_k = 2,      # retrieve top 2 relevant chunks
    )

    # ── Ask Questions ──────────────────────────���──────────
    questions = [
        "What is LlamaIndex used for?",
        "How does RAG work?",
        "What model format does Ollama use?",
    ]

    for question in questions:
        print(f"\n❓ {question}")
        response = query_engine.query(question)
        print(f"💬 {response}")

    print()


# ══════════════════════════════════════════════════════════
# USE CASE 4 — Streaming Response
# ══════════════════════════════════════════════════════════
def demo_streaming(llm: Ollama):
    print("=" * 55)
    print("  USE CASE 4 : Streaming Response")
    print("=" * 55)

    prompt = "Explain what an embedding model does in 3 bullet points."
    print(f"\n❓ {prompt}")
    print("💬 ", end="", flush=True)

    # Stream tokens as they are generated
    response_stream = llm.stream_complete(prompt)
    for chunk in response_stream:
        print(chunk.delta, end="", flush=True)

    print("\n")


# ══════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════
def main():
    print("\n" + "=" * 55)
    print("  LlamaIndex + Ollama  |  No OpenAI Key Needed")
    print("=" * 55 + "\n")

    # ── Configure Ollama globally for LlamaIndex ──────────
    llm, embed = configure_ollama(
        llm_model   = "llama3.2",        # change to any ollama model
        embed_model = "nomic-embed-text", # change to any ollama embed model
    )

    # ── Run all demos ─────────────────────────────────────
    demo_basic_chat(llm)
    demo_text_to_sql()
    demo_document_qa()
    demo_streaming(llm)


if __name__ == "__main__":
    main()