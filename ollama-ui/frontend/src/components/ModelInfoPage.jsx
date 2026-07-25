import { useState, useEffect } from "react";

export default function ModelInfoPage({ models }) {
  const [model, setModel]   = useState("");
  const [info, setInfo]     = useState(null);
  const [loading, setLoading] = useState(false);

  const getModelInfo = (payload) => payload?.modelinfo ?? payload?.model_info ?? null;

  const extractNumCtxFromText = (text) => {
    if (!text) return null;
    const match = String(text).match(/\bnum_ctx\b\s*(?:=|:)?\s*(\d+)/i);
    return match ? Number(match[1]) : null;
  };

  const getContextSize = (payload) => {
    if (!payload) return null;
    const modelInfo = getModelInfo(payload);
    const architecture = modelInfo?.["general.architecture"];
    const architectureContextKey = architecture ? `${architecture}.context_length` : null;

    return (
      payload.details?.context_length ??
      payload.details?.num_ctx ??
      (architectureContextKey ? modelInfo?.[architectureContextKey] : null) ??
      modelInfo?.["general.context_length"] ??
      modelInfo?.["llama.context_length"] ??
      modelInfo?.context_length ??
      extractNumCtxFromText(payload.parameters) ??
      extractNumCtxFromText(payload.modelfile) ??
      null
    );
  };

  const formatContextSize = (value) => {
    if (value === null || value === undefined || value === "") return "";
    const numeric = Number(value);
    if (Number.isFinite(numeric)) return `${numeric.toLocaleString()} tokens`;
    return String(value);
  };

  useEffect(() => { if (models.length) setModel(models[0].name); }, [models]);

  const fetchInfo = async () => {
    if (!model) return;
    setLoading(true); setInfo(null);
    const res = await fetch("/api/model/info", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: model }),
    });
    setInfo(await res.json());
    setLoading(false);
  };

  const Section = ({ title, children }) => (
    <div className="card flex flex-col gap-3">
      <strong style={{ color: "var(--accent)" }}>{title}</strong>
      {children}
    </div>
  );

  const KV = ({ k, v }) => v ? (
    <div className="flex justify-between" style={{ fontSize: 13, borderBottom: "1px solid var(--border)", paddingBottom: 6 }}>
      <span style={{ color: "var(--muted)" }}>{k}</span>
      <span style={{ fontWeight: 500, maxWidth: "65%", textAlign: "right", wordBreak: "break-all" }}>{v}</span>
    </div>
  ) : null;

  return (
    <div className="page">
      <div className="page-header">
        <h1>ℹ️ Model Info</h1>
        <p>Detailed model metadata via <code>/api/show</code></p>
      </div>
      <div className="page-body flex flex-col gap-4">
        <div className="flex gap-2">
          <select className="select" value={model} onChange={e => setModel(e.target.value)}>
            {models.map(m => <option key={m.name} value={m.name}>{m.name}</option>)}
          </select>
          <button className="btn btn-primary" onClick={fetchInfo} disabled={loading || !model}>
            {loading ? "Loading…" : "Fetch Info"}
          </button>
        </div>

        {info && (
          <div className="flex flex-col gap-4">
            {info.details && (
              <Section title="📋 Model Details">
                <KV k="Family"          v={info.details.family} />
                <KV k="Parameter Size"  v={info.details.parameter_size} />
                <KV k="Context Size"    v={formatContextSize(getContextSize(info))} />
                <KV k="Quantization"    v={info.details.quantization_level} />
                <KV k="Format"          v={info.details.format} />
                <KV k="Families"        v={info.details.families?.join(", ")} />
              </Section>
            )}
            {getModelInfo(info) && (
              <Section title="🧠 Model Architecture">
                {Object.entries(getModelInfo(info)).slice(0, 15).map(([k, v]) => (
                  <KV key={k} k={k} v={String(v)} />
                ))}
              </Section>
            )}
            {info.modelfile && (
              <Section title="📄 Modelfile">
                <pre style={{
                  background: "var(--bg)", padding: 12, borderRadius: 8,
                  fontSize: 12, overflow: "auto", maxHeight: 300,
                  color: "var(--accent)", lineHeight: 1.6,
                }}>
                  {info.modelfile}
                </pre>
              </Section>
            )}
            {info.template && (
              <Section title="📝 Prompt Template">
                <pre style={{
                  background: "var(--bg)", padding: 12, borderRadius: 8,
                  fontSize: 12, overflow: "auto", color: "var(--text)", lineHeight: 1.6,
                }}>
                  {info.template}
                </pre>
              </Section>
            )}
          </div>
        )}
      </div>
    </div>
  );
}