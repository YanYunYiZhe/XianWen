"""FastAPI application entry for XianWen."""

from fastapi import FastAPI

app = FastAPI(title="XianWen", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    """Return a fixed health payload for smoke checks and CI."""
    return {"status": "ok", "service": "xianwen"}
