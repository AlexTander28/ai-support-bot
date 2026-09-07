from __future__ import annotations

import pytest

from app.config import ConfigurationError, Settings
from app.keyboards import HandoffAction, faq_keyboard, handoff_keyboard


def test_handoff_keyboard_uses_typed_callback() -> None:
    callback = handoff_keyboard().inline_keyboard[0][0].callback_data
    unpacked = HandoffAction.unpack(callback)

    assert unpacked.action == "request"


def test_faq_keyboard_has_four_questions() -> None:
    assert len(faq_keyboard().inline_keyboard) == 4


def test_settings_refuse_placeholder_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BOT_TOKEN", "replace_with_botfather_token")
    monkeypatch.setenv("MANAGER_CHAT_ID", "123")
    monkeypatch.setenv("MANAGER_IDS", "123")

    with pytest.raises(ConfigurationError, match="BOT_TOKEN"):
        Settings.from_env()

