"""
游戏 API：题库、速句测评、游戏记录保存
"""
import json
import random
from pathlib import Path
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import GameRecord

router = APIRouter(prefix="/api/game", tags=["game"])


def _load(name):
    p = Path(__file__).parent.parent / "data" / f"data_{name}.json"
    return json.load(open(p, encoding="utf-8"))


class GameRecordIn(BaseModel):
    mode: str
    difficulty: str | None = None
    score: int
    correct: int
    total: int


@router.get("/quiz")
def get_quiz(difficulty: str = "easy", count: int = 10):
    """随机抽取 count 道指定难度的题目"""
    qbank = _load("QBANK_ALL")
    pool = qbank.get(difficulty) or qbank["easy"]
    random.shuffle(pool)
    return pool[:count]


@router.get("/speech")
def get_speech_questions():
    """发音测评题目列表"""
    return _load("SPEECH_QS")


@router.post("/record")
def save_record(r: GameRecordIn, db: Session = Depends(get_db)):
    """保存一次游戏记录"""
    rec = GameRecord(
        mode=r.mode,
        difficulty=r.difficulty,
        score=r.score,
        correct_count=r.correct,
        total=r.total,
    )
    db.add(rec)
    db.commit()
    return {"ok": True, "id": rec.id}


@router.get("/history")
def get_history(limit: int = 20, db: Session = Depends(get_db)):
    """最近游戏历史（大赛答辩可展示）"""
    rows = db.query(GameRecord).order_by(GameRecord.id.desc()).limit(limit).all()
    return [
        {
            "id": r.id, "mode": r.mode, "difficulty": r.difficulty,
            "score": r.score, "correct": r.correct_count, "total": r.total,
            "played_at": r.played_at.isoformat() if r.played_at else None,
        }
        for r in rows
    ]
