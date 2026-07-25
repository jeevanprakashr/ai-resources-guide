import { Routes, Route, Navigate } from "react-router-dom";
import { useState, useEffect } from "react";
import Sidebar from "./components/Sidebar";
import ChatPage from "./components/ChatPage";
import GeneratePage from "./components/GeneratePage";
import EmbeddingsPage from "./components/EmbeddingsPage";
import ModelsPage from "./components/ModelsPage";
import ModelInfoPage from "./components/ModelInfoPage";

export default function App() {
  const [ollamaOk, setOllamaOk] = useState(null);
  const [models, setModels] = useState([]);

  // Poll Ollama health every 10s
  useEffect(() => {
    const check = async () => {
      try {
        const r = await fetch("/health");
        const d = await r.json();
        setOllamaOk(d.ollama);
      } catch { setOllamaOk(false); }
    };
    check();
    const t = setInterval(check, 10000);
    return () => clearInterval(t);
  }, []);

  // Load models on startup
  useEffect(() => {
    if (!ollamaOk) return;
    fetch("/api/models")
      .then(r => r.json())
      .then(d => setModels(d.models || []))
      .catch(() => {});
  }, [ollamaOk]);

  return (
    <div style={{ display: "flex", width: "100%", height: "100vh" }}>
      <Sidebar ollamaOk={ollamaOk} />
      <main style={{ flex: 1, overflow: "hidden", display: "flex", flexDirection: "column" }}>
        <Routes>
          <Route path="/" element={<Navigate to="/chat" replace />} />
          <Route path="/chat"       element={<ChatPage       models={models} />} />
          <Route path="/generate"   element={<GeneratePage   models={models} />} />
          <Route path="/embeddings" element={<EmbeddingsPage models={models} />} />
          <Route path="/models"     element={<ModelsPage     models={models} setModels={setModels} />} />
          <Route path="/model-info" element={<ModelInfoPage  models={models} />} />
        </Routes>
      </main>
    </div>
  );
}