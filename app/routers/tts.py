"""
TTS API (模块 3 词典朗读 + 模块 4 故事朗读会用)
使用阿里云 qwen3-omni-flash 合成方言语音
带磁盘缓存：相同 text + dialect 只合成一次
"""
import os
import hashlib
from pathlib import Path
from fastapi import APIRouter, Response
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.services.qwen import tts_only, pcm_b64_to_wav_bytes, DIALECT_VOICE

router = APIRouter(prefix="/api/tts", tags=["tts"])

CACHE_DIR = Path(os.getenv("AUDIO_CACHE_DIR", "./audio_cache"))
CACHE_DIR.mkdir(parents=True, exist_ok=True)


class TTSRequest(BaseModel):
    text: str
    dialect: str = "普通话"


@router.post("")
async def tts_synthesize(req: TTSRequest):
    """合成指定文本和方言的语音，返回 WAV。
    基于 (text, dialect) 做缓存，重复调用秒回。
    """
    if not req.text or not req.text.strip():
        return Response(content=b"empty text", status_code=400)

    text = req.text.strip()[:300]
    print(f"[TTS] Request: dialect={req.dialect} text={text[:30]}...")

    key = hashlib.md5(f"qwen:{req.dialect}:{text}".encode("utf-8")).hexdigest()
    cache_path = CACHE_DIR / f"{key}.wav"

    if cache_path.exists() and cache_path.stat().st_size > 100:
        print(f"[TTS] Cache hit: {cache_path.name} ({cache_path.stat().st_size} bytes)")
        return FileResponse(cache_path, media_type="audio/wav")

    audio_b64 = await tts_only(text, req.dialect)
    if not audio_b64:
        print(f"[TTS] FAILED: got empty audio from Qwen. Check DASHSCOPE_API_KEY in .env")
        return Response(
            content=b"TTS service unavailable",
            status_code=503,
            media_type="text/plain",
        )

    wav_bytes = pcm_b64_to_wav_bytes(audio_b64, sample_rate=24000)
    if not wav_bytes:
        print(f"[TTS] FAILED: got audio_b64 but pcm_b64_to_wav_bytes returned empty")
        return Response(content=b"empty audio", status_code=500)

    cache_path.write_bytes(wav_bytes)
    print(f"[TTS] Synthesized: {len(wav_bytes)} bytes cached to {cache_path.name}")
    return FileResponse(cache_path, media_type="audio/wav")


@router.get("/voices")
def list_voices():
    """列出所有方言及对应声音名（前端展示用）"""
    return {
        "voices": [
            {"dialect": d, "voice": v}
            for d, v in DIALECT_VOICE.items()
        ]
    }
