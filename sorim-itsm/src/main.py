"""FastAPI entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.config import settings
from src.routes import router

settings.validate()

app = FastAPI(
    title="Sorim.ai ITSM Platform",
    version="1.0",
    description="AI-Powered ITSM & Intelligent Helpdesk Automation",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=settings.ALLOW_CREDENTIALS,
    allow_methods=settings.ALLOW_METHODS,
    allow_headers=settings.ALLOW_HEADERS,
)

app.include_router(router)


@app.get("/")
def root():
    return {"status": "ok", "platform": "Sorim.ai ITSM", "version": "1.0"}


@app.get("/health")
def health():
    """Reports which LLM / embedder is active right now."""
    from src.ai import llm, embedder
    llm_name = getattr(llm, "active_name", type(llm).__name__)
    return {
        "status": "ok",
        "llm_backend": llm_name,
        "embedder_backend": type(embedder).__name__,
        "env": settings.ENV,
    }


# =========================================================
# Dev entrypoint — run `python -m src.main` to start server
# =========================================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",       # module path : app variable
        host="0.0.0.0",       # 0.0.0.0 = accessible on your LAN + localhost
        port=8000,            # ← your port here
        reload=True,          # hot-reload on file changes (dev only)
    )



    ######### to run - python -m src.main ##############