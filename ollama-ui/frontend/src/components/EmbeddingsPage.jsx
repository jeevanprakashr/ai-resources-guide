import { useState, useEffect } from "react";

export default function EmbeddingsPage({ models }) {
  const [model, setModel]   = useState("");
  const [textA, setTextA]   = useState("The cat sat on the mat");
  const [textB, setTextB]   = useState("A kitten rested on the rug");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError]   = useState("");

  // Filter embedding-friendly models
  const embedModels = models.filter(m =>
    m.name.includes("embed") || m.name.includes("nomic") ||
    m.name.includes("mxbai") || m.name.includes("bge")
  );
  const allModels = embedModels.length ? embedModels : models;

  useEffect(() => { if (allModels.length) setModel(allModels[0].name); }, [models]);

  const cosineSim = (a, b) => {
    const dot  = a.reduce((s, v, i) => s + v * b[i], 0);
    const magA = Math.sqrt(a.reduce((s, v) => s + v * v, 0));
    const magB = Math.sqrt(b.reduce((s, v) => s + v * v, 0));
    return dot / (magA * magB);
  };

  const embed = async () => {
    if (!textA.trim() || !model) return;
    setLoading(true); setError(""); setResult(null);
    try {
      const [r1, r2] = await Promise.all([
        fetch("/api/embed", {
          method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ model, input: textA }),
        }).then(r => r.json()),
        textB.trim()
          ? fetch("/api/embed", {
              method: "POST", headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ model, input: textB }),
            }).then(r => r.json())
          : null,
      ]);
      const similarity = r2 ? cosineSim(r1.embedding, r2.embedding) : null;
      setResult({ r1, r2, similarity });
    } catch (e) { setError(e.message); }
    setLoading(false);
  };

  const simColor = (s) => s > 0.85 ? "var(--success)" : s > 0.5 ? "var(--warning)" : "var(--danger)";
  const simLabel = (s) => s > 0.85 ? "Very Similar" : s > 0.5 ? "Somewhat Similar" : "Different";

  return (
    <div className="page">
      <div className="page-header">
        <h1># Embeddings</h1>
        <p>Generate vector embeddings & compare similarity via <code>/api/embed</code></p>
      </div>
      <div className="page-body flex flex-col gap-4">
        {/* Controls */}
        <div className="card flex flex-col gap-3">
          <div>
            <label>Embedding Model</label>
            <select className="select" value={model} onChange={e => setModel(e.target.value)}>
              {allModels.map(m => <option key={m.name} value={m.name}>{m.name}</option>)}
            </select>
          </div>
          <div className="grid-2">
            <div>
              <label>Text A</label>
              <textarea className="textarea" value={textA} onChange={e => setTextA(e.target.value)} />
            </div>
            <div>
              <label>Text B (optional — for similarity)</label>
              <textarea className="textarea" value={textB} onChange={e => setTextB(e.target.value)} />
            </div>
          </div>
          <button className="btn btn-primary" onClick={embed} disabled={loading || !model}>
            {loading ? "Embedding…" : "Generate Embeddings"}
          </button>
          {error && <div style={{ color: "var(--danger)", fontSize: 12 }}>{error}</div>}
        </div>

        {result && (
          <>
            {/* Similarity Score */}
            {result.similarity !== null && (
              <div className="card" style={{ textAlign: "center" }}>
                <div style={{ fontSize: 12, color: "var(--muted)", marginBottom: 8 }}>Cosine Similarity</div>
                <div style={{ fontSize: 48, fontWeight: 800, color: simColor(result.similarity) }}>
                  {result.similarity.toFixed(4)}
                </div>
                <div className="tag" style={{ marginTop: 8, background: "var(--surface)", color: simColor(result.similarity) }}>
                  {simLabel(result.similarity)}
                </div>
                <div style={{ marginTop: 12, fontSize: 12, color: "var(--muted)" }}>
                  1.0 = identical meaning &nbsp;|&nbsp; 0.0 = no relation &nbsp;|&nbsp; -1.0 = opposite
                </div>
              </div>
            )}

            {/* Vector Info */}
            <div className="grid-2">
              {[{ label: "Text A", data: result.r1 }, result.r2 && { label: "Text B", data: result.r2 }]
                .filter(Boolean).map(({ label, data }) => (
                <div key={label} className="card flex flex-col gap-3">
                  <div className="flex items-center justify-between">
                    <strong>{label}</strong>
                    <span className="tag tag-purple">{data.dimensions} dims</span>
                  </div>
                  <div style={{ fontSize: 12, color: "var(--muted)", wordBreak: "break-all" }}>
                    "{data.model}"
                  </div>
                  <div>
                    <label>First 10 values</label>
                    <div className="vector-grid">
                      {data.preview.map((v, i) => (
                        <div key={i} className="vector-cell">{v.toFixed(4)}</div>
                      ))}
                      <div className="vector-cell" style={{ color: "var(--muted)" }}>…+{data.dimensions - 10} more</div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
}