"""
history_engine.py
--------------------
Nhiệm vụ:
- Đây là “bộ não ghi nhớ lịch sử” của hệ thống.
- Trích xuất dữ liệu từ pipeline_history.json (HISTORY_DB_PATH)
- Lọc và tạo một đoạn context ngắn gọn cho LLM, để phục vụ:
    + Gợi ý hành động
    + Gợi ý thói quen
    + Phân tích lại ký ức tích cực/tiêu cực
"""

import json
from datetime import datetime
from core.config import HISTORY_DB_PATH


# ============================================================
# 1. Load toàn bộ lịch sử từ JSON
# ============================================================

def load_full_history():
    """
    Mở file pipeline_history.json và trả về dạng list.
    Nếu file chưa tồn tại → trả về list rỗng để không lỗi chương trình.

    Returns:
        list[dict]: danh sách các entry lịch sử mood.
    """
    try:
        with open(HISTORY_DB_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        # Khi chưa có dữ liệu — tránh crash
        return []


# ============================================================
# 2. Lọc lịch sử theo cảm xúc (label)
# ============================================================

def filter_history_by_label(history, label):
    """
    Lọc những entry có cùng cảm xúc (label) với user hiện tại.

    Args:
        history (list): toàn bộ lịch sử
        label (str): "positive" / "neutral" / "negative"

    Returns:
        list: các entry phù hợp
    """
    return [item for item in history if item.get("label") == label]


# ============================================================
# 3. Lấy ra số lượng ví dụ gần nhất (theo timestamp)
# ============================================================

def pick_recent_examples(history, max_examples=3):
    """
    Sắp xếp danh sách theo timestamp giảm dần → lấy n entry mới nhất.

    Args:
        history (list): list entry sau khi lọc label
        max_examples (int): số lượng entry cần lấy

    Returns:
        list: entry đã được chọn
    """

    # Dữ liệu timestamp có thể lỗi → dùng get() để tránh crash
    sorted_items = sorted(
        history,
        key=lambda x: x.get("timestamp", ""),
        reverse=True
    )

    return sorted_items[:max_examples]


# ============================================================
# 4. Chuyển example → thành 1 đoạn text ngắn cho LLM
# ============================================================

def format_context(examples):
    """
    Convert list example thành text dạng bullet:
        - [2025-11-20 10:22] Hôm nay mình nghe nhạc thấy thoải mái hơn.

    Args:
        examples (list)

    Returns:
        str
    """
    lines = []

    for ex in examples:
        ts = ex.get("timestamp", "unknown time")
        text = ex.get("text", "")
        lines.append(f"- [{ts}] {text}")

    return "\n".join(lines)


# ============================================================
# 5. Hàm chính build context — Hệ thống sẽ gọi hàm này
# ============================================================

def build_past_context(current_label, case_type, user_id=None, max_examples=3):
    """
    Đây là hàm cốt lõi.
    Dùng để lấy ra “kí ức gần nhất” theo cảm xúc user đang có.

    Args:
        current_label (str): cảm xúc người dùng hiện tại
        case_type (str): để mở rộng trong tương lai (vd: case stress, case success…)
        user_id: khi bạn làm multi-user
        max_examples: lấy bao nhiêu ví dụ

    Returns:
        str: đoạn context ngắn gọn đưa vào prompt LLM
    """

    # 1) Load toàn bộ lịch sử
    history = load_full_history()

    # 2) Lọc theo cảm xúc cần tìm
    filtered = filter_history_by_label(history, current_label)

    # 3) Chọn n entry gần nhất
    picked = pick_recent_examples(filtered, max_examples)

    # 4) Format lại thành đoạn text
    context = format_context(picked)

    return context
