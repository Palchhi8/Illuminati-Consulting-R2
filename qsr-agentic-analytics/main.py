import os
import socket
from pathlib import Path

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from orchestrator import answer_question
from queries import ensure_database_ready


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
INDEX_HTML = STATIC_DIR / "index.html"
load_dotenv(BASE_DIR / ".env")


class QuestionRequest(BaseModel):
    question: str


app = FastAPI(title="QSR Agentic Analytics")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
def read_root() -> FileResponse:
    return FileResponse(str(INDEX_HTML))


@app.get("/favicon.ico")
def favicon() -> Response:
    return Response(content=b"", media_type="image/x-icon")


@app.get("/health")
def health_check() -> dict:
    return {"status": "ok"}


@app.post("/ask")
def ask_question(request: QuestionRequest) -> dict:
    try:
        result = answer_question(request.question)
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to process question: {exc}") from exc


def get_available_port(start_port: int, host: str, max_attempts: int = 20) -> int:
    for port in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind((host, port))
                return port
            except OSError:
                continue
    raise RuntimeError(f"No available port found starting from {start_port}")


def run_server() -> None:
    host = os.getenv("HOST", "127.0.0.1")
    configured_port = int(os.getenv("PORT", "8000"))
    auto_port = os.getenv("AUTO_PORT", "true").lower() not in {"0", "false", "no"}
    use_auto_port = auto_port and host in {"127.0.0.1", "localhost", "0.0.0.0"}
    port = get_available_port(configured_port, host) if use_auto_port else configured_port

    ensure_database_ready()
    print(f"Starting server on http://{host}:{port}")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_server()
