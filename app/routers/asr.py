"""
发音评测 API —— 基于 qwen3-omni-flash 真实语音识别
"""
import base64
from fastapi import APIRouter, UploadFile, Form, File
from app.services.scorer import score_pronunciation
from app.services.qwen import transcribe_audio

router = APIRouter(prefix="/api/asr", tags=["asr"])


@router.post("/evaluate")
async def evaluate(
    reference: str = Form(...),
    dialect: str = Form("四川话"),
    audio: UploadFile = File(...),
):
    """
    接收用户录音（WAV）+ 参考文本，返回真实评分结果。
    评分流程：
      1. Qwen-Omni 识别录音 → 得到"用户实际说的文字"
      2. 和参考文本做字符级相似度比对（Levenshtein）
      3. 根据相似度 + 启发式规则映射到 0-100 分
    """
    data = await audio.read()
    result = await score_pronunciation(data, reference, dialect)
    return result


@router.post("/transcribe")
async def transcribe(
    dialect: str = Form("普通话"),
    audio: UploadFile = File(...),
):
    """
    只做识别，不打分 —— 对话页语音输入（模块 10）使用
    返回 {text: '识别出的文字'}
    """
    data = await audio.read()
    if len(data) < 1000:
        return {"text": "", "error": "audio_too_short"}
    if len(data) > 5 * 1024 * 1024:
        return {"text": "", "error": "audio_too_large"}

    audio_b64 = base64.b64encode(data).decode("ascii")
    text = await transcribe_audio(audio_b64, audio_format="wav", dialect_hint=dialect)
    # 去掉识别"无声"时的标记
    if text in ("无声", "「无声」"):
        text = ""
    return {"text": text}
