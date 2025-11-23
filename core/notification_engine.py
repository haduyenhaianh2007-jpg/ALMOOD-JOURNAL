# notification_engine.py
# Engine xử lý thông báo thông minh theo 4 loại: A, B, C, D
# ---------------------------------------------------------
# A – Emotion-Aware Notifications
# B – Task-Aware Notifications
# C – Success-Pattern Notifications
# D – Weekly/Monthly Summary Notifications
# ---------------------------------------------------------
# File này đóng vai trò trung tâm của hệ thống thông báo.
# Mỗi hàm đều có comment chi tiết để cậu dễ tích hợp vào pipeline.

import datetime
from typing import List, Dict, Optional, Any

# ---------------------------------------------------------
# IMPORT CÁC ENGINE LIÊN QUAN
# ---------------------------------------------------------
# history_engine: đọc lịch sử cảm xúc, mood trend, pattern
# todo_engine: lấy các task còn hạn, task stress, deadline
# (Giả sử 2 module này đã có trong core như mô tả của cậu)
# ---------------------------------------------------------

from core.history_engine import (
    load_full_history,
    get_recent_mood_trend,
    get_success_patterns,
    get_last_entry_time,
)

from core.todo_engine import (
    get_upcoming_tasks,
    get_tasks_due_soon,
    get_overdue_tasks,
)

# ---------------------------------------------------------
# CÁC RULE DÙNG CHUNG (tách riêng để dễ chỉnh sửa)
# ---------------------------------------------------------

from core.notification_rules import RULES


# ---------------------------------------------------------
# HÀM TIỆN ÍCH
# ---------------------------------------------------------

def now():
    return datetime.datetime.now()

# Tạo object notification trả về pipeline

def build_notification(ntype: str, message: str, reason: str) -> Dict[str, Any]:
    return {
        "type": ntype,
        "message": message,
        "reason": reason,
        "created_at": now().strftime("%Y-%m-%d %H:%M:%S"),
        "source": "notification_engine",
    }

# ---------------------------------------------------------
# A – EMOTION-AWARE NOTIFICATION
# ---------------------------------------------------------

def check_emotion_notification() -> Optional[Dict[str, Any]]:
    """
    Gửi thông báo khi:
    - mood giảm liên tục RULES["emotion_drop_days"] ngày
    - user lâu không ghi nhật ký (no_journal_hours)
    """
    history = load_full_history()
    if not history:
        return None

    # 1) Mood trend check
    mood_trend = get_recent_mood_trend(history, days=RULES["emotion_drop_days"])
    if mood_trend and all(m == "negative" for m in mood_trend):
        return build_notification(
            "EMOTION_ALERT",
            "Dạo gần đây cậu có vẻ hơi mệt và tiêu cực. Mình ở đây nếu cậu muốn kể thêm nhé.",
            reason="mood_drop_multiple_days"
        )

    # 2) No journal too long
    last_time = get_last_entry_time(history)
    if last_time:
        hours_passed = (now() - last_time).total_seconds() / 3600
        if hours_passed > RULES["no_journal_hours"]:
            return build_notification(
                "EMOTION_REMINDER",
                "Lâu rồi cậu chưa ghi cảm xúc. Viết vài dòng giúp cậu dễ chịu hơn đấy.",
                reason="no_journal_long_time"
            )

    return None

# ---------------------------------------------------------
# B – TASK-AWARE NOTIFICATION
# ---------------------------------------------------------

def check_task_notification() -> Optional[Dict[str, Any]]:
    """
    Gửi thông báo dựa trên:
    - task sắp đến hạn trong RULES["deadline_hours"]
    - task đã quá hạn
    """
    due_soon = get_tasks_due_soon(hours=RULES["deadline_hours"])
    if due_soon:
        task = due_soon[0]
        msg = f"Nhiệm vụ '{task['action']}' sắp đến hạn. Muốn mình chia nhỏ giúp cậu bắt đầu nhẹ nhàng không?"
        return build_notification("TASK_DEADLINE", msg, reason="deadline_coming")

    overdue = get_overdue_tasks()
    if overdue:
        task = overdue[0]
        msg = f"Nhiệm vụ '{task['action']}' đã quá hạn một chút. Ta làm 5 phút để giảm áp lực nhé?"
        return build_notification("TASK_OVERDUE", msg, reason="task_overdue")

    return None

# ---------------------------------------------------------
# C – SUCCESS-PATTERN NOTIFICATION
# ---------------------------------------------------------

def check_success_pattern_notification() -> Optional[Dict[str, Any]]:
    """
    Gợi ý thói quen từng giúp user cải thiện mood.
    """
    patterns = get_success_patterns(days=RULES["success_pattern_days"])
    if not patterns:
        return None

    best = patterns[0]  # lấy thói quen hiệu quả nhất
    msg = (
        f"Lần trước cậu '{best['activity']}' và mood cải thiện rõ rệt. Muốn thử lại không?"
    )
    return build_notification("SUCCESS_REINFORCE", msg, reason="success_pattern_match")

# ---------------------------------------------------------
# D – WEEKLY / MONTHLY SUMMARY
# ---------------------------------------------------------

def check_summary_notification() -> Optional[Dict[str, Any]]:
    """
    - Chủ nhật → tổng kết tuần
    - Ngày 1 tháng → tổng kết tháng
    """
    today = now()

    # Weekly summary
    if today.weekday() == RULES["weekly_summary_day"]:
        return build_notification(
            "WEEKLY_SUMMARY",
            "Đây là tổng kết tuần của cậu. Muốn xem phân tích chi tiết không?",
            reason="weekly_auto"
        )

    # Monthly summary
    if today.day == RULES["monthly_summary_day"]:
        return build_notification(
            "MONTHLY_SUMMARY",
            "Đã đến lúc tổng kết tháng rồi. Cậu muốn xem lại hành trình cảm xúc tháng này không?",
            reason="monthly_auto"
        )

    return None

# ---------------------------------------------------------
# HÀM TỔNG – GỌI TỪ PIPELINE
# ---------------------------------------------------------

def generate_notification() -> Optional[Dict[str, Any]]:
    """
    Thử lần lượt A → B → C → D.
    Chỉ gửi 1 thông báo/lần để tránh spam.
    """
    # A – Emotion
    n = check_emotion_notification()
    if n:
        return n

    # B – Task
    n = check_task_notification()
    if n:
        return n

    # C – Success pattern
    n = check_success_pattern_notification()
    if n:
        return n

    # D – Summary
    n = check_summary_notification()
    if n:
        return n

    return None
