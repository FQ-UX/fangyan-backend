"""
AI 对话 API (模块 2)
使用阿里云通义 qwen3-omni-flash，一次调用同时获得文字回复 + 方言语音
"""
import json
from typing import List, Optional
from pathlib import Path
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import ChatMessage
from app.services.qwen import chat_with_audio, DIALECT_VOICE
from app.services.rag import retrieve_words

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatMsg(BaseModel):
    role: str           # 'user' or 'assistant'
    content: str


class ChatRequest(BaseModel):
    dialect: str = "普通话"
    message: str
    history: List[ChatMsg] = []
    include_audio: bool = True


class ChatResponse(BaseModel):
    reply: str
    dialect: str
    voice: str
    audio_base64: Optional[str] = None
    rag_hits: List[dict] = []


@router.post("", response_model=ChatResponse)
async def chat(req: ChatRequest, db: Session = Depends(get_db)):
    """发送一条消息，接收 AI 的方言回复 + 同步合成的方言语音"""
    rag_hits = retrieve_words(req.message, dialect=req.dialect, top_k=3)

    history_msgs = [{"role": m.role, "content": m.content} for m in req.history[-8:]]
    history_msgs.append({"role": "user", "content": req.message})

    reply_text, audio_b64 = await chat_with_audio(
        dialect=req.dialect,
        history=history_msgs,
        rag_hits=rag_hits,
    )

    try:
        db.add(ChatMessage(dialect=req.dialect, role="user", content=req.message))
        db.add(ChatMessage(dialect=req.dialect, role="assistant", content=reply_text))
        db.commit()
    except Exception as e:
        print(f"[chat] DB 写入失败: {e}")
        db.rollback()

    return ChatResponse(
        reply=reply_text,
        dialect=req.dialect,
        voice=DIALECT_VOICE.get(req.dialect, "Cherry"),
        audio_base64=audio_b64 if req.include_audio else None,
        rag_hits=rag_hits,
    )


@router.get("/quick-phrases")
def quick_phrases(dialect: str = "普通话"):
    """获取某方言的快捷短语"""
    p = Path(__file__).parent.parent / "data" / "data_QUICK.json"
    try:
        data = json.load(open(p, encoding="utf-8"))
        return {"phrases": data.get(dialect, data.get("普通话", []))}
    except Exception as e:
        return {"phrases": [], "error": str(e)}


@router.get("/history")
def chat_history(
    dialect: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    q = db.query(ChatMessage)
    if dialect:
        q = q.filter_by(dialect=dialect)
    rows = q.order_by(ChatMessage.id.desc()).limit(limit).all()
    return [
        {
            "role": r.role,
            "content": r.content,
            "dialect": r.dialect,
            "at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in reversed(rows)
    ]


@router.delete("/history")
def clear_history(db: Session = Depends(get_db)):
    db.query(ChatMessage).delete()
    db.commit()
    return {"ok": True}
