"""
数据库模型定义
单用户模式（方案B），UserState 表永远只有一条 id=1 的记录
"""
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, Boolean
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()


class UserState(Base):
    """用户状态 - 单用户模式，永远只有一条 id=1"""
    __tablename__ = "user_state"

    id = Column(Integer, primary_key=True, default=1)
    pts = Column(Integer, default=260)
    streak = Column(Integer, default=3)
    words_learned = Column(Integer, default=0)
    dlg_cnt = Column(Integer, default=0)
    game_cnt = Column(Integer, default=0)
    stories_played = Column(Text, default="[]")       # JSON array of story IDs
    dialects_used = Column(Text, default='["普通话"]')   # JSON array
    current_dialect = Column(String, default="普通话")
    stories_liked = Column(Text, default="[]")
    stories_read = Column(Integer, default=0)
    cmp_view_count = Column(Integer, default=0)
    last_login = Column(DateTime, default=datetime.utcnow)


class UserAchievement(Base):
    """用户已解锁的成就记录"""
    __tablename__ = "user_achievements"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ach_id = Column(Integer, unique=True, index=True)
    done = Column(Boolean, default=False)
    progress_c = Column(Integer, default=0)     # 当前进度
    unlocked_at = Column(String, nullable=True)


class ChatMessage(Base):
    """聊天记录（可用于答辩展示多轮对话历史）"""
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    dialect = Column(String, index=True)
    role = Column(String)              # 'user' or 'assistant'
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class GameRecord(Base):
    """游戏记录"""
    __tablename__ = "game_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    mode = Column(String)              # 'quiz' or 'speech'
    difficulty = Column(String, nullable=True)     # 'easy' 'mid' 'hard'
    score = Column(Integer)
    correct_count = Column(Integer)
    total = Column(Integer)
    played_at = Column(DateTime, default=datetime.utcnow)


class StudyLog(Base):
    """每日学习日志（用于日历打卡）"""
    __tablename__ = "study_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(String, index=True)  # YYYY-MM-DD
    events = Column(Integer, default=0)     # 当日活动次数
