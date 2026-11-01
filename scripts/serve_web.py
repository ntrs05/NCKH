"""Chạy giao diện web: python scripts/serve_web.py [--mock] [--port 8000]"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from tutor.config import Config
from tutor.engine import Engine, EngineError
from tutor.web import MAX_CHARS, WebTutor


class ChatIn(BaseModel):
    session_id: str = Field(min_length=8, max_length=64)
    mode: str
    message: str = Field(min_length=1, max_length=MAX_CHARS * 2)


class ResetIn(BaseModel):
    session_id: str = Field(min_length=8, max_length=64)


def create_app(web: WebTutor) -> FastAPI:
    app = FastAPI(title="Gia sư Toán tiểu học")

    @app.post("/api/chat")
    def chat(body: ChatIn) -> dict[str, str]:
        try:
            return {"reply": web.chat(body.session_id, body.mode, body.message)}
        except ValueError as exc:
            raise HTTPException(400, str(exc))
        except Exception:
            raise HTTPException(500, "Gia sư đang gặp sự cố. Em thử gửi lại nhé.")

    @app.post("/api/reset")
    def reset(body: ResetIn) -> dict[str, bool]:
        web.reset(body.session_id)
        return {"ok": True}

    @app.get("/")
    def index() -> FileResponse:
        return FileResponse(ROOT / "web" / "index.html")

    @app.get("/style.css")
    def style() -> FileResponse:
        return FileResponse(ROOT / "web" / "style.css", media_type="text/css")

    return app


def main() -> int:
    ap = argparse.ArgumentParser(description="Giao diện web cho gia sư Toán tiểu học")
    ap.add_argument("--config", help="đường dẫn config.yaml")
    ap.add_argument("--model", help="đường dẫn file .gguf (ghi đè config)")
    ap.add_argument(
        "--mock", action="store_true", help="backend giả lập, không cần model"
    )
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8000)
    args = ap.parse_args()

    cfg = Config.load(args.config)
    if args.mock:
        cfg = cfg.with_overrides({"engine.backend": "mock"})
    try:
        engine = Engine(cfg, model_path=args.model)
        engine.load()
    except EngineError as exc:
        print(f"LỖI: {exc}")
        return 2
    uvicorn.run(create_app(WebTutor(engine, cfg)), host=args.host, port=args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
