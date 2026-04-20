"""
故事 API：列表、全文、点赞
"""
import json
from pathlib import Path
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import UserState

router = APIRouter(prefix="/api/stories", tags=["stories"])


def _load(name):
    p = Path(__file__).parent.parent / "data" / f"data_{name}.json"
    return json.load(open(p, encoding="utf-8"))


@router.get("")
def list_stories():
    """返回故事列表（含用户点赞状态）"""
    stories = _load("STORIES")
    return stories


@router.get("/categories")
def story_categories():
    return _load("STORY_CATS")


@router.get("/{story_id}/text")
def get_story_text(story_id: int):
    """获取某个故事的完整正文"""
    texts = _load("STORY_TEXTS")
    text = texts.get(str(story_id)) or texts.get(story_id)
    if not text:
        return {"error": "not found"}
    # 同时返回封面、方言等信息
    stories = _load("STORIES")
    meta = next((s for s in stories if s["id"] == story_id), None)
    return {"id": story_id, "text": text, "meta": meta}
