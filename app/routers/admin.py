"""
管理员/统计 API (模块 8)
后端数据统计接口。不在前端显示入口，答辩时通过以下方式展示：
  - 访问 http://127.0.0.1:8000/docs 查看所有 API
  - 直接访问 http://127.0.0.1:8000/api/admin/stats 看 JSON
  - curl http://127.0.0.1:8000/api/admin/dialect-distribution
"""
import json
from pathlib import Path
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db import get_db
from app.models import ChatMessage, GameRecord, UserAchievement, StudyLog

router = APIRouter(prefix="/api/admin", tags=["admin"])

DATA_DIR = Path(__file__).parent.parent / "data"


def _load(name):
    return json.load(open(DATA_DIR / f"data_{name}.json", encoding="utf-8"))


@router.get("/stats", summary="系统数据概览")
def overview_stats(db: Session = Depends(get_db)):
    """返回系统全景数据：内容规模 + 使用统计"""
    words = _load("WORDS")
    stories = _load("STORIES")
    qbank = _load("QBANK_ALL")
    achs = _load("ACHS")

    chat_count = db.query(ChatMessage).count()
    game_count = db.query(GameRecord).count()
    ach_unlocked = db.query(UserAchievement).filter_by(done=True).count()
    study_days = db.query(StudyLog).count()
    quiz_total = sum(len(qs) for qs in qbank.values())

    real_audio = sum(1 for s in stories if s.get("has_real_audio"))

    return {
        "content": {
            "dict_words": len(words),
            "stories": len(stories),
            "stories_with_real_audio": real_audio,
            "stories_with_tts": len(stories) - real_audio,
            "quiz_questions": quiz_total,
            "achievements": len(achs),
            "dialects": len({w["dialect"] for w in words}),
        },
        "usage": {
            "chat_messages": chat_count,
            "games_played": game_count,
            "achievements_unlocked": ach_unlocked,
            "study_days": study_days,
        },
        "api_tech_stack": {
            "llm": "qwen3-omni-flash (阿里云通义千问多模态大模型)",
            "framework": "FastAPI + SQLAlchemy + SQLite",
            "features": [
                "文本对话 + 方言 TTS（一次 API 调用双输出）",
                "方言语音识别 + Levenshtein 相似度打分",
                "RAG 检索增强（从方言词典动态注入 Prompt）",
                "音频缓存（磁盘持久化，同文本重复合成秒回）",
                "持久化学习进度（SQLite）",
            ],
        },
    }


@router.get("/dialect-distribution", summary="方言使用分布")
def dialect_distribution(db: Session = Depends(get_db)):
    """按方言分组统计用户发起的对话数"""
    rows = (
        db.query(ChatMessage.dialect, func.count(ChatMessage.id))
        .filter(ChatMessage.role == "user")
        .group_by(ChatMessage.dialect)
        .all()
    )
    return [{"dialect": d or "普通话", "count": c} for d, c in rows]


@router.get("/recent-chats", summary="最近对话（脱敏）")
def recent_chats(limit: int = 20, db: Session = Depends(get_db)):
    """返回最近 N 条聊天记录"""
    rows = (
        db.query(ChatMessage)
        .order_by(ChatMessage.id.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "role": r.role,
            "content": r.content[:80] + ("…" if len(r.content) > 80 else ""),
            "dialect": r.dialect,
            "at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in reversed(rows)
    ]


@router.get("/top-games", summary="游戏战绩 Top N")
def top_games(limit: int = 10, db: Session = Depends(get_db)):
    rows = (
        db.query(GameRecord)
        .order_by(GameRecord.score.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "mode": r.mode,
            "difficulty": r.difficulty,
            "score": r.score,
            "correct": r.correct_count,
            "total": r.total,
            "accuracy": round(r.correct_count / r.total, 3) if r.total else 0,
            "at": r.played_at.isoformat() if r.played_at else None,
        }
        for r in rows
    ]


@router.get("/hot-words", summary="常用词条 Top N")
def hot_words(limit: int = 10):
    """简易版：按"常用"难度取前 N"""
    words = _load("WORDS")
    common = [w for w in words if w.get("diff") == 1][:limit]
    return [
        {"id": w["id"], "char": w["char"], "dialect": w["dialect"], "meaning": w["meaning"]}
        for w in common
    ]


@router.get("/recent-games", summary="最近游戏记录")
def recent_games(limit: int = 10, db: Session = Depends(get_db)):
    """时间倒序的游戏记录"""
    rows = (
        db.query(GameRecord)
        .order_by(GameRecord.played_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "mode": r.mode,
            "difficulty": r.difficulty,
            "score": r.score,
            "accuracy": round(r.correct_count / r.total, 3) if r.total else 0,
            "at": r.played_at.isoformat() if r.played_at else None,
        }
        for r in rows
    ]


@router.get("/achievement-progress", summary="成就解锁进度")
def achievement_progress(db: Session = Depends(get_db)):
    """已解锁成就列表"""
    rows = db.query(UserAchievement).filter_by(done=True).all()
    return {
        "total_unlocked": len(rows),
        "unlocked_ids": [r.ach_id for r in rows],
        "unlocked_at": [r.unlocked_at.isoformat() if r.unlocked_at else None for r in rows],
    }
