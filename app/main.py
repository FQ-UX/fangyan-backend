"""
方言互动 · FastAPI 主入口
"""
import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.db import init_db
from app.routers import progress, achievements, dict as dict_r, stories, game, chat, tts, asr, admin


app = FastAPI(
    title="方言互动 · 国风传承",
    description="计算机设计大赛作品 · 后端 API",
    version="1.0",
)


# ── CORS ───────────────────────────────────────────────────────────────
# 开发模式下允许所有源访问，便于本地前后端调试
if os.getenv("DEV_MODE", "true").lower() == "true":
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )


# ── 路由注册 ───────────────────────────────────────────────────────────
app.include_router(progress.router)
app.include_router(achievements.router)
app.include_router(dict_r.router)
app.include_router(stories.router)
app.include_router(game.router)
app.include_router(chat.router)
app.include_router(tts.router)
app.include_router(asr.router)
app.include_router(admin.router)


# ── 静态资源 ───────────────────────────────────────────────────────────
STATIC_DIR = Path(__file__).parent.parent / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def root():
    """根路径 → 返回前端 index.html"""
    index = STATIC_DIR / "index.html"
    if index.exists():
        return FileResponse(index)
    return {
        "name": "方言互动",
        "docs": "/docs",
        "hint": "前端 HTML 未放置在 static/ 目录。将 index.html 复制到 static/ 即可。",
    }


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/favicon.ico")
def favicon():
    """浏览器自动请求，返回 SVG favicon"""
    svg = STATIC_DIR / "favicon.svg"
    if svg.exists():
        return FileResponse(svg, media_type="image/svg+xml")
    # 万一 SVG 不存在返回透明 1x1 GIF 避免 404
    from fastapi.responses import Response
    return Response(
        content=bytes.fromhex("47494638396101000100800000ffffff00000021f90401000000002c00000000010001000002024401003b"),
        media_type="image/gif",
    )


@app.on_event("startup")
def on_startup():
    init_db()
    print("\n" + "=" * 60)
    print("  方言互动 · 国风传承  —  后端服务已启动")
    print("=" * 60)
    print("  前端地址:        http://127.0.0.1:8000/")
    print("  API 文档:        http://127.0.0.1:8000/docs")
    print("  系统统计:        http://127.0.0.1:8000/api/admin/stats")
    print("  方言分布:        http://127.0.0.1:8000/api/admin/dialect-distribution")
    print("  最近对话:        http://127.0.0.1:8000/api/admin/recent-chats")
    print("=" * 60 + "\n")
