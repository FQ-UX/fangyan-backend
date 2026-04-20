"""
成就系统 API
"""
import json
from pathlib import Path
from datetime import date
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import UserAchievement

router = APIRouter(prefix="/api/achievements", tags=["achievements"])

_ACH_DATA = None


def _load_achs():
    global _ACH_DATA
    if _ACH_DATA is None:
        p = Path(__file__).parent.parent / "data" / "data_ACHS.json"
        _ACH_DATA = json.load(open(p, encoding="utf-8"))
    return _ACH_DATA


class UnlockIn(BaseModel):
    ach_id: int
    progress_c: int | None = None


@router.get("")
def list_achievements(db: Session = Depends(get_db)):
    """返回所有成就及其用户状态"""
    static = _load_achs()
    user_rows = {r.ach_id: r for r in db.query(UserAchievement).all()}
    out = []
    for a in static:
        ur = user_rows.get(a["id"])
        # 默认从静态数据读已完成状态（保留 demo 数据的 3 个初始成就）
        done = bool(a.get("done", False))
        date_str = a.get("date")
        prog_c = None
        if "prog" in a:
            prog_c = a["prog"]["c"]
        if ur:
            done = ur.done or done
            if ur.unlocked_at:
                date_str = ur.unlocked_at
            if ur.progress_c:
                prog_c = ur.progress_c
        item = {**a, "done": done, "date": date_str}
        if "prog" in a and prog_c is not None:
            item["prog"] = {**a["prog"], "c": prog_c}
        out.append(item)
    return out


@router.post("/unlock")
def unlock(payload: UnlockIn, db: Session = Depends(get_db)):
    """解锁一个成就或更新其进度"""
    row = db.query(UserAchievement).filter_by(ach_id=payload.ach_id).first()
    if not row:
        row = UserAchievement(ach_id=payload.ach_id)
        db.add(row)
    if payload.progress_c is not None:
        row.progress_c = payload.progress_c
    row.done = True
    if not row.unlocked_at:
        row.unlocked_at = date.today().isoformat()
    db.commit()
    return {"ok": True}


@router.post("/progress")
def update_progress(payload: UnlockIn, db: Session = Depends(get_db)):
    """仅更新进度，不解锁"""
    row = db.query(UserAchievement).filter_by(ach_id=payload.ach_id).first()
    if not row:
        row = UserAchievement(ach_id=payload.ach_id, progress_c=payload.progress_c or 0)
        db.add(row)
    else:
        if payload.progress_c is not None:
            row.progress_c = payload.progress_c
    db.commit()
    return {"ok": True}
