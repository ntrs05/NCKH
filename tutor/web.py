"""Lớp mỏng nối TutorSession với giao diện web (nhiều phiên, một khoá sinh)."""
from __future__ import annotations

import re
import threading

from .config import Config
from .engine import Engine
from .session import TutorSession

MODES = {"socratic": "1", "visual": "2", "worked": "3"}  # khoá giao diện -> chế độ 1/2/3
MAX_CHARS = 500
MAX_SESSIONS = 50

_FRAC = re.compile(r"\\frac\{([^{}]+)\}\{([^{}]+)\}")


def plain_text(text: str) -> str:
    """Bỏ LaTeX/Markdown mà khung chat đơn giản không vẽ được."""
    t = text.replace("\\times", "×").replace("\\div", ":").replace("\\cdot", "·")
    t = _FRAC.sub(r"\1/\2", t)
    t = re.sub(r"\\text\{\s*([^{}]*?)\s*\}", r"\1", t)
    t = re.sub(r"\\[(\[]\s*|\s*\\[)\]]|\$", "", t)
    t = re.sub(r"\*\*|__", "", t)
    t = re.sub(r"(?m)^\s{0,3}#{1,6}\s*", "", t)
    t = re.sub(r"(?m)^\s*-{3,}\s*$", "", t)
    return re.sub(r"\n{3,}", "\n\n", t).strip()


class WebTutor:
    """Giữ các TutorSession theo session_id; llama.cpp chỉ sinh một lượt tại một thời điểm."""

    def __init__(self, engine: Engine, cfg: Config) -> None:
        self.engine, self.cfg = engine, cfg
        self._lock = threading.Lock()
        self._sessions: dict[str, TutorSession] = {}

    def chat(self, session_id: str, mode: str, message: str) -> str:
        key = MODES.get(mode)
        if key is None:
            raise ValueError("Chế độ học không hợp lệ.")
        message = message.strip()
        if not message:
            raise ValueError("Tin nhắn đang để trống.")
        if len(message) > MAX_CHARS:
            raise ValueError(f"Tin nhắn dài quá {MAX_CHARS} ký tự, em viết ngắn hơn nhé.")
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                if len(self._sessions) >= MAX_SESSIONS:
                    self._sessions.pop(next(iter(self._sessions)))  # bỏ phiên cũ nhất
                session = self._sessions[session_id] = TutorSession(self.engine, key, self.cfg)
            elif session.mode != key:
                session.set_mode(key)
            return plain_text(session.send(message).reply)

    def reset(self, session_id: str) -> None:
        with self._lock:
            self._sessions.pop(session_id, None)
