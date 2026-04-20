"""
简易 RAG 检索：从词典中找出与用户问题相关的方言词条
"""
from typing import List, Dict

# 模块级缓存，避免每次调用都重新加载
_WORDS_CACHE = None


def _load_words() -> List[Dict]:
    global _WORDS_CACHE
    if _WORDS_CACHE is None:
        import json
        from pathlib import Path
        p = Path(__file__).parent.parent / "data" / "data_WORDS.json"
        with open(p, "r", encoding="utf-8") as f:
            _WORDS_CACHE = json.load(f)
    return _WORDS_CACHE


def retrieve_words(query: str, dialect: str = None, top_k: int = 3) -> List[Dict]:
    """根据用户查询文本，检索相关方言词条。
    检索策略（按优先级）：
    1. 字面命中（用户问题包含词条的 char 或 meaning）
    2. 方言过滤（若指定了 dialect，优先返回该方言的词）
    """
    words = _load_words()
    hits = []

    for w in words:
        score = 0
        # 字面命中
        if w["char"] in query:
            score += 10
        if any(ch in query for ch in w["char"]):
            score += 3
        # meaning 关键词命中
        for keyword in w["meaning"].split("，"):
            if keyword.strip() and keyword.strip() in query:
                score += 5
        # 方言匹配加权
        if dialect and dialect != "普通话" and w["dialect"] == dialect:
            score += 2
        if score > 0:
            hits.append((score, w))

    hits.sort(key=lambda x: -x[0])
    return [h[1] for h in hits[:top_k]]
