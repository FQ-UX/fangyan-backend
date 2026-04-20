"""
阿里云通义 qwen3-omni-flash 服务封装
这个模型的特色：一次调用同时返回文字 + 方言语音（流式 SSE）
官方文档: https://help.aliyun.com/zh/model-studio/qwen-omni
"""
import os
import json
import httpx
from typing import List, Dict, Optional, Tuple

DASHSCOPE_KEY = os.getenv("DASHSCOPE_API_KEY", "")
DASHSCOPE_URL = os.getenv("DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
QWEN_OMNI_MODEL = os.getenv("QWEN_OMNI_MODEL", "qwen3-omni-flash")

# 方言 → 声音名映射
DIALECT_VOICE = {
    "普通话": "Cherry",
    "四川话": "Sunny",
    "广东话": "Rocky",
    "上海话": "Jada",
    "闽南语": "Roy",
    "北京话": "Dylan",
    "南京话": "Li",
    "陕西话": "Marcus",
    "天津话": "Peter",
}

# 每种方言的 Prompt 风格引导
DIALECT_PROMPTS = {
    "普通话": "请用标准普通话回答，自然亲切。",
    "四川话": "请用四川话回答，多用\"巴适\"\"要得\"\"嘛\"\"哇\"\"整\"\"安逸\"等词，语气热情。",
    "广东话": "请用广东话（粤语）回答，多用\"靓\"\"系\"\"唔\"\"嘅\"\"咁\"\"好正\"等词。",
    "上海话": "请用上海话回答，多用\"侬\"\"阿拉\"\"嗲\"\"伐\"\"蛮\"等词。",
    "闽南语": "请用闽南语回答，多用\"汝\"\"厝\"\"真\"\"好康\"等词。",
    "北京话": "请用北京话回答，加入儿化音和京味表达，多用\"得嘞\"\"甭\"\"劳驾\"\"门儿清\"等。",
    "南京话": "请用南京话回答，多用\"蛮好\"\"甩斯\"\"潘西\"\"韶\"等词。",
    "陕西话": "请用陕西话回答，多用\"美得很\"\"咋了\"\"撩咋咧\"\"额\"等词。",
    "天津话": "请用天津话回答，多用\"嘛\"\"倍儿\"\"结棍\"等词。",
}


def build_system_prompt(dialect: str, rag_hits: List[Dict] = None) -> str:
    style = DIALECT_PROMPTS.get(dialect, DIALECT_PROMPTS["普通话"])
    base = f"""你是"言小助"，一位友善的方言学习助手。当前方言：{dialect}。

{style}

回复要求：
- 用{dialect}的口吻和词汇自然回复
- 在方言特色词后用（）标注普通话含义
- 回复长度不超过 80 字
- 不要用 Markdown 格式、不要用 emoji
- 像朋友聊天一样亲切自然"""

    if rag_hits:
        snippets = "\n".join(
            f"  · {w['char']}（{w['pin']}）：{w['meaning']}"
            for w in rag_hits
        )
        base += f"\n\n## 参考词条（与用户问题相关）\n{snippets}"
    return base


async def chat_with_audio(
    dialect: str,
    history: List[Dict[str, str]],
    rag_hits: List[Dict] = None,
) -> Tuple[str, str]:
    """调用 qwen3-omni-flash，同时返回：文字回复 + base64 音频。
    失败时返回 ('', '')。
    """
    if not DASHSCOPE_KEY:
        return _fallback_reply(dialect), ""

    voice = DIALECT_VOICE.get(dialect, "Cherry")
    system_prompt = build_system_prompt(dialect, rag_hits)
    messages = [{"role": "system", "content": system_prompt}] + history

    payload = {
        "model": QWEN_OMNI_MODEL,
        "messages": messages,
        "stream": True,
        "modalities": ["text", "audio"],
        "audio": {"voice": voice, "format": "wav"},
    }

    text_reply = ""
    audio_b64 = ""

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream(
                "POST",
                f"{DASHSCOPE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {DASHSCOPE_KEY}",
                    "Content-Type": "application/json",
                },
                json=payload,
            ) as resp:
                if resp.status_code != 200:
                    err = await resp.aread()
                    print(f"[Qwen] HTTP {resp.status_code}: {err[:200]}")
                    return _fallback_reply(dialect), ""

                async for line in resp.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    payload_str = line[6:].strip()
                    if payload_str == "[DONE]":
                        break
                    try:
                        chunk = json.loads(payload_str)
                        delta = chunk.get("choices", [{}])[0].get("delta", {})
                        if delta.get("content"):
                            text_reply += delta["content"]
                        audio_delta = delta.get("audio", {})
                        if audio_delta.get("data"):
                            audio_b64 += audio_delta["data"]
                    except Exception:
                        continue
    except Exception as e:
        print(f"[Qwen] 请求异常: {e}")
        return _fallback_reply(dialect), ""

    if not text_reply:
        text_reply = _fallback_reply(dialect)
    return text_reply, audio_b64


async def tts_only(text: str, dialect: str) -> str:
    """仅合成语音（用于词典朗读、故事朗读等场景，不需要 AI 思考）。
    返回 base64 的 WAV 音频数据。空字符串表示失败。
    """
    if not DASHSCOPE_KEY or not text:
        return ""

    voice = DIALECT_VOICE.get(dialect, "Cherry")
    # 用 omni 模型，Prompt 直接让它朗读
    messages = [
        {
            "role": "user",
            "content": f"请直接朗读以下内容，不要添加任何额外文字：\n{text}",
        }
    ]

    payload = {
        "model": QWEN_OMNI_MODEL,
        "messages": messages,
        "stream": True,
        "modalities": ["text", "audio"],
        "audio": {"voice": voice, "format": "wav"},
    }

    audio_b64 = ""
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream(
                "POST",
                f"{DASHSCOPE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {DASHSCOPE_KEY}",
                    "Content-Type": "application/json",
                },
                json=payload,
            ) as resp:
                if resp.status_code != 200:
                    err = await resp.aread()
                    print(f"[Qwen-TTS] HTTP {resp.status_code}: {err[:200]}")
                    return ""

                async for line in resp.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    payload_str = line[6:].strip()
                    if payload_str == "[DONE]":
                        break
                    try:
                        chunk = json.loads(payload_str)
                        delta = chunk.get("choices", [{}])[0].get("delta", {})
                        audio_delta = delta.get("audio", {})
                        if audio_delta.get("data"):
                            audio_b64 += audio_delta["data"]
                    except Exception:
                        continue
    except Exception as e:
        print(f"[Qwen-TTS] 请求异常: {e}")
        return ""

    return audio_b64


def pcm_b64_to_wav_bytes(b64: str, sample_rate: int = 24000) -> bytes:
    """把 Qwen 返回的 base64 PCM 转成带 WAV 头的完整字节流。
    Qwen 的音频是 16bit mono 24000Hz 的裸 PCM。
    """
    import base64 as b64lib
    import struct

    if not b64:
        return b""

    pcm = b64lib.b64decode(b64)
    data_size = len(pcm)
    num_channels = 1
    bits_per_sample = 16
    byte_rate = sample_rate * num_channels * bits_per_sample // 8
    block_align = num_channels * bits_per_sample // 8

    header = (
        b"RIFF"
        + struct.pack("<I", 36 + data_size)
        + b"WAVE"
        + b"fmt "
        + struct.pack(
            "<IHHIIHH",
            16,
            1,
            num_channels,
            sample_rate,
            byte_rate,
            block_align,
            bits_per_sample,
        )
        + b"data"
        + struct.pack("<I", data_size)
    )
    return header + pcm


def _fallback_reply(dialect: str) -> str:
    """Qwen 不可用时的兜底回复"""
    replies = {
        "普通话": "你好！我是言小助，很高兴为你介绍方言知识。",
        "四川话": "巴适！欢迎来学四川话，我们一起整起！",
        "广东话": "你好！我哋一齐嚟学广东话啦，好唔好？",
        "上海话": "侬好！阿拉一道学上海话，蛮好个！",
        "闽南语": "汝好！一起来学闽南语，真趣味！",
        "北京话": "您好！咱聊聊北京话，门儿清！",
        "陕西话": "额给你说，学咱陕西话美得很！",
        "天津话": "嘛也甭说，咱今儿个就学津味儿！",
        "南京话": "蛮好嘞，一起来学南京话，韶韶子！",
    }
    return replies.get(dialect, replies["普通话"]) + "（AI 服务暂时不可用，正在使用本地回复）"


async def transcribe_audio(audio_base64: str, audio_format: str = "wav", dialect_hint: str = "四川话") -> str:
    """使用 qwen3-omni-flash 进行音频识别（ASR）。
    audio_base64: 音频文件的 base64（支持 wav/mp3/m4a 等）
    audio_format: 音频格式，默认 wav
    dialect_hint: 方言提示，会加入 prompt 指导识别
    返回：识别出的文字，失败返回空字符串
    """
    if not DASHSCOPE_KEY or not audio_base64:
        return ""

    # Qwen 要求音频大小有限制，且期望 base64 不带 data:xxx; 前缀
    # 构造 multi-modal 输入
    prompt_text = (
        f"这是一段{dialect_hint}录音。"
        f"请仔细聆听并转写其中的内容。"
        f"只输出识别出的汉字文本，不要任何其他说明、标点或解释。"
        f"如果听不清或是噪音，输出「无声」。"
    )

    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "input_audio",
                    "input_audio": {
                        "data": f"data:audio/{audio_format};base64,{audio_base64}",
                        "format": audio_format,
                    },
                },
                {"type": "text", "text": prompt_text},
            ],
        }
    ]

    # 按官方文档，音频输入必须用 stream=True
    payload = {
        "model": QWEN_OMNI_MODEL,
        "messages": messages,
        "stream": True,
        "modalities": ["text"],
    }

    text_result = ""
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream(
                "POST",
                f"{DASHSCOPE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {DASHSCOPE_KEY}",
                    "Content-Type": "application/json",
                },
                json=payload,
            ) as resp:
                if resp.status_code != 200:
                    err = await resp.aread()
                    print(f"[Qwen-ASR] HTTP {resp.status_code}: {err[:300]}")
                    return ""

                async for line in resp.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    payload_str = line[6:].strip()
                    if payload_str == "[DONE]":
                        break
                    try:
                        chunk = json.loads(payload_str)
                        delta = chunk.get("choices", [{}])[0].get("delta", {})
                        if delta.get("content"):
                            text_result += delta["content"]
                    except Exception:
                        continue
    except Exception as e:
        print(f"[Qwen-ASR] 请求异常: {e}")
        return ""

    return text_result.strip()
