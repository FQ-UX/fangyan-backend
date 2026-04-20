"""
方言词典 API：词条查询、方言分类、对照表
"""
import json
from pathlib import Path
from fastapi import APIRouter, Query
from typing import Optional

router = APIRouter(prefix="/api/dict", tags=["dict"])


def _load(name: str):
    p = Path(__file__).parent.parent / "data" / f"data_{name}.json"
    return json.load(open(p, encoding="utf-8"))


@router.get("/words")
def list_words(
    dialect: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    sort: str = Query("default"),
):
    """返回词典列表，支持方言筛选、关键词搜索、排序"""
    words = _load("WORDS")
    if dialect and dialect != "all":
        words = [w for w in words if w["dialect"] == dialect]
    if q:
        q_lower = q.lower()
        words = [
            w for w in words
            if q in w["char"] or q in w["meaning"]
            or q_lower in w["pin"].lower() or q in w["dialect"]
        ]
    if sort == "alpha":
        words.sort(key=lambda w: w["pin"])
    elif sort == "difficulty":
        words.sort(key=lambda w: w["diff"])
    return words


@router.get("/word/{word_id}")
def get_word(word_id: int):
    words = _load("WORDS")
    for w in words:
        if w["id"] == word_id:
            return w
    return {"error": "not found"}


@router.get("/dialects")
def list_dialects():
    return _load("DICT_CATS")


@router.get("/compare")
def list_comparisons():
    """方言对照表"""
    return _load("CMP_DATA")
