

import { useState, useEffect } from "react";
import api from "./api";

const TABS = ["Chat", "Tickets", "Audit", "Knowledge", "Software"];

export default function App() {
  const [tab, setTab] = useState("Chat");

  return (
    <div style={S.app}>
      <header style={S.header}>
        <h1 style={S.title}>SORIM.ai</h1>
        <p style={S.subtitle}>AI-Powered ITSM Platform</p>
      </header>

      <nav style={S.nav}>
        {TABS.map((t) => (
          <button key={t} onClick={() => setTab(t)} style={S.tab(tab === t)}>
            {t}
          </button>
        ))}
      </nav>

      <main style={S.panel}>
        {tab === "Chat" && <Chat />}
        {tab === "Tickets" && <Tickets />}
        {tab === "Audit" && <Audit />}
        {tab === "Knowledge" && <Knowledge />}
        {tab === "Software" && <Software />}
      </main>
    </div>
  );
}

/* ---------------- UC4: Chat ---------------- */
function Chat() {
  const [msgs, setMsgs] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const send = async () => {
    if (!input.trim() || loading) return;
    setMsgs((p) => [...p, { role: "user", text: input }]);
    setInput("");
    setLoading(true);
    try {
      const { data } = await api.post("/api/chat/", { message: input });
      setMsgs((p) => [...p, { role: "ai", text: data.message, meta: data }]);
    } catch (e) {
      setMsgs((p) => [...p, { role: "ai", text: "Error: " + e.message }]);
    }
    setLoading(false);
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", height: 500 }}>
      <div style={{ flex: 1, overflowY: "auto" }}>
        {msgs.map((m, i) => (
          <div
            key={i}
            style={{
              textAlign: m.role === "user" ? "right" : "left",
              margin: 10,
            }}
          >
            <div style={S.bubble(m.role === "user")}>
              {m.text}
              {m.meta?.ticket && (
                <div style={S.metaBox}>
                  <b>{m.meta.ticket.servicenow_id}</b> •{" "}
                  {m.meta.ticket.category}
                  {m.meta.ticket.sub_category && ` / ${m.meta.ticket.sub_category}`} •{" "}
                  {m.meta.ticket.priority} • <b>{m.meta.status}</b>
                </div>
              )}
            </div>
          </div>
        ))}
        {loading && <p style={{ color: "#888" }}>🤖 Thinking…</p>}
      </div>
      <div style={{ display: "flex", gap: 8 }}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && send()}
          placeholder="e.g., I cannot connect to VPN since this morning..."
          style={S.input}
        />
        <button onClick={send} style={S.btn}>
          Send
        </button>
      </div>
    </div>
  );
}

/* ---------------- UC1: Tickets ---------------- */
function Tickets() {
  const [rows, setRows] = useState([]);

  const load = () => {
    api.get("/api/tickets/").then((r) => setRows(r.data));
  };

  useEffect(() => {
    load();
  }, []);

  return (
    <div>
      <div style={{ marginBottom: 15 }}>
        <button onClick={load} style={S.btn}>
          🔄 Refresh
        </button>
      </div>
      <table style={S.table}>
        <thead style={S.thead}>
          <tr>
            <th style={S.th}>SN ID</th>
            <th style={S.th}>Summary</th>
            <th style={S.th}>Category</th>
            <th style={S.th}>Sub-Cat</th>
            <th style={S.th}>Priority</th>
            <th style={S.th}>Group</th>
            <th style={S.th}>Status</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((t, i) => (
            <tr key={i}>
              <td style={S.td}>{t.servicenow_id}</td>
              <td style={S.td}>{t.summary}</td>
              <td style={S.td}>{t.category}</td>
              <td style={S.td}>{t.sub_category}</td>
              <td style={S.td}>{t.priority}</td>
              <td style={S.td}>{t.assignment_group}</td>
              <td style={S.td}>{t.status}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/* ---------------- UC2: Audit ---------------- */
function Audit() {
  const [rows, setRows] = useState([]);

  useEffect(() => {
    api.get("/api/audit/").then((r) => setRows(r.data));
  }, []);

  return (
    <div>
      <p style={{ color: "#666" }}>
        🔒 Every automated self-heal action is logged for enterprise compliance.
      </p>
      <table style={S.table}>
        <thead style={S.theadDark}>
          <tr>
            <th style={S.th}>Action</th>
            <th style={S.th}>Result</th>
            <th style={S.th}>Ticket</th>
            <th style={S.th}>Time</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i}>
              <td style={S.td}>
                <b>{r.action}</b>
              </td>
              <td style={S.td}>{r.result}</td>
              <td style={S.td}>{r.ticket_id}</td>
              <td style={S.td}>{new Date(r.timestamp).toLocaleString()}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/* ---------------- UC3: Knowledge ---------------- */
function Knowledge() {
  const [q, setQ] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const ask = async () => {
    if (!q.trim() || loading) return;
    setLoading(true);
    try {
      const { data } = await api.post("/api/knowledge/ask", { query: q });
      setResult(data);
    } catch (e) {
      setResult({ answer: "Error: " + e.message, sources: [] });
    }
    setLoading(false);
  };

  return (
    <div>
      <div style={{ display: "flex", gap: 8 }}>
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="e.g., How do I fix Outlook cache issues?"
          style={S.input}
          onKeyDown={(e) => e.key === "Enter" && ask()}
        />
        <button onClick={ask} style={S.btn}>
          Ask
        </button>
      </div>

      {loading && <p style={{ color: "#888", marginTop: 20 }}>🔍 Searching knowledge base…</p>}

      {result && (
        <div style={S.result}>
          <h3>💡 Answer</h3>
          <p style={{ whiteSpace: "pre-wrap" }}>{result.answer}</p>
          <h4>📎 Sources Used</h4>
          <ul>
            {result.sources.map((s, i) => (
              <li key={i}>
                <b>{s.source}</b> (relevance: {s.score})
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

/* ---------------- UC5: Software ---------------- */
function Software() {
  const [req, setReq] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const submit = async () => {
    if (!req.trim() || loading) return;
    setLoading(true);
    try {
      const { data } = await api.post("/api/provisioning/request", { request: req });
      setResult(data);
    } catch (e) {
      setResult({ software_name: "Error", status: e.message });
    }
    setLoading(false);
  };

  return (
    <div>
      <div style={{ display: "flex", gap: 8 }}>
        <input
          value={req}
          onChange={(e) => setReq(e.target.value)}
          placeholder="e.g., I need Adobe Photoshop for design work"
          style={S.input}
          onKeyDown={(e) => e.key === "Enter" && submit()}
        />
        <button onClick={submit} style={S.btn}>
          Request
        </button>
      </div>

      {loading && <p style={{ color: "#888", marginTop: 20 }}>💾 Processing request…</p>}

      {result && (
        <div style={S.result}>
          <h3>
            {result.software_name} —{" "}
            <span
              style={{
                color:
                  result.status === "AUTO_APPROVED" ? "green" : "orange",
              }}
            >
              {result.status}
            </span>
          </h3>
          <p>
            <b>Risk:</b> {result.risk} | <b>Licensed:</b>{" "}
            {result.licensed ? "Yes" : "No"}
          </p>
          <p>
            <b>Next Step:</b> {result.next_step}
          </p>
          <p>
            <b>Justification:</b> {result.justification}
          </p>
        </div>
      )}
    </div>
  );
}

/* ---------------- Styles ---------------- */
const S = {
  app: {
    fontFamily: "system-ui, -apple-system, sans-serif",
    maxWidth: 1100,
    margin: "0 auto",
    padding: 20,
  },
  header: { textAlign: "center", marginBottom: 20 },
  title: { color: "#4B3FCA", fontSize: 36, margin: 0, letterSpacing: 2 },
  subtitle: { color: "#666", marginTop: 4 },
  nav: {
    display: "flex",
    gap: 8,
    marginBottom: 16,
    justifyContent: "center",
    flexWrap: "wrap",
  },
  tab: (a) => ({
    padding: "10px 18px",
    border: "none",
    borderRadius: 8,
    cursor: "pointer",
    background: a ? "#4B3FCA" : "#f0f0f5",
    color: a ? "white" : "#333",
    fontWeight: 500,
  }),
  panel: {
    border: "1px solid #eee",
    borderRadius: 12,
    padding: 20,
    minHeight: 500,
  },
  bubble: (user) => ({
    display: "inline-block",
    padding: "10px 14px",
    borderRadius: 10,
    maxWidth: "75%",
    textAlign: "left",
    whiteSpace: "pre-wrap",
    background: user ? "#4B3FCA" : "#f5f5f7",
    color: user ? "white" : "#333",
  }),
  metaBox: {
    marginTop: 10,
    padding: 10,
    background: "#fff",
    border: "1px solid #eee",
    borderRadius: 6,
    fontSize: 12,
    color: "#333",
  },
  input: {
    flex: 1,
    padding: 12,
    borderRadius: 8,
    border: "1px solid #ddd",
    fontSize: 14,
  },
  btn: {
    padding: "12px 22px",
    background: "#4B3FCA",
    color: "white",
    border: "none",
    borderRadius: 8,
    cursor: "pointer",
    fontWeight: 600,
  },
  table: { width: "100%", borderCollapse: "collapse" },
  thead: { background: "#4B3FCA", color: "white" },
  theadDark: { background: "#333", color: "white" },
  th: { padding: 12, textAlign: "left" },
  td: { padding: 12, borderBottom: "1px solid #eee", textAlign: "left" },
  result: {
    marginTop: 20,
    padding: 20,
    background: "#f9f9fc",
    borderRadius: 10,
    border: "1px solid #eee",
  },
};