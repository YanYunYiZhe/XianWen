"""FastAPI application entry for XianWen."""

from fastapi import FastAPI

from xianwen.web.routes import router

app = FastAPI(title="XianWen", version="0.1.0")
app.include_router(router)


@app.get("/health")
def health() -> dict[str, str]:
    """Return a fixed health payload for smoke checks and CI."""
    return {"status": "ok", "service": "xianwen"}
