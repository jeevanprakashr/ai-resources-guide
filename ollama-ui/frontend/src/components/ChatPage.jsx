import { useState, useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import { Send, Trash2, Settings } from "lucide-react";

export default function ChatPage({ models }) {
  const [messages, setMessages]     = useState([]);
  const [input, setInput]           = useState("");
  const [model, setModel]           = useState("");
  const [loading, setLoading]       = useState(false);
  const [stream, setStream]         = useState(true);
  const [temperature, setTemperature] = useState(0.7);
  const [showSettings, setShowSettings] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => { if (models.length) setModel(models[0].name); }, [models]);
  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages]);

  const send = async () => {
    if (!input.trim() || !model || loading) return;
    const userMsg = { role: "user", content: input.trim() };
    const history = [...messages, userMsg];
    setMessages(history);
    setInput("");
    setLoading(true);

    if (stream) {
      // Streaming mode
      const assistantMsg = { role: "assistant", content: "" };
      setMessages([...history, assistantMsg]);

      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ model, messages: history, stream: true, temperature }),
      });

      const reader = res.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const text = decoder.decode(value);
        const lines = text.split("\n").filter(l => l.startsWith("data: "));
        for (const line of lines) {
          try {
            const data = JSON.parse(line.slice(6));
            if (data.message?.content) {
              setMessages(prev => {
                const updated = [...prev];
                updated[updated.length - 1] = {
                  ...updated[updated.length - 1],
                  content: updated[updated.length - 1].content + data.message.content,
                };
                return updated;
              });
            }
          } catch {}
        }
      }
    } else {
      // Non-streaming
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ model, messages: history, stream: false, temperature }),
      });
      const data = await res.json();
      setMessages([...history, { role: "assistant", content: data.message?.content || "No response" }]);
    }
    setLoading(false);
  };

  return (
    <div className="page">
      {/* Header */}
      <div className="page-header flex items-center justify-between">
        <div>
          <h1>💬 Chat</h1>
          <p>Multi-turn conversation via <code>/api/chat</code></p>
        </div>
        <div className="flex items-center gap-2">
          <select className="select" style={{ width: 180 }} value={model} onChange={e => setModel(e.target.value)}>
            {models.map(m => <option key={m.name} value={m.name}>{m.name}</option>)}
          </select>
          <button className="btn btn-ghost" onClick={() => setShowSettings(!showSettings)} title="Settings">
            <Settings size={15} />
          </button>
          <button className="btn btn-ghost" onClick={() => setMessages([])} title="Clear">
            <Trash2 size={15} />
          </button>
        </div>
      </div>

      {/* Settings Bar */}
      {showSettings && (
        <div className="flex items-center gap-4" style={{ padding: "10px 24px", background: "var(--surface)", borderBottom: "1px solid var(--border)" }}>
          <div className="flex items-center gap-2">
            <label style={{ margin: 0 }}>Temperature: {temperature}</label>
            <input type="range" min="0" max="2" step="0.1" value={temperature}
              onChange={e => setTemperature(Number(e.target.value))}
              style={{ width: 100 }} />
          </div>
          <div className="flex items-center gap-2">
            <label style={{ margin: 0 }}>Streaming</label>
            <input type="checkbox" checked={stream} onChange={e => setStream(e.target.checked)} />
          </div>
        </div>
      )}

      {/* Messages */}
      <div className="chat-wrap">
        {messages.length === 0 && (
          <div style={{ textAlign: "center", color: "var(--muted)", marginTop: 60 }}>
            <div style={{ fontSize: 40 }}>🦙</div>
            <div style={{ marginTop: 12 }}>Start a conversation with your local model</div>
          </div>
        )}
        {messages.map((msg, i) => (
          <div key={i} className={`bubble ${msg.role}`}>
            <div className="bubble-avatar">{msg.role === "user" ? "👤" : "🤖"}</div>
            <div className="bubble-content">
              <ReactMarkdown>{msg.content || "…"}</ReactMarkdown>
            </div>
          </div>
        ))}
        {loading && messages[messages.length - 1]?.role !== "assistant" && (
          <div className="bubble assistant">
            <div className="bubble-avatar">🤖</div>
            <div className="bubble-content" style={{ color: "var(--muted)" }}>Thinking…</div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div style={{ padding: "16px 24px", borderTop: "1px solid var(--border)", display: "flex", gap: 10 }}>
        <textarea
          className="textarea"
          style={{ minHeight: 44, maxHeight: 140, resize: "none" }}
          placeholder="Type a message… (Shift+Enter for newline)"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => {
            if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); }
          }}
        />
        <button className="btn btn-primary" onClick={send} disabled={loading || !model}>
          <Send size={15} />
        </button>
      </div>
    </div>
  );
}