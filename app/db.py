"""
数据库连接和会话管理
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./fangyan.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # 只为 SQLite 需要
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """FastAPI 依赖注入用的 DB 会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """创建所有表，并初始化单用户记录"""
    from app.models import Base, UserState
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        if not db.query(UserState).filter_by(id=1).first():
            db.add(UserState(id=1))
            db.commit()
            print("[DB] 初始化单用户记录")
    finally:
        db.close()
