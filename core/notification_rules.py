# notification_rules.py
# ---------------------------------------------------------
# Chứa toàn bộ rule cấu hình cho hệ thống Notification Engine.
# Đây là nơi tập trung các con số, thời gian, tần suất...
# để dễ chỉnh sửa mà không cần chạm vào logic của engine.
# ---------------------------------------------------------

RULES = {
    # -----------------------------------------------------
    # A – EMOTION-AWARE NOTIFICATIONS
    # -----------------------------------------------------
    # Mood giảm liên tục bao nhiêu ngày thì gửi cảnh báo cảm xúc?
    "emotion_drop_days": 3,

    # Bao nhiêu giờ không ghi nhật ký thì nhắc nhở?
    "no_journal_hours": 36,  # 1.5 ngày

    # -----------------------------------------------------
    # B – TASK-AWARE NOTIFICATIONS
    # -----------------------------------------------------
    # Task còn bao nhiêu giờ đến deadline thì nhắc?
    "deadline_hours": 24,

    # -----------------------------------------------------
    # C – SUCCESS-PATTERN NOTIFICATIONS
    # -----------------------------------------------------
    # Sau bao nhiêu ngày nên nhắc lại thói quen từng giúp user tốt hơn?
    "success_pattern_days": 7,

    # -----------------------------------------------------
    # D – SUMMARY NOTIFICATIONS
    # -----------------------------------------------------
    # Weekly summary: gửi vào ngày nào?
    # weekday() → 0=Mon … 6=Sun, nên Chủ Nhật là 6.
    "weekly_summary_day": 6,

    # Monthly summary: gửi vào ngày số mấy?
    "monthly_summary_day": 1,
}