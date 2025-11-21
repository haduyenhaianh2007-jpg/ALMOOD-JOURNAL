# core/history_engine.py
# Module: Đọc lại history → tạo BỐI CẢNH QUÁ KHỨ cho LLM
# Dùng cùng với pipeline.py v4.0

from __future__ import annotations

import json
import os
from datetime import datetime
from typing import List, Dict, Optional

# File lịch sử mà pipeline.py đang ghi
HISTORY_PATH = "pipeline_history.json"


def _parse_ts(value: str) -> datetime:
    """
    Parse timestamp từ chuỗi trong history.
    Pipeline đang dùng format: 'YYYY-MM-DD HH:MM:SS'.
    Nếu lỗi thì trả về datetime.min để sort không bị crash.
    """
    try:
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
    except Exception:
        return datetime.min


def _load_history(
    max_records: int = 200,
    user_id: Optional[str] = None,
) -> List[Dict]:
    """
    Đọc lịch sử từ pipeline_history.json.
    Trả về list các bản ghi mới nhất (đã sort theo thời gian giảm dần).
    Nếu có user_id trong record thì filter theo user_id (nếu truyền vào).
    """
    if not os.path.exists(HISTORY_PATH):
        return []

    try:
        with open(HISTORY_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return []

    if not isinstance(data, list):
        return []

    # Lọc theo user_id nếu field này tồn tại trong dữ liệu
    if user_id is not None:
        filtered = []
        for rec in data:
            rec_uid = rec.get("user_id")
            # Nếu history chưa có user_id thì giữ lại tất cả
            if rec_uid is None or rec_uid == user_id:
                filtered.append(rec)
        data = filtered

    # Sort theo timestamp mới → cũ
    data_sorted = sorted(
        data,
        key=lambda r: _parse_ts(r.get("timestamp", "")),
        reverse=True,
    )

    return data_sorted[:max_records]


def _shorten(text: str, max_len: int = 80) -> str:
    """
    Cắt ngắn text để đưa vào prompt cho gọn.
    """
    text = (text or "").strip().replace("\n", " ")
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def build_past_context(
    current_label: str,
    case_type: str,
    user_id: Optional[str] = None,
    max_examples: int = 3,
) -> str:
    """
    Tạo đoạn 'BỐI CẢNH QUÁ KHỨ' để nhét vào prompt gửi LLM.

    current_label:  nhãn cảm xúc hiện tại ('negative' / 'neutral' / 'positive')
    case_type:      case do detect_sentiment_case trả về (consistent / mild_shift / ...)
    user_id:        nếu có multi-user, truyền vào để chỉ đọc history của user đó
    """
    history = _load_history(max_records=200, user_id=user_id)
    if not history:
        return "Chưa có nhiều dữ liệu nhật ký cũ giống tình huống này."

    good_labels = {"positive", "neutral"}

    candidates: List[Dict] = []
    for rec in history:
        # 1. Bối cảnh tương tự
        same_case = rec.get("case_type") == case_type

        # 2. Nếu hiện tại đang negative → ta quan tâm các lần kết thúc ở positive/neutral
        if current_label == "negative":
            mood_ok = rec.get("predicted_label") in good_labels
        else:
            # trường hợp khác: chỉ cần cùng “họ” cảm xúc
            mood_ok = True

        if same_case and mood_ok:
            candidates.append(rec)

    if not candidates:
        return "Hiện tại chưa tìm thấy lần tương tự nào trong nhật ký cũ."

    # Lấy vài ví dụ mới nhất
    examples = candidates[:max_examples]

    lines: List[str] = []
    for rec in examples:
        ts = rec.get("timestamp", "")
        txt = _shorten(rec.get("text", ""))
        label = rec.get("predicted_label", "")
        detail = rec.get("emotion_detail", "")
        line = f"- {ts}: \"{txt}\" (cảm xúc lúc đó: {label}, chi tiết: {detail})"
        lines.append(line)

    context_text = (
        "Trong nhật ký cũ, đã có một vài lần bạn ở trạng thái gần giống như bây giờ "
        "và sau đó tâm trạng đã thay đổi như sau:\n"
        + "\n".join(lines)
    )

    return context_text
