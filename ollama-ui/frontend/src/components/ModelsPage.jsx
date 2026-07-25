import { useState, useEffect } from "react";
import { Download, Trash2, RefreshCw, Activity } from "lucide-react";

export default function ModelsPage({ models, setModels }) {
  const [pullName, setPullName]     = useState("");
  const [pulling, setPulling]       = useState(false);
  const [pullLog, setPullLog]       = useState([]);
  const [deleting, setDeleting]     = useState("");
  const [runningModels, setRunning] = useState([]);

  // Poll running models every 5 seconds
  useEffect(() => {
    const fetchRunning = () =>
      fetch("/api/running")
        .then(r => r.json())
        .then(d => setRunning(d.models || []))
        .catch(() => setRunning([]));

    fetchRunning();
    const t = setInterval(fetchRunning, 5000);
    return () => clearInterval(t);
  }, []);

  const refreshModels = () =>
    fetch("/api/models").then(r => r.json()).then(d => setModels(d.models || []));

  const pullModel = async () => {
    if (!pullName.trim()) return;
    setPulling(true); setPullLog([]);

    const res = await fetch("/api/model/pull", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: pullName.trim() }),
    });

    const reader  = res.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      const text  = decoder.decode(value);
      const lines = text.split("\n").filter(l => l.startsWith("data: "));
      for (const line of lines) {
        try {
          const data = JSON.parse(line.slice(6));
          if (data.status) {
            setPullLog(prev => {
              const updated = [...prev];
              const last    = updated[updated.length - 1];
              if (last?.status === data.status) updated[updated.length - 1] = data;
              else updated.push(data);
              return updated.slice(-20);
            });
          }
        } catch {}
      }
    }
    setPulling(false);
    await refreshModels();
  };

  const deleteModel = async (name) => {
    if (!confirm(`Delete model "${name}"?`)) return;
    setDeleting(name);
    await fetch("/api/model/delete", {
      method: "DELETE", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name }),
    });
    setDeleting("");
    refreshModels();
  };

  const formatSize = (bytes) => {
    if (!bytes) return "—";
    const gb = bytes / 1e9;
    return gb >= 1 ? `${gb.toFixed(1)} GB` : `${(bytes / 1e6).toFixed(0)} MB`;
  };

  const formatExpiry = (expiresAt) => {
    if (!expiresAt) return "—";
    const diff = Math.round((new Date(expiresAt) - Date.now()) / 1000);
    if (diff <= 0) return "Expiring…";
    return diff > 60 ? `${Math.round(diff / 60)}m ${diff % 60}s` : `${diff}s`;
  };

  return (
    <div className="page">
      <div className="page-header flex items-center justify-between">
        <div>
          <h1>📦 Models</h1>
          <p>
            Manage models via <code>/api/tags</code> · <code>/api/pull</code> ·{" "}
            <code>/api/delete</code> · <code>/api/ps</code>
          </p>
        </div>
        <button className="btn btn-ghost" onClick={refreshModels}>
          <RefreshCw size={14} style={{ marginRight: 6 }} />Refresh
        </button>
      </div>

      <div className="page-body flex flex-col gap-4">

        {/* ── Running Models (Live) ── */}
        <div className="card flex flex-col gap-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Activity size={15} color="var(--accent)" />
              <strong>Running Models</strong>
              <span style={{
                background: "var(--bg)", border: "1px solid var(--border)",
                borderRadius: 20, padding: "1px 8px", fontSize: 11, color: "var(--accent)",
              }}>
                live · refreshes every 5s
              </span>
            </div>
            <span className="tag tag-green">{runningModels.length} loaded</span>
          </div>

          {runningModels.length === 0 ? (
            <div style={{ color: "var(--muted)", fontSize: 13, padding: "8px 0" }}>
              No models currently loaded in memory. Run a chat or generate request to load one.
            </div>
          ) : (
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr style={{ borderBottom: "1px solid var(--border)" }}>
                  {["Model", "Size (VRAM)", "Processor", "Expires In"].map(h => (
                    <th key={h} style={{
                      padding: "8px 12px", textAlign: "left", fontSize: 11,
                      color: "var(--muted)", fontWeight: 600, textTransform: "uppercase",
                    }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {runningModels.map((m) => (
                  <tr key={m.name} style={{ borderBottom: "1px solid var(--border)" }}>
                    <td style={{ padding: "10px 12px" }}>
                      <div className="flex items-center gap-2">
                        <span className="dot dot-green" />
                        <span style={{ fontWeight: 600 }}>{m.name}</span>
                      </div>
                    </td>
                    <td style={{ padding: "10px 12px" }}>
                      <span className="tag tag-yellow">{formatSize(m.size_vram)}</span>
                    </td>
                    <td style={{ padding: "10px 12px", color: "var(--muted)", fontSize: 12 }}>
                      {m.details?.family || "—"}
                    </td>
                    <td style={{ padding: "10px 12px" }}>
                      <span className="tag tag-green">{formatExpiry(m.expires_at)}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {/* ── Pull Model ── */}
        <div className="card flex flex-col gap-3">
          <strong>Pull a New Model</strong>
          <div className="flex gap-2">
            <input
              className="input"
              placeholder="e.g. llama3.2, mistral, gemma3:2b"
              value={pullName}
              onChange={e => setPullName(e.target.value)}
              onKeyDown={e => e.key === "Enter" && pullModel()}
            />
            <button
              className="btn btn-accent"
              onClick={pullModel}
              disabled={pulling}
              style={{ whiteSpace: "nowrap" }}
            >
              <Download size={14} style={{ marginRight: 6 }} />
              {pulling ? "Pulling…" : "Pull"}
            </button>
          </div>
          {pullLog.length > 0 && (
            <div style={{
              background: "var(--bg)", borderRadius: "var(--radius)", padding: 12,
              maxHeight: 180, overflowY: "auto", fontSize: 12, fontFamily: "monospace",
            }}>
              {pullLog.map((log, i) => (
                <div key={i} style={{ marginBottom: 4 }}>
                  <span style={{ color: "var(--accent)" }}>{log.status}</span>
                  {log.completed && log.total && (
                    <span style={{ color: "var(--muted)", marginLeft: 8 }}>
                      {formatSize(log.completed)} / {formatSize(log.total)}{" "}
                      ({Math.round((log.completed / log.total) * 100)}%)
                    </span>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* ── Installed Models Table ── */}
        <div className="card" style={{ padding: 0, overflow: "hidden" }}>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ borderBottom: "1px solid var(--border)", background: "var(--bg)" }}>
                {["Model", "Size", "Family", "Quantization", "Modified", "Actions"].map(h => (
                  <th key={h} style={{
                    padding: "10px 16px", textAlign: "left", fontSize: 11,
                    color: "var(--muted)", fontWeight: 600, textTransform: "uppercase",
                  }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {models.map((m, i) => (
                <tr key={m.name} style={{
                  borderBottom: i < models.length - 1 ? "1px solid var(--border)" : "none",
                  background: runningModels.some(r => r.name === m.name)
                    ? "rgba(0,212,170,0.04)" : "transparent",
                }}>
                  <td style={{ padding: "12px 16px" }}>
                    <div className="flex items-center gap-2">
                      {/* Green dot if model is currently loaded in memory */}
                      {runningModels.some(r => r.name === m.name) && (
                        <span className="dot dot-green" title="Currently loaded in memory" />
                      )}
                      <div>
                        <div style={{ fontWeight: 600 }}>{m.name}</div>
                        <div style={{ fontSize: 11, color: "var(--muted)", fontFamily: "monospace" }}>
                          {m.digest?.slice(0, 12)}…
                        </div>
                      </div>
                    </div>
                  </td>
                  <td style={{ padding: "12px 16px" }}>
                    <span className="tag tag-yellow">{formatSize(m.size)}</span>
                  </td>
                  <td style={{ padding: "12px 16px", color: "var(--muted)", fontSize: 12 }}>
                    {m.details?.family || "—"}
                  </td>
                  <td style={{ padding: "12px 16px" }}>
                    {m.details?.quantization_level && (
                      <span className="tag tag-green">{m.details.quantization_level}</span>
                    )}
                  </td>
                  <td style={{ padding: "12px 16px", color: "var(--muted)", fontSize: 12 }}>
                    {m.modified_at ? new Date(m.modified_at).toLocaleDateString() : "—"}
                  </td>
                  <td style={{ padding: "12px 16px" }}>
                    <button
                      className="btn btn-danger"
                      style={{ padding: "6px 10px" }}
                      onClick={() => deleteModel(m.name)}
                      disabled={deleting === m.name}
                    >
                      <Trash2 size={13} />
                    </button>
                  </td>
                </tr>
              ))}
              {models.length === 0 && (
                <tr>
                  <td colSpan={6} style={{ padding: 32, textAlign: "center", color: "var(--muted)" }}>
                    No models found. Pull one above.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

      </div>
    </div>
  );
}