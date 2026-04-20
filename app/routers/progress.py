"""
用户进度 API：积分、连续天数、学习统计
"""
import json
from datetime import date, datetime
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import UserState, StudyLog

router = APIRouter(prefix="/api/progress", tags=["progress"])


class ProgressOut(BaseModel):
    pts: int
    streak: int
    wordsLearned: int
    dlgCnt: int
    gameCnt: int
    storiesPlayed: list
    dialectsUsed: list
    currentDialect: str
    storiesLiked: list
    storiesRead: int
    cmpViewCount: int


class ProgressUpdate(BaseModel):
    pts: int | None = None
    streak: int | None = None
    wordsLearned: int | None = None
    dlgCnt: int | None = None
    gameCnt: int | None = None
    storiesPlayed: list | None = None
    dialectsUsed: list | None = None
    currentDialect: str | None = None
    storiesLiked: list | None = None
    storiesRead: int | None = None
    cmpViewCount: int | None = None


class AddPtsIn(BaseModel):
    amount: int
    reason: str = ""


def _get_or_create_user(db: Session) -> UserState:
    u = db.query(UserState).filter_by(id=1).first()
    if not u:
        u = UserState(id=1)
        db.add(u)
        db.commit()
        db.refresh(u)
    return u


def _log_study(db: Session):
    """记录一次今日学习活动，用于日历打卡"""
    today_str = date.today().isoformat()
    log = db.query(StudyLog).filter_by(date=today_str).first()
    if not log:
        log = StudyLog(date=today_str, events=1)
        db.add(log)
    else:
        log.events += 1
    db.commit()


@router.get("", response_model=ProgressOut)
def get_progress(db: Session = Depends(get_db)):
    u = _get_or_create_user(db)
    return ProgressOut(
        pts=u.pts,
        streak=u.streak,
        wordsLearned=u.words_learned,
        dlgCnt=u.dlg_cnt,
        gameCnt=u.game_cnt,
        storiesPlayed=json.loads(u.stories_played or "[]"),
        dialectsUsed=json.loads(u.dialects_used or "[]"),
        currentDialect=u.current_dialect,
        storiesLiked=json.loads(u.stories_liked or "[]"),
        storiesRead=u.stories_read,
        cmpViewCount=u.cmp_view_count,
    )


@router.patch("")
def update_progress(payload: ProgressUpdate, db: Session = Depends(get_db)):
    u = _get_or_create_user(db)
    d = payload.model_dump(exclude_unset=True)

    # 标量字段
    if "pts" in d: u.pts = d["pts"]
    if "streak" in d: u.streak = d["streak"]
    if "wordsLearned" in d: u.words_learned = d["wordsLearned"]
    if "dlgCnt" in d: u.dlg_cnt = d["dlgCnt"]
    if "gameCnt" in d: u.game_cnt = d["gameCnt"]
    if "currentDialect" in d: u.current_dialect = d["currentDialect"]
    if "storiesRead" in d: u.stories_read = d["storiesRead"]
    if "cmpViewCount" in d: u.cmp_view_count = d["cmpViewCount"]

    # JSON 字段
    if "storiesPlayed" in d: u.stories_played = json.dumps(d["storiesPlayed"])
    if "dialectsUsed" in d: u.dialects_used = json.dumps(d["dialectsUsed"])
    if "storiesLiked" in d: u.stories_liked = json.dumps(d["storiesLiked"])

    _log_study(db)
    db.commit()
    return {"ok": True}


@router.post("/pts")
def add_pts(payload: AddPtsIn, db: Session = Depends(get_db)):
    u = _get_or_create_user(db)
    u.pts += payload.amount
    _log_study(db)
    db.commit()
    return {"pts": u.pts, "added": payload.amount}


@router.get("/calendar")
def get_calendar(db: Session = Depends(get_db)):
    """返回本月所有已学习的日期"""
    today = date.today()
    month_str = today.strftime("%Y-%m")
    logs = db.query(StudyLog).filter(StudyLog.date.like(f"{month_str}-%")).all()
    return {
        "month": month_str,
        "studied": [l.date for l in logs],
    }
