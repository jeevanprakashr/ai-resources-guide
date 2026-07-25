import os

from llama_index.core import SQLDatabase, SimpleDirectoryReader, Document, ServiceContext, set_global_service_context
from llama_index.core.settings import Settings
from llama_index.core.indices.struct_store import NLSQLTableQueryEngine, SQLTableRetrieverQueryEngine
from llama_index.llms import openai, anthropic, ollama
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.embeddings.ollama import OllamaEmbedding
from sqlalchemy import (
    MetaData,
    Table,
    Column,
    String,
    Integer,
    create_engine,
    select,
    column,
    insert
)

def configure_ollama():
    llm_model = "qwen2.5-coder:1.5b"
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

## Define SQLAlchemy table
metadata_obj = MetaData()
city_stats_table = Table(
    "city_stats",
    metadata_obj,
    Column("city_name", String(16), primary_key=True),
    Column("population", Integer),
    Column("country", String(16), nullable=False)
)
# print(metadata_obj.tables)

## Create in-memory DuckDB engine, bind it to SQLAlchemy metadata - creates table in DuckDB
engine = create_engine("duckdb:///:memory:")
metadata_obj.create_all(engine)

## Insert data into the table
rows = [
    {"city_name": "Toronto", "population": 2930000, "country": "Canada"},
    {"city_name": "Tokyo", "population": 13960000, "country": "Japan"},
    {"city_name": "Chicago", "population": 2679000, "country": "United States"},
    {"city_name": "Seoul", "population": 9776000, "country": "South Korea"},
]
with engine.begin() as conn:
    for row in rows:
        stmt = insert(city_stats_table).values(**row)
        conn.execute(stmt)

## Fetch from DuckDB
with engine.connect() as conn:
    cursor = conn.exec_driver_sql("SELECT * FROM city_stats")
    print(cursor.fetchall())


## Setting up LLM in llama_index
# with open("openai.txt") as f:
#     api_key = f.read().strip()
#     os.environ["OPENAI_API_KEY"] = api_key

# with open("anthropic.txt") as f:
#     api_key = f.read().strip()
#     os.environ["ANTHROPIC_API_KEY"] = api_key

# llm = openai.OpenAI(model="gpt-3.5-turbo")
# llm = anthropic.Anthropic(model="claude-opus-4-0", temperature=0.9)
# llm = ollama.Ollama(model="llama3.1", temperature=0.9)
# Settings.llm = llm
# Settings.embed_model = HuggingFaceEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")
# service_context = ServiceContext.from_defaults(llm=llm)
configure_ollama()

## Bind SQL database to llama_index, create query engine, and query
sql_database = SQLDatabase(engine, include_tables=["city_stats"])   # pip install "SQLAlchemy<2.0.36"
query_engine_openai = NLSQLTableQueryEngine(sql_database)
qry = "Which city has the highest population?"
res = query_engine_openai.query(qry)
print("Result:\n", res, "\n")
# print("MetaData:\n", res.metadata, "\n")
# print("Response:\n", res.response)

qry = "What is the overall population of all cities?"
res = query_engine_openai.query(qry)
print("Result:\n", res, "\n")

