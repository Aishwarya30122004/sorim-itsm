"""MongoDB for tickets/audit/provisioning. ChromaDB handled in ai.py."""
from pymongo import MongoClient, ASCENDING, DESCENDING
from src.config import settings

client = MongoClient(settings.MONGO_URI)
db = client[settings.DB_NAME]

tickets = db["tickets"]
audit_logs = db["audit_logs"]
conversations = db["conversations"]
provisioning = db["provisioning"]


def ensure_indexes():
    """Create indexes once at startup. Idempotent."""
    try:
        tickets.create_index([("servicenow_id", ASCENDING)], unique=True)
        tickets.create_index([("user_id", ASCENDING)])
        tickets.create_index([("created_at", DESCENDING)])

        audit_logs.create_index([("timestamp", DESCENDING)])
        audit_logs.create_index([("ticket_id", ASCENDING)])

        provisioning.create_index([("user_id", ASCENDING)])
        provisioning.create_index([("timestamp", DESCENDING)])

        print("✅ MongoDB indexes ensured")
    except Exception as e:
        print(f"⚠️  Index creation skipped: {e}")


ensure_indexes()