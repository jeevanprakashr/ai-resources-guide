import { useState, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import { Zap } from "lucide-react";

export default function GeneratePage({ models }) {
  const [model, setModel]           = useState("");
  const [prompt, setPrompt]         = useState("");
  const [output, setOutput]         = useState("");
  const [loading, setLoading]       = useState(false);
  const [stream, setStream]         = useState(true);
  const [temperature, setTemperature] = useState(0.7);
  const [stats, setStats]           = useState(null);

  useEffect(() => { if (models.length) setModel(models[0].name); }, [models]);

  const generate = async () => {
    if (!prompt.trim() || !model || loading) return;
    setLoading(true);
    setOutput("");
    setStats(null);

    if (stream) {
      const res = await fetch("/api/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ model, prompt, stream: true, temperature }),
      });
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let fullText = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const text = decoder.decode(value);
        const lines = text.split("\n").filter(l => l.startsWith("data: "));
        for (const line of lines) {
          try {
            const data = JSON.parse(line.slice(6));
            if (data.response) {
              fullText += data.response;
              setOutput(fullText);
            }
            if (data.done && data.eval_count) {
              setStats({
                tokens     : data.eval_count,
                promptTokens: data.prompt_eval_count,
                duration   : (data.total_duration / 1e9).toFixed(2),
                tokensPerSec: (data.eval_count / (data.eval_duration / 1e9)).toFixed(1),
              });
            }
          } catch {}
        }
      }
    } else {
      const res = await fetch("/api/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ model, prompt, stream: false, temperature }),
      });
      const data = await res.json();
      setOutput(data.response || "No response");
      if (data.eval_count) {
        setStats({
          tokens      : data.eval_count,
          promptTokens: data.prompt_eval_count,
          duration    : (data.total_duration / 1e9).toFixed(2),
          tokensPerSec: (data.eval_count / (data.eval_duration / 1e9)).toFixed(1),
        });
      }
    }
    setLoading(false);
  };

  const EXAMPLES = [
    "Write a Python function to reverse a linked list.",
    "Explain the difference between TCP and UDP in simple terms.",
    "Write a SQL query to find the top 5 customers by total sales.",
    "What is the time complexity of quicksort?",
  ];

  return (
    <div className="page">
      <div className="page-header">
        <h1>⚡ Generate</h1>
        <p>Single-shot text completion via <code>/api/generate</code></p>
      </div>
      <div className="page-body">
        <div className="grid-2">
          {/* LEFT — Input */}
          <div className="flex flex-col gap-3">
            <div>
              <label>Model</label>
              <select className="select" value={model} onChange={e => setModel(e.target.value)}>
                {models.map(m => <option key={m.name} value={m.name}>{m.name}</option>)}
              </select>
            </div>
            <div>
              <label>Prompt</label>
              <textarea className="textarea" style={{ minHeight: 140 }}
                placeholder="Enter your prompt…"
                value={prompt} onChange={e => setPrompt(e.target.value)} />
            </div>
            <div className="flex items-center gap-4">
              <div style={{ flex: 1 }}>
                <label>Temperature: {temperature}</label>
                <input type="range" min="0" max="2" step="0.1" value={temperature}
                  onChange={e => setTemperature(Number(e.target.value))}
                  className="w-full" />
              </div>
              <div className="flex items-center gap-2 mt-3">
                <label style={{ margin: 0 }}>Stream</label>
                <input type="checkbox" checked={stream} onChange={e => setStream(e.target.checked)} />
              </div>
            </div>
            <button className="btn btn-accent w-full" onClick={generate} disabled={loading || !model}>
              {loading ? "Generating…" : <><Zap size={14} style={{ marginRight: 6 }} />Generate</>}
            </button>
            {/* Examples */}
            <div>
              <label>Quick Examples</label>
              <div className="flex flex-col gap-2">
                {EXAMPLES.map((ex, i) => (
                  <button key={i} className="btn btn-ghost" style={{ textAlign: "left", fontSize: 12 }}
                    onClick={() => setPrompt(ex)}>
                    {ex}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* RIGHT — Output */}
          <div className="flex flex-col gap-3">
            <label>Output</label>
            <div className="card" style={{ flex: 1, minHeight: 300, overflow: "auto" }}>
              {output
                ? <ReactMarkdown>{output}</ReactMarkdown>
                : <span style={{ color: "var(--muted)" }}>Output will appear here…</span>
              }
              {loading && !output && (
                <span style={{ color: "var(--muted)" }}>⏳ Generating…</span>
              )}
            </div>
            {stats && (
              <div className="card flex gap-4" style={{ flexWrap: "wrap" }}>
                {[
                  ["🕐 Time",       `${stats.duration}s`],
                  ["📝 Tokens",     stats.tokens],
                  ["⚡ Tokens/sec", stats.tokensPerSec],
                  ["📥 Prompt Tokens", stats.promptTokens],
                ].map(([k, v]) => (
                  <div key={k}>
                    <div style={{ fontSize: 11, color: "var(--muted)" }}>{k}</div>
                    <div style={{ fontWeight: 700, color: "var(--accent)" }}>{v}</div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}