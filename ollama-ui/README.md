# ─────────────── Backend ───────────────
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# ─────────────── Frontend ──────────────
cd frontend
npm install
npm run dev
# → Open http://localhost:5173

# ─────────────── Ollama ────────────────
ollama serve
ollama pull llama3.2
ollama pull nomic-embed-text   # for embeddings page