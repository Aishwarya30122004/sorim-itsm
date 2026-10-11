"""
AI logic: Groq LLM with Mock fallback, ChromaDB vector store, RAG.

Vector DB = ChromaDB (persistent, local folder configured via CHROMA_DIR).
LLM fallback chain: Groq → Mock.
Embeddings: neural (sentence-transformers) with TF-IDF fallback.
"""

import json
import re
import math
from collections import Counter
import numpy as np

from src.config import settings


# =========================================================
# CHROMADB — vector store
# =========================================================
import chromadb
from chromadb.config import Settings as ChromaSettings

_chroma_client = chromadb.PersistentClient(
    path=settings.CHROMA_DIR,
    settings=ChromaSettings(anonymized_telemetry=False),
)
_chroma_collection = _chroma_client.get_or_create_collection(
    name=settings.CHROMA_COLLECTION,
    metadata={"hnsw:space": "cosine"},   # cosine similarity
)


# =========================================================
# LLM BACKENDS
# =========================================================
class GroqLLM:
    """Groq cloud LLM — OpenAI-compatible, free tier, fast."""

    def __init__(self):
        from groq import Groq
        if not settings.GROQ_API_KEY:
            raise RuntimeError("GROQ_API_KEY is empty")
        self._client = Groq(api_key=settings.GROQ_API_KEY)
        self.model = settings.GROQ_MODEL

    def chat(self, prompt: str, max_tokens: int = 500) -> str:
        r = self._client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=0.3,
        )
        return r.choices[0].message.content

    def chat_json(self, prompt: str, max_tokens: int = 700) -> dict:
        raw = re.sub(r"```json|```", "", self.chat(prompt, max_tokens)).strip()
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if not m:
            raise ValueError(f"No JSON in LLM response: {raw}")
        return json.loads(m.group(0))


class MockLLM:
    """Offline keyword-based fallback — keeps the app alive if Groq fails."""

    def chat(self, prompt: str, max_tokens: int = 500) -> str:
        p = prompt.lower()
        if "vpn" in p: return "1. Restart VPN client.\n2. Verify internet.\n3. Reset password."
        if "outlook" in p: return "1. Restart Outlook.\n2. Clear cache.\n3. Re-add account."
        if "password" in p: return "1. Go to portal.company.com/reset\n2. Enter email.\n3. Follow link."
        if "wifi" in p or "wi-fi" in p: return "1. Forget network.\n2. Reconnect.\n3. Restart adapter."
        if "laptop" in p or "slow" in p: return "1. Check Task Manager.\n2. Close apps.\n3. Restart."
        return "Please contact IT support."

    def chat_json(self, prompt: str, max_tokens: int = 700) -> dict:
        p = prompt.lower()
        if "analyze" in p or "issue" in p or "ticket" in p:
            if "vpn" in p:
                return {"intent": "Incident", "category": "Network", "sub_category": "VPN",
                        "priority": "P2", "impact": "Individual", "urgency": "High",
                        "assignment_group": "Network Support",
                        "summary": "VPN authentication failure",
                        "suggested_resolution": "VPN troubleshooting",
                        "auto_resolvable": True, "auto_action": "vpn_troubleshoot"}
            if "password" in p:
                return {"intent": "Incident", "category": "Identity", "sub_category": "Password",
                        "priority": "P2", "impact": "Individual", "urgency": "High",
                        "assignment_group": "IAM Support",
                        "summary": "Password expired", "suggested_resolution": "Password reset",
                        "auto_resolvable": True, "auto_action": "reset_password"}
            if "outlook" in p or "email" in p or "cache" in p:
                return {"intent": "Incident", "category": "Application", "sub_category": "Email",
                        "priority": "P3", "impact": "Individual", "urgency": "Medium",
                        "assignment_group": "Application Support",
                        "summary": "Outlook cache issue", "suggested_resolution": "Clear cache",
                        "auto_resolvable": True, "auto_action": "clear_cache"}
            if "laptop" in p or "slow" in p:
                return {"intent": "Incident", "category": "Hardware", "sub_category": "Performance",
                        "priority": "P3", "impact": "Individual", "urgency": "Low",
                        "assignment_group": "Endpoint Support",
                        "summary": "Laptop performance", "suggested_resolution": "Restart",
                        "auto_resolvable": True, "auto_action": "app_restart"}
            return {"intent": "Incident", "category": "General", "sub_category": "Other",
                    "priority": "P3", "impact": "Individual", "urgency": "Medium",
                    "assignment_group": "Service Desk", "summary": "General inquiry",
                    "suggested_resolution": "Assign to agent",
                    "auto_resolvable": False, "auto_action": None}
        if "software" in p or "adobe" in p or "photoshop" in p:
            if "adobe" in p or "photoshop" in p:
                return {"software_name": "Adobe Photoshop", "justification": "Design work",
                        "requires_approval": True, "risk": "Medium"}
            if "vscode" in p or "vs code" in p:
                return {"software_name": "VS Code", "justification": "Development",
                        "requires_approval": False, "risk": "Low"}
            return {"software_name": "Unknown", "justification": "User request",
                    "requires_approval": True, "risk": "High"}
        return {"intent": "Incident", "category": "General", "sub_category": "Other",
                "priority": "P3", "impact": "Individual", "urgency": "Medium",
                "assignment_group": "Service Desk", "summary": "General inquiry",
                "suggested_resolution": "Assign to agent",
                "auto_resolvable": False, "auto_action": None}


class FallbackLLM:
    """Wraps a primary LLM. Retries next backend on failure."""

    def __init__(self, primary, fallbacks: list):
        self.primary = primary
        self.fallbacks = fallbacks
        self._active = primary
        self._active_name = type(primary).__name__

    def _chain(self):
        return [self.primary] + self.fallbacks

    def chat(self, prompt: str, max_tokens: int = 500) -> str:
        last_err = None
        for backend in self._chain():
            try:
                result = backend.chat(prompt, max_tokens)
                if self._active is not backend:
                    print(f"⚠️  LLM fell back to: {type(backend).__name__}")
                    self._active = backend
                    self._active_name = type(backend).__name__
                return result
            except Exception as e:
                last_err = e
                print(f"⚠️  {type(backend).__name__} chat failed: {e}")
        raise RuntimeError(f"All LLM backends failed. Last error: {last_err}")

    def chat_json(self, prompt: str, max_tokens: int = 700) -> dict:
        last_err = None
        for backend in self._chain():
            try:
                result = backend.chat_json(prompt, max_tokens)
                if self._active is not backend:
                    print(f"⚠️  LLM fell back to: {type(backend).__name__}")
                    self._active = backend
                    self._active_name = type(backend).__name__
                return result
            except Exception as e:
                last_err = e
                print(f"⚠️  {type(backend).__name__} chat_json failed: {e}")
        raise RuntimeError(f"All LLM backends failed. Last error: {last_err}")

    @property
    def active_name(self) -> str:
        return self._active_name


def _smoke_test(backend) -> bool:
    try:
        backend.chat("ping", max_tokens=5)
        return True
    except Exception as e:
        print(f"   smoke test failed for {type(backend).__name__}: {e}")
        return False


def _build_llm():
    preferred = (settings.LLM_BACKEND or "auto").lower()
    mock = MockLLM()

    if preferred == "mock":
        print("🤖 Using Mock LLM (offline keyword-based)")
        return mock

    if preferred == "groq":
        try:
            g = GroqLLM()
            if _smoke_test(g):
                print(f"✅ Groq LLM ready — {settings.GROQ_MODEL}")
                return FallbackLLM(g, [mock])
            print("⚠️  Groq failed smoke test → Mock only")
        except Exception as e:
            print(f"⚠️  Groq init failed: {e} → Mock only")
        return mock

    print("🔎 Auto-selecting LLM backend...")

    if settings.GROQ_API_KEY:
        try:
            g = GroqLLM()
            if _smoke_test(g):
                print(f"✅ Primary LLM: Groq ({settings.GROQ_MODEL})")
                print(f"✅ Fallback LLM: Mock (offline)")
                return FallbackLLM(g, [mock])
            print("⚠️  Groq smoke test failed")
        except Exception as e:
            print(f"⚠️  Groq unavailable: {e}")

    print("⚠️  No cloud LLM available → Mock LLM (offline keyword-based)")
    return mock


llm = _build_llm()


# =========================================================
# EMBEDDINGS
# =========================================================
class NeuralEmbedder:
    """Neural embeddings using sentence-transformers."""

    def __init__(self):
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer(settings.EMBEDDING_MODEL)
        print(f"✅ Neural embedder loaded: {settings.EMBEDDING_MODEL}")

    def embed(self, text: str) -> list:
        return self.model.encode(text, normalize_embeddings=True).tolist()


class TFIDFEmbedder:
    """TF-IDF fallback (pure Python)."""

    def __init__(self):
        self._vocab = None
        self._idf = None
        print("✅ TF-IDF fallback embedder ready")

    def _tokenize(self, text: str) -> list:
        return re.findall(r"\b[a-z0-9]+\b", text.lower())

    def fit(self, docs: list):
        vocab = set()
        for d in docs:
            vocab.update(self._tokenize(d))
        self._vocab = {w: i for i, w in enumerate(sorted(vocab))}

        N = len(docs)
        df = Counter()
        for d in docs:
            df.update(set(self._tokenize(d)))
        self._idf = {w: math.log((N + 1) / (df[w] + 1)) + 1 for w in self._vocab}

    def embed(self, text: str) -> list:
        if self._vocab is None:
            return []
        tokens = self._tokenize(text)
        counts = Counter(tokens)
        total = max(sum(counts.values()), 1)
        vec = [0.0] * len(self._vocab)
        for w, c in counts.items():
            if w in self._vocab:
                vec[self._vocab[w]] = (c / total) * self._idf.get(w, 1.0)
        return vec


def _build_embedder():
    preferred = (settings.EMBEDDING_BACKEND or "auto").lower()

    if preferred == "neural":
        try:
            print("🧠 Using neural embeddings (forced)")
            return NeuralEmbedder()
        except Exception as e:
            print(f"⚠️ Neural failed: {e}. Falling back to TF-IDF")
            return TFIDFEmbedder()

    if preferred == "tfidf":
        print("📊 Using TF-IDF (forced)")
        return TFIDFEmbedder()

    try:
        emb = NeuralEmbedder()
        print("✅ Auto-selected: Neural embeddings (semantic search)")
        return emb
    except Exception as e:
        print(f"⚠️ Neural unavailable ({type(e).__name__}). Using TF-IDF fallback")
        return TFIDFEmbedder()


embedder = _build_embedder()
_embedder_is_tfidf = isinstance(embedder, TFIDFEmbedder)


# =========================================================
# RAG PIPELINE (ChromaDB as vector store)
# =========================================================
def ingest(text: str, source: str) -> int:
    """
    Chunk → embed → store in ChromaDB.
    ChromaDB persists to CHROMA_DIR automatically.
    """
    chunks = [
        text[i:i + settings.CHUNK_SIZE]
        for i in range(0, len(text), settings.CHUNK_SIZE)
    ]
    chunks = [c.strip() for c in chunks if c.strip()]
    if not chunks:
        return 0

    # TF-IDF fallback needs the corpus to fit before embedding
    if _embedder_is_tfidf:
        embedder.fit(chunks)

    embeddings = [embedder.embed(c) for c in chunks]
    ids = [f"{source}::{i}" for i in range(len(chunks))]
    metadatas = [{"source": source, "chunk_index": i} for i in range(len(chunks))]

    _chroma_collection.add(
        ids=ids,
        documents=chunks,
        embeddings=embeddings,
        metadatas=metadatas,
    )
    return len(chunks)


def search_kb(query: str, top_k: int = None) -> list:
    """Semantic search against ChromaDB."""
    top_k = top_k or settings.TOP_K_RAG

    if _chroma_collection.count() == 0:
        return []

    query_vec = embedder.embed(query)
    if not query_vec:
        return []

    results = _chroma_collection.query(
        query_embeddings=[query_vec],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    hits = []
    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    dists = results.get("distances", [[]])[0]

    for doc, meta, dist in zip(docs, metas, dists):
        # ChromaDB cosine distance → similarity = 1 - distance
        similarity = round(1.0 - float(dist), 3)
        hits.append({
            "text": doc,
            "source": (meta or {}).get("source", "unknown"),
            "score": similarity,
        })

    hits.sort(key=lambda x: x["score"], reverse=True)
    return hits[:top_k]


def answer_with_rag(question: str) -> dict:
    matches = search_kb(question)
    context = "\n\n".join(f"[{m['source']}]\n{m['text']}" for m in matches)
    from src.prompts import RAG_PROMPT
    answer = llm.chat(RAG_PROMPT.format(context=context, question=question), 350)
    return {
        "answer": answer,
        "sources": [{"source": m["source"], "score": m["score"]} for m in matches],
    }