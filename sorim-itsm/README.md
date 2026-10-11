# 🚀 Sorim.ai — AI-Powered ITSM & Intelligent Helpdesk Automation

An enterprise-style ITSM prototype that classifies tickets, auto-resolves common issues, answers questions via RAG, and integrates with ServiceNow.

---

## 🎯 The 5 AI Capabilities

| # | Use Case | Implementation |
|---|----------|----------------|
| 1 | **Intelligent Ticket Intake** | AI extracts intent, category, sub-category, priority, impact, urgency, assignment group, summary, resolution |
| 2 | **Auto Resolution / Self-Heal Agents** | Whitelisted actions: password reset, account unlock, VPN troubleshoot, cache clear, service restart, app restart |
| 3 | **Knowledge Management Automation** | 7 KB docs → Chunking → Embedding → Vector DB → Semantic Search → LLM → Grounded answer with sources |
| 4 | **Self-Service Chatbot** | Combines UC1+UC2+UC3 in one pipeline |
| 5 | **Software Provisioning Automation** | AI parses request → catalog lookup → approval decision |

---

## 🏗️ Architecture

```
┌──────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   React.js   │────▶│    FastAPI      │────▶│  Hugging Face   │
│   Frontend   │◀────│    Backend      │◀────│  Llama 3 8B     │
└──────────────┘     └────────┬────────┘     └─────────────────┘
                              │
                     ┌────────┴────────┐
                     │                 │
              ┌──────▼──────┐   ┌──────▼──────┐
              │  MongoDB    │   │ ServiceNow  │
              │  Atlas      │   │   (Mock)    │
              │  (Tickets + │   │             │
              │   Vectors + │   │             │
              │   Audit)    │   │             │
              └─────────────┘   └─────────────┘
```

---

## 🧩 Tech Stack

| Layer            | Technology                          |
|------------------|-------------------------------------|
| Frontend         | React.js + Vite                     |
| Backend          | Python 3.11 + FastAPI               |
| Database         | MongoDB Atlas (Vector + Tickets)    |
| LLM              | Meta Llama 3 8B (Hugging Face)      |
| Embeddings       | `all-MiniLM-L6-v2` (local)          |
| ITSM Integration | ServiceNow REST API (mocked)        |
| RAG              | Cosine similarity over MongoDB      |

---

## 📂 Project Layout

```
sorim-itsm/
├── README.md
├── requirements.txt
├── .env                    ← Your secrets (not committed)
├── src/                    ← Backend (8 files, one job each)
│   ├── config.py           ← 🔑 All credentials
│   ├── database.py         ← MongoDB collections
│   ├── prompts.py          ← AI prompt templates
│   ├── ai.py               ← LLM + RAG + Embeddings
│   ├── services.py         ← All 5 use cases
│   ├── routes.py           ← All API endpoints
│   └── main.py             ← FastAPI app
└── frontend/               ← React app
    └── src/
        ├── App.jsx         ← All UI components
        └── api.js          ← Axios client
```

---

## ⚙️ Setup

### 1. Backend

```bash
# Clone
git clone <your-repo-url>
cd sorim-itsm

# Virtual env
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

# Install
pip install -r requirements.txt

# Configure
cp .env.example .env
# Add MONGO_URI and HF_TOKEN

# Run
uvicorn src.main:app --reload --port 8000
```

**API docs:** http://localhost:8000/docs

### 2. Seed Knowledge Base (once)

```bash
curl -X POST http://localhost:8000/api/knowledge/seed
```

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

---

## 🧪 Test Commands

```bash
# UC1 — Ticket Intake
curl -X POST http://localhost:8000/api/tickets/analyze \
  -H "Content-Type: application/json" \
  -d '{"user_input": "I cannot connect to VPN since this morning. Authentication keeps failing."}'

# UC2 — Auto-Heal
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "My password has expired"}'

# UC3 — RAG
curl -X POST http://localhost:8000/api/knowledge/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "How do I fix Outlook cache issues?"}'

# UC5 — Software
curl -X POST http://localhost:8000/api/provisioning/request \
  -H "Content-Type: application/json" \
  -d '{"request": "I need Adobe Photoshop for design work"}'
```

---

## 🎯 Use Case Demos

### UC1 — Intelligent Ticket Intake

**Input:** `"I cannot connect to VPN since this morning. Authentication keeps failing."`

**Output:**
```json
{
  "servicenow_id": "INC4821039",
  "intent": "Incident",
  "category": "Network",
  "sub_category": "VPN",
  "priority": "P2",
  "impact": "Individual",
  "urgency": "High",
  "assignment_group": "Network Support",
  "summary": "VPN authentication failure",
  "suggested_resolution": "VPN troubleshooting",
  "auto_resolvable": true,
  "auto_action": "vpn_troubleshoot"
}
```

### UC2 — Auto Resolution / Self-Heal Agents

**Pipeline:** Identify → Diagnose → Knowledge Search → Determine Automation → Execute → Validate → Update ServiceNow → Audit Log

**Example:** `"My password has expired."`

**Whitelisted actions:**
| Action | Description |
|--------|-------------|
| `reset_password` | Password reset via AD API |
| `unlock_account` | Unlock AD account (MFA next login) |
| `vpn_troubleshoot` | Refresh VPN profile |
| `clear_cache` | Clear application cache |
| `service_restart` | Restart backend service |
| `app_restart` | Restart user's application |

**Safety:** Any action not in whitelist is escalated to a human agent.

### UC3 — Knowledge Management (RAG)

**Pipeline:** Document → Chunking → Embedding → Vector DB → Semantic Search → LLM → Grounded Response

**7 KB docs:** VPN, Password Reset, Outlook, Wi-Fi, Laptop Performance, Software Installation, Application Access.

**Input:** `"How do I fix Outlook cache?"` → Grounded answer + sources displayed.

### UC4 — Self-Service Chatbot

Combines UC1 + UC2 + UC3 in one pipeline. Status: `AUTO_RESOLVED` | `ANSWERED_FROM_KB` | `ESCALATED`.

### UC5 — Software Provisioning

**Input:** `"I need Adobe Photoshop for design work"`

**Output:**
```json
{
  "software_name": "Adobe Photoshop",
  "requires_approval": true,
  "risk": "Medium",
  "status": "PENDING_APPROVAL",
  "next_step": "Awaiting manager approval"
}
```

---

## 🧠 Technical Decisions

- **RAG over fine-tuning** — Zero training cost, fresh data, grounded answers, no hallucinations.
- **Llama 3 8B on Hugging Face** — Free tier, strong JSON output, OpenAI-compatible API.
- **MongoDB Atlas for everything** — Unified store for tickets + vectors + audit logs.
- **Mocked ServiceNow** — Demonstrates integration pattern without enterprise credentials.
- **One job per file** — 8 backend files, easy to review and explain.

---

## 🎤 3-Minute Demo Script

> *"Sorim.ai is an AI layer on top of ServiceNow. Let me show you the 5 use cases."*

1. **UC1** — Type: *"Cannot connect to VPN, authentication failing."* → AI returns `Network/VPN`, `P2`, `Network Support`, ServiceNow ID.
2. **UC2** — Type: *"My password expired."* → Auto-resolved, audit log records action.
3. **UC3** — Ask: *"How do I fix Outlook?"* → Grounded answer with sources.
4. **UC4** — Open Chat tab → UC1+UC2+UC3 combined in one conversation.
5. **UC5** — Request: *"I need Photoshop."* → `PENDING_APPROVAL` with reasoning.

---

Built for **Sorim.ai Technical Hackathon** — October 2026.



#####

sorim-itsm/
│
├── README.md
├── requirements.txt
├── .env
├── .gitignore
│
├── src/
│   ├── __init__.py
│   ├── config.py
│   ├── database.py
│   ├── prompts.py
│   ├── ai.py
│   ├── services.py
│   ├── routes.py
│   ├── main.py
│   │
│   └── data/                       ← 🆕 INSIDE src/
│       └── knowledge_base.pdf      ← 📄 YOUR PDF HERE
│
└── frontend/
    └── src/
        ├── App.jsx
        └── api.js