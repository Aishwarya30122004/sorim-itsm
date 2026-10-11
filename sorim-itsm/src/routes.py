"""All API routes."""
from fastapi import APIRouter, UploadFile, File
from pydantic import BaseModel

from src import services
from src.ai import ingest
from src.database import tickets, audit_logs, provisioning

router = APIRouter()


class TicketInput(BaseModel):
    user_input: str
    user_id: str = "emp_001"

class ChatInput(BaseModel):
    message: str
    user_id: str = "emp_001"

class Query(BaseModel):
    query: str

class SoftwareInput(BaseModel):
    request: str
    user_id: str = "emp_001"


@router.post("/api/tickets/analyze", tags=["UC1"])
def analyze_ticket(req: TicketInput):
    return services.analyze_ticket(req.user_input, req.user_id)

@router.get("/api/tickets/", tags=["UC1"])
def list_tickets():
    return list(tickets.find({}, {"_id": 0}))


@router.get("/api/audit/", tags=["UC2"])
def list_audit_logs():
    return list(audit_logs.find({}, {"_id": 0}).sort("timestamp", -1).limit(50))


@router.post("/api/knowledge/seed", tags=["UC3"])
def seed_kb():
    return {"chunks_ingested": services.seed_knowledge_base()}

@router.post("/api/knowledge/ask", tags=["UC3"])
def ask_kb(q: Query):
    return services.ask_knowledge_base(q.query)

@router.post("/api/knowledge/upload", tags=["UC3"])
async def upload_kb(file: UploadFile = File(...)):
    content = (await file.read()).decode("utf-8")
    return {"chunks": ingest(content, source=file.filename)}


@router.post("/api/chat/", tags=["UC4"])
def chat(req: ChatInput):
    return services.handle_chat(req.message, req.user_id)


@router.post("/api/provisioning/request", tags=["UC5"])
def request_software(req: SoftwareInput):
    return services.request_software(req.request, req.user_id)

@router.get("/api/provisioning/", tags=["UC5"])
def list_provisioning():
    return list(provisioning.find({}, {"_id": 0}))