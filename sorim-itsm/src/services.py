"""All 5 use case implementations."""
import random
from datetime import datetime, timezone
from pathlib import Path

from src.ai import llm, answer_with_rag, ingest, _chroma_collection
from src.config import settings
from src.prompts import TICKET_PROMPT, SOFTWARE_PROMPT
from src.database import tickets, audit_logs, provisioning


def _now():
    """UTC now — replaces deprecated datetime.utcnow()."""
    return datetime.now(timezone.utc)


# =========================================================
# UC1: Intelligent Ticket Intake
# =========================================================
def analyze_ticket(user_input: str, user_id: str = "emp_001") -> dict:
    analysis = llm.chat_json(TICKET_PROMPT.format(issue=user_input))
    sn_id = f"INC{random.randint(1000000, 9999999)}"
    ticket_doc = {
        "servicenow_id": sn_id,
        "user_id": user_id,
        "raw_input": user_input,
        **analysis,
        "status": "New",
        "created_at": _now(),
    }
    tickets.insert_one(ticket_doc.copy())
    return ticket_doc


# =========================================================
# UC2: Auto Resolution / Self-Heal
# =========================================================
MOCK_ACTIONS = {
    "reset_password":   "Password reset via AD API — new password emailed",
    "unlock_account":   "Account unlocked — MFA required on next login",
    "vpn_troubleshoot": "VPN profile refreshed — user prompted to reconnect",
    "clear_cache":      "Application cache cleared successfully",
    "service_restart":  "Service restarted via remote management API",
    "app_restart":      "Application restarted on user's device",
}


def self_heal(analysis: dict, ticket_id: str) -> dict:
    action = analysis.get("auto_action")
    if not analysis.get("auto_resolvable") or action not in MOCK_ACTIONS:
        return {"executed": False, "reason": "Not auto-resolvable"}

    result = {
        "action": action,
        "result": MOCK_ACTIONS[action],
        "ticket_id": ticket_id,
        "status": "success",
        "timestamp": _now(),
    }
    audit_logs.insert_one(result.copy())
    tickets.update_one(
        {"servicenow_id": ticket_id},
        {"$set": {"status": "Auto-Resolved", "resolved_at": _now()}},
    )
    return {"executed": True, **result}


# =========================================================
# UC3: Knowledge Management (PDF → ChromaDB → RAG)
# =========================================================
def _read_pdf(file_path: Path) -> str:
    """Extract text from PDF using pypdf."""
    from pypdf import PdfReader
    reader = PdfReader(str(file_path))
    return "\n".join((p.extract_text() or "") for p in reader.pages).strip()


def seed_knowledge_base() -> dict:
    """
    Load PDF → chunk → embed → store in ChromaDB.
    This CREATES the vector DB.
    """
    pdf_path = settings.KB_PDF

    if not pdf_path.exists():
        return {
            "error": f"PDF not found at {pdf_path}",
            "hint": "Place your PDF at: src/data/knowledge_base.pdf",
        }

    print(f"📄 Reading PDF: {pdf_path}")
    text = _read_pdf(pdf_path)

    if not text.strip():
        return {"error": "PDF has no extractable text (scanned image?)"}

    print(f"📄 Extracted {len(text)} characters")

    # Wipe previous collection contents (idempotent re-seed)
    try:
        existing = _chroma_collection.get()
        ids = existing.get("ids", [])
        if ids:
            _chroma_collection.delete(ids=ids)
            print(f"🧹 Cleared {len(ids)} old chunks from ChromaDB")
    except Exception as e:
        print(f"⚠️  Clear step skipped: {e}")

    chunks = ingest(text, source=pdf_path.name)
    print(f"✅ Ingested {chunks} chunks into ChromaDB")

    return {
        "documents_loaded": 1,
        "total_chunks": chunks,
        "source": pdf_path.name,
        "characters": len(text),
        "vector_db": "chromadb",
        "collection": settings.CHROMA_COLLECTION,
    }


def ask_knowledge_base(question: str) -> dict:
    return answer_with_rag(question)


# =========================================================
# UC4: Self-Service Chatbot
# =========================================================
def handle_chat(message: str, user_id: str = "emp_001") -> dict:
    ticket = analyze_ticket(message, user_id)
    heal = self_heal(ticket, ticket["servicenow_id"])

    if heal["executed"]:
        status = "AUTO_RESOLVED"
        reply = f"✅ {heal['result']}\n\nTicket {ticket['servicenow_id']} auto-resolved."
    else:
        rag = answer_with_rag(message)
        if rag["sources"] and rag["sources"][0]["score"] > settings.MIN_SIMILARITY:
            status = "ANSWERED_FROM_KB"
            reply = rag["answer"]
        else:
            status = "ESCALATED"
            reply = f"🎫 Created ticket {ticket['servicenow_id']}. IT will respond shortly."

    return {
        "message": reply,
        "status": status,
        "ticket": ticket,
        "auto_resolution": heal,
    }


# =========================================================
# UC5: Software Provisioning
# =========================================================
SOFTWARE_CATALOG = {
    "vscode": {"licensed": False, "auto_approve": True,  "risk": "Low"},
    "slack":  {"licensed": True,  "auto_approve": True,  "risk": "Low"},
    "adobe":  {"licensed": True,  "auto_approve": False, "risk": "Medium"},
    "docker": {"licensed": False, "auto_approve": True,  "risk": "Medium"},
}


def request_software(request: str, user_id: str = "emp_001") -> dict:
    parsed = llm.chat_json(SOFTWARE_PROMPT.format(request=request), max_tokens=200)
    sw = parsed["software_name"].lower()
    info = SOFTWARE_CATALOG.get(sw, {"licensed": True, "auto_approve": False, "risk": "High"})
    status = "AUTO_APPROVED" if info["auto_approve"] else "PENDING_APPROVAL"
    next_step = "Installing via Software Center..." if info["auto_approve"] else "Awaiting manager approval"

    doc = {
        "user_id": user_id,
        "request": request,
        "software_name": parsed["software_name"],
        "justification": parsed["justification"],
        "licensed": info["licensed"],
        "risk": info["risk"],
        "status": status,
        "next_step": next_step,
        "timestamp": _now(),
    }
    provisioning.insert_one(doc.copy())
    return doc





##📄 Document  →  ✂️ Chunking  →  🔢 Vectorization  →  💾 Vector Store  →  🔍 Semantic Search  →  🤖 LLM