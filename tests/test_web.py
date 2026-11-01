"""Kiểm thử lớp web (backend mock, không cần model/GPU/fastapi)."""

import pytest

from tutor.config import Config
from tutor.engine import Engine
from tutor.web import MAX_CHARS, WebTutor, plain_text

PROBLEM = "Hai bạn An và Bình có tổng cộng 24 cái kẹo. An có nhiều hơn Bình 6 cái kẹo. Hỏi mỗi bạn có bao nhiêu cái kẹo?"


@pytest.fixture()
def web():
    cfg = Config.load().with_overrides({"engine.backend": "mock"})
    engine = Engine(cfg)
    engine.load()
    return WebTutor(engine, cfg)


def test_chat_tra_loi_va_doi_che_do(web):
    assert web.chat("phien-0001", "socratic", PROBLEM)
    assert "|--" in web.chat("phien-0002", "visual", PROBLEM)  # sơ đồ đoạn thẳng ASCII


def test_tin_nhan_khong_hop_le(web):
    with pytest.raises(ValueError):
        web.chat("phien-0001", "khong-co", "xin chào")
    with pytest.raises(ValueError):
        web.chat("phien-0001", "socratic", "   ")
    with pytest.raises(ValueError):
        web.chat("phien-0001", "socratic", "x" * (MAX_CHARS + 1))


def test_reset_bat_dau_lai_phien(web):
    web.chat("phien-0001", "socratic", PROBLEM)
    web.reset("phien-0001")
    assert "phien-0001" not in web._sessions


def test_plain_text_bo_latex_va_markdown():
    raw = "### Bước 1\n**Mỗi phần** là \\( \\frac{36}{4} = 9 \\text{ kg} \\)\n---\n"
    out = plain_text(raw)
    assert "\\" not in out and "**" not in out and "###" not in out
    assert "36/4 = 9 kg" in out
