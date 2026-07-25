import { NavLink } from "react-router-dom";
import {
  MessageSquare, Zap, Hash, Package, Info
} from "lucide-react";

const NAV = [
  { to: "/chat",       icon: MessageSquare, label: "Chat",        desc: "/api/chat"       },
  { to: "/generate",   icon: Zap,           label: "Generate",    desc: "/api/generate"   },
  { to: "/embeddings", icon: Hash,          label: "Embeddings",  desc: "/api/embed"      },
  { to: "/models",     icon: Package,       label: "Models",      desc: "/api/tags"       },
  { to: "/model-info", icon: Info,          label: "Model Info",  desc: "/api/show"       },
];

export default function Sidebar({ ollamaOk }) {
  return (
    <aside style={{
      width: "var(--sidebar)", minWidth: "var(--sidebar)",
      background: "var(--surface)", borderRight: "1px solid var(--border)",
      display: "flex", flexDirection: "column", padding: "0",
    }}>
      {/* Logo */}
      <div style={{ padding: "20px 16px 16px", borderBottom: "1px solid var(--border)" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <div style={{
            width: 36, height: 36, borderRadius: 10,
            background: "linear-gradient(135deg, var(--primary), var(--accent))",
            display: "flex", alignItems: "center", justifyContent: "center",
            fontSize: 18,
          }}>🦙</div>
          <div>
            <div style={{ fontWeight: 700, fontSize: 15 }}>Ollama UI</div>
            <div style={{ fontSize: 11, color: "var(--muted)" }}>Local LLM Explorer</div>
          </div>
        </div>
        {/* Ollama status */}
        <div style={{ display: "flex", alignItems: "center", gap: 6, marginTop: 12 }}>
          <span className={`dot ${ollamaOk === null ? "dot-yellow" : ollamaOk ? "dot-green" : "dot-red"}`} />
          <span style={{ fontSize: 11, color: "var(--muted)" }}>
            {ollamaOk === null ? "Checking…" : ollamaOk ? "Ollama running" : "Ollama offline"}
          </span>
        </div>
      </div>

      {/* Nav */}
      <nav style={{ flex: 1, padding: "12px 8px" }}>
        {NAV.map(({ to, icon: Icon, label, desc }) => (
          <NavLink key={to} to={to} style={({ isActive }) => ({
            display: "flex", alignItems: "center", gap: 12,
            padding: "10px 12px", borderRadius: "var(--radius)",
            textDecoration: "none", marginBottom: 2,
            background: isActive ? "rgba(108,99,255,0.15)" : "transparent",
            color: isActive ? "var(--primary)" : "var(--text)",
            borderLeft: isActive ? "3px solid var(--primary)" : "3px solid transparent",
            transition: "all 0.15s",
          })}>
            <Icon size={16} />
            <div>
              <div style={{ fontSize: 13, fontWeight: 600 }}>{label}</div>
              <div style={{ fontSize: 10, color: "var(--muted)", fontFamily: "monospace" }}>{desc}</div>
            </div>
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div style={{ padding: "12px 16px", borderTop: "1px solid var(--border)", fontSize: 11, color: "var(--muted)" }}>
        localhost:11434
      </div>
    </aside>
  );
}