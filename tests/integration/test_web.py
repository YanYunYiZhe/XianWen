"""Web 最小闭环集成测试。"""

import html
import json
import re

import httpx
import pytest
from fastapi.testclient import TestClient

from xianwen.core.engine import new_game
from xianwen.main import app
from xianwen.web.save import SaveFormatError, dump_save, load_save

client = TestClient(app)

EVENT_ID = "base.morning_training"


def _hidden_save(page: str) -> str:
    match = re.search(r'name="save" value="([^"]+)"', page)
    assert match is not None
    return html.unescape(match.group(1))


def _choose(page: str, choice_id: str) -> httpx.Response:
    return client.post(
        "/game/choice",
        data={
            "save": _hidden_save(page),
            "event_id": EVENT_ID,
            "choice_id": choice_id,
        },
    )


def test_index_page_has_start_button() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "开始游戏" in response.text


def test_start_game_shows_first_turn() -> None:
    response = client.post("/game/start")
    assert response.status_code == 200
    assert "第 1 年" in response.text
    assert "修为 0" in response.text
    assert "清晨灵气尚可" in response.text


def test_cultivate_advances_year_and_cultivation() -> None:
    page = client.post("/game/start").text
    response = _choose(page, "cultivate")
    assert response.status_code == 200
    assert "第 2 年" in response.text
    assert "修为 1" in response.text


def test_rest_advances_year_only() -> None:
    page = client.post("/game/start").text
    response = _choose(page, "rest")
    assert response.status_code == 200
    assert "第 2 年" in response.text
    assert "修为 0" in response.text


def test_invalid_choice_returns_error() -> None:
    page = client.post("/game/start").text
    response = _choose(page, "meditate")
    assert response.status_code == 400
    assert "无效" in response.text


def test_broken_save_returns_error() -> None:
    response = client.post(
        "/game/choice",
        data={"save": "{not json}", "event_id": EVENT_ID, "choice_id": "cultivate"},
    )
    assert response.status_code == 400
    assert "存档" in response.text


def test_save_round_trip_and_fields() -> None:
    state = new_game()
    assert load_save(dump_save(state)) == state

    payload = json.loads(dump_save(state))
    assert payload["schema_version"] == 1
    assert set(payload) == {
        "schema_version",
        "game",
        "plugin_state",
        "plugin_versions",
        "usage",
    }
    assert "api_key" not in dump_save(state).lower()


def test_save_rejects_api_key_field() -> None:
    payload = json.loads(dump_save(new_game()))
    payload["api_key"] = "sk-test"
    with pytest.raises(SaveFormatError):
        load_save(json.dumps(payload))
