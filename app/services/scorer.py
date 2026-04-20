"""
方言发音评分器 v2 —— 基于 Qwen-Omni 真实语音识别

流程：
1. 接收用户 WAV 音频（base64）
2. 调 qwen3-omni-flash 识别出用户实际说的内容
3. 和参考文本做字符级相似度比对
4. 根据相似度 + 识别置信度给出 0-100 分

相比假打分器，这是真的：
  - 不说话 → 识别空 → 低分
  - 说错话 → 字符不匹配 → 低分
  - 说对话 → 字符匹配 → 高分
"""
import base64
from typing import Tuple

from app.services.qwen import transcribe_audio


def clean_text(s: str) -> str:
    """清洗文字：去掉标点、空格、引号，只保留汉字和字母"""
    out = []
    for ch in s:
        if '\u4e00' <= ch <= '\u9fff':
            out.append(ch)
        elif ch.isalpha() or ch.isdigit():
            out.append(ch.lower())
    return "".join(out)


def char_similarity(hyp: str, ref: str) -> Tuple[float, int, int, int]:
    """字符级相似度（Levenshtein 距离）
    返回 (相似度 0-1, 正确字符数, 总字符数, 编辑距离)
    """
    hyp = clean_text(hyp)
    ref = clean_text(ref)
    if not ref:
        return 0.0, 0, 0, 0
    if not hyp:
        return 0.0, 0, len(ref), len(ref)

    # Levenshtein 距离
    m, n = len(hyp), len(ref)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if hyp[i-1] == ref[j-1]:
                dp[i][j] = dp[i-1][j-1]
            else:
                dp[i][j] = 1 + min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1])

    distance = dp[m][n]
    max_len = max(m, n)
    similarity = 1 - distance / max_len if max_len > 0 else 0

    # 计算正确字符数（LCS 近似）
    correct = max(0, n - distance)
    return similarity, correct, n, distance


async def score_pronunciation(
    wav_bytes: bytes,
    reference_text: str,
    dialect: str = "四川话",
) -> dict:
    """核心入口：给一段录音打分。
    wav_bytes: WAV 格式的音频字节
    reference_text: 用户应该朗读的标准文本
    dialect: 方言类型
    """

    # 基础校验
    if len(wav_bytes) < 1000:
        return {
            "score": 0,
            "grade": "无效",
            "feedback": "录音太短或损坏，请重新录制",
            "details": {"recognized": "", "reference": reference_text, "reason": "too_short"},
        }

    if len(wav_bytes) > 5 * 1024 * 1024:  # 5MB
        return {
            "score": 30,
            "grade": "太长",
            "feedback": "录音太长，请只朗读目标短语",
            "details": {"recognized": "", "reference": reference_text, "reason": "too_long"},
        }

    # 调 Qwen 识别
    audio_b64 = base64.b64encode(wav_bytes).decode("ascii")
    print(f"[Scorer] 调用 Qwen-ASR 识别...音频大小 {len(wav_bytes)} 字节")

    recognized = await transcribe_audio(audio_b64, audio_format="wav", dialect_hint=dialect)
    print(f"[Scorer] Qwen 识别结果: '{recognized}' vs 参考: '{reference_text}'")

    # 识别失败兜底
    if not recognized or recognized in ("无声", "「无声」", ""):
        return {
            "score": 35,
            "grade": "未识别",
            "feedback": "没有识别到清晰的人声，请靠近麦克风大声朗读",
            "details": {
                "recognized": recognized,
                "reference": reference_text,
                "reason": "no_speech_detected",
            },
        }

    # 相似度计算
    similarity, correct_chars, total_chars, edit_distance = char_similarity(
        recognized, reference_text
    )

    # 评分映射：相似度 → 分数
    # 完全匹配 = 95-100（留一点空间不给满分避免看起来假）
    # 80%+ = 85-94 优秀
    # 60-80% = 75-84 良好
    # 40-60% = 65-74 中等
    # 20-40% = 55-64 加油
    # <20% = 40-55 不及格

    if similarity >= 1.0:
        score = 95
    elif similarity >= 0.9:
        score = 88 + int((similarity - 0.9) * 70)
    elif similarity >= 0.75:
        score = 80 + int((similarity - 0.75) * 53)
    elif similarity >= 0.6:
        score = 72 + int((similarity - 0.6) * 53)
    elif similarity >= 0.4:
        score = 62 + int((similarity - 0.4) * 50)
    elif similarity >= 0.2:
        score = 52 + int((similarity - 0.2) * 50)
    else:
        score = 40 + int(similarity * 60)

    # 等级
    if score >= 90:
        grade = "优秀"
    elif score >= 80:
        grade = "良好"
    elif score >= 70:
        grade = "中等"
    elif score >= 60:
        grade = "加油"
    else:
        grade = "再练"

    # 反馈语
    feedback = _build_feedback(
        recognized, reference_text, similarity, correct_chars, total_chars
    )

    return {
        "score": score,
        "grade": grade,
        "feedback": feedback,
        "details": {
            "recognized": recognized,
            "reference": reference_text,
            "similarity": round(similarity, 3),
            "correct_chars": correct_chars,
            "total_chars": total_chars,
            "edit_distance": edit_distance,
        },
    }


def _build_feedback(hyp: str, ref: str, sim: float, correct: int, total: int) -> str:
    """根据比对结果生成人性化的反馈"""
    hyp_clean = clean_text(hyp)
    ref_clean = clean_text(ref)

    if sim >= 1.0:
        return f"🎉 完美！标准读音「{ref}」，你读得和标准完全一致！"

    if sim >= 0.9:
        return f"👍 非常棒！识别结果：「{hyp}」，几乎和标准一致。"

    if sim >= 0.75:
        # 找出哪里错了
        diff = _find_diff_chars(hyp_clean, ref_clean)
        if diff:
            return f"不错！识别出「{hyp}」。注意「{diff}」这几个字的发音，再试试。"
        return f"不错！识别出「{hyp}」。个别字发音略有出入，多练几次会更好。"

    if sim >= 0.5:
        return f"有进步！识别出「{hyp}」。发音还不够准，建议先听标准朗读再跟读。"

    if sim >= 0.2:
        return f"识别出的是「{hyp}」，和「{ref}」差距较大。请放慢语速，每个字清晰朗读。"

    return f"识别结果「{hyp}」与标准「{ref}」差异较大。请确认朗读的是「{ref}」，靠近麦克风。"


def _find_diff_chars(hyp: str, ref: str) -> str:
    """找出 ref 中哪些字没在 hyp 里出现"""
    missing = []
    for ch in ref:
        if ch not in hyp:
            missing.append(ch)
    return "".join(missing[:3])  # 最多返回 3 个
