"""Centralized configuration - MongoDB (tickets) + ChromaDB (vectors) + Groq/Mock."""
import os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")


class Settings:
    # ---- MongoDB (tickets, audit, provisioning) ----
    MONGO_URI = os.getenv("MONGO_URI", "")
    DB_NAME = os.getenv("DB_NAME", "sorim_itsm")

    # ---- ChromaDB (vector store for knowledge base) ----
    CHROMA_DIR = os.getenv("CHROMA_DIR", str(SRC_DIR / "chroma_db"))
    CHROMA_COLLECTION = os.getenv("CHROMA_COLLECTION", "knowledge_base")

    # ---- LLM backends ----
    # LLM_BACKEND: "auto" | "groq" | "mock"
    LLM_BACKEND = os.getenv("LLM_BACKEND", "auto")

    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

    # ---- Embeddings ----
    # EMBEDDING_BACKEND: "neural" | "tfidf" | "auto"
    EMBEDDING_BACKEND = os.getenv("EMBEDDING_BACKEND", "auto")
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

    # ---- RAG ----
    TOP_K_RAG = int(os.getenv("TOP_K_RAG", "3"))
    CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "400"))
    MIN_SIMILARITY = float(os.getenv("MIN_SIMILARITY", "0.5"))

    # ---- CORS ----
    _raw_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").strip()
    ALLOWED_ORIGINS = [o.strip() for o in _raw_origins.split(",") if o.strip()]
    ALLOW_CREDENTIALS = ALLOWED_ORIGINS != ["*"]
    ALLOW_METHODS = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    ALLOW_HEADERS = ["*"]

    # ---- Paths ----
    DATA_DIR = SRC_DIR / "data"
    KB_PDF = DATA_DIR / "ITSM_Helpdesk_Knowledge_Base.pdf"

    ENV = os.getenv("ENV", "development").lower()
    IS_PRODUCTION = ENV == "production"

    def validate(self):
        if not self.MONGO_URI:
            raise RuntimeError(f"❌ MONGO_URI missing. Check {ROOT / '.env'}")

        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
        Path(self.CHROMA_DIR).mkdir(parents=True, exist_ok=True)

        if not self.KB_PDF.exists():
            print(f"⚠️  KB PDF not found at {self.KB_PDF}")
            print(f"   → Place your PDF at: src/data/knowledge_base.pdf")

        if not self.GROQ_API_KEY:
            print("⚠️  GROQ_API_KEY missing → will run on Mock LLM only")

        if self.IS_PRODUCTION and "*" in self.ALLOWED_ORIGINS:
            print("⚠️  CORS allows '*' — set ALLOWED_ORIGINS to your real domains in production")
        return True


settings = Settings()