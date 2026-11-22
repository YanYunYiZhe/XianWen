"""Web 路由：开始页、游戏页和选择提交。

路由只调用核心公开接口，不直接构造或修改游戏状态。
"""

from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from xianwen.core.engine import (
    InvalidChoiceError,
    InvalidEventError,
    apply_choice,
    get_current_event,
    new_game,
)
from xianwen.core.models import LegacyGameState
from xianwen.web.save import SaveFormatError, dump_save, load_save

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    """渲染开始页。"""
    return templates.TemplateResponse(request, "index.html")


@router.post("/game/start", response_class=HTMLResponse)
def start_game(request: Request) -> HTMLResponse:
    """创建新游戏并渲染第一回合。"""
    return _render_game(request, new_game())


@router.post("/game/choice", response_class=HTMLResponse)
def submit_choice(
    request: Request,
    save: Annotated[str, Form()],
    event_id: Annotated[str, Form()],
    choice_id: Annotated[str, Form()],
) -> HTMLResponse:
    """提交玩家选择；非法输入失败关闭，不修改状态。"""
    try:
        state = load_save(save)
    except SaveFormatError:
        return _render_broken_save(request)

    try:
        result = apply_choice(state, event_id, choice_id)
    except (InvalidEventError, InvalidChoiceError):
        return _render_game(
            request,
            state,
            error="该选项无效，请重新选择。",
            status_code=400,
        )
    return _render_game(request, result.state, result_text=result.result_text)


def _render_game(
    request: Request,
    state: LegacyGameState,
    *,
    result_text: str | None = None,
    error: str | None = None,
    status_code: int = 200,
) -> HTMLResponse:
    """渲染游戏页；save_json 是唯一随页面流转的状态载体。"""
    return templates.TemplateResponse(
        request,
        "game.html",
        {
            "state": state,
            "event": get_current_event(state),
            "save_json": dump_save(state),
            "result_text": result_text,
            "error": error,
        },
        status_code=status_code,
    )


def _render_broken_save(request: Request) -> HTMLResponse:
    """存档损坏时回到开始页并给出明确提示。"""
    return templates.TemplateResponse(
        request,
        "index.html",
        {"error": "存档格式无效，请重新开始游戏。"},
        status_code=400,
    )
