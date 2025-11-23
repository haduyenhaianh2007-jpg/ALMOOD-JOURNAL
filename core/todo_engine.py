# core/todo_engine.py
# ============================================================
#  To-Do Engine (Rule-based version)
#  - Trích nhiệm vụ từ nhật ký
#  - Dò deadline
#  - Chuẩn bị dữ liệu cho Notification Engine
# ============================================================
from datetime import datetime, timedelta
import re
from dataclasses import dataclass
from typing import List, Optional, Dict, Any


# ============================================================
# 1. DATA CLASS CHUẨN CHO 1 NHIỆM VỤ
# ============================================================
@dataclass
class TodoCandidate:
    action: str                # việc cần làm
    description: str           # mô tả ngắn
    source_text: str           # câu user nói
    confidence: float          # độ tự tin rule-based
    context_tags: List[str]    # từ khóa
    deadline: Optional[str] = None   # deadline dạng string (“mai”, “thứ 3”, …)


# ============================================================
# 2. TRÍCH NHIỆM VỤ TỪ TEXT (RULE-BASED)
# ============================================================
def extract_tasks_from_text(text: str, context_tags: Optional[List[str]] = None) -> List[TodoCandidate]:
    """
    Rule-based V1 → chỉ để chạy ngay.
    Sau này có thể nâng cấp bằng LLM.
    """
    text_low = text.lower()
    cands: List[TodoCandidate] = []

    # ---------- Rule 1: Thi cử ----------
    if "thi" in text_low:
        cands.append(
            TodoCandidate(
                action="Ôn bài thi",
                description="Ôn 1 chương hoặc làm 1 đề ngắn.",
                source_text=text,
                confidence=0.7,
                context_tags=(context_tags or []) + ["thi_cu"],
                deadline=detect_deadline(text),
            )
        )

    # ---------- Rule 2: Thuyết trình ----------
    if "slide" in text_low or "thuyết trình" in text_low or "presentation" in text_low:
        cands.append(
            TodoCandidate(
                action="Làm slide thuyết trình",
                description="Chuẩn bị dàn ý + intro.",
                source_text=text,
                confidence=0.75,
                context_tags=(context_tags or []) + ["slide", "presentation"],
                deadline=detect_deadline(text),
            )
        )

    # ---------- Rule 3: Deadline ----------
    if "deadline" in text_low or "nộp" in text_low:
        cands.append(
            TodoCandidate(
                action="Hoàn thành bài tập/đồ án",
                description="Làm 1 phần nhỏ trước.",
                source_text=text,
                confidence=0.8,
                context_tags=(context_tags or []) + ["deadline"],
                deadline=detect_deadline(text),
            )
        )

    return cands


# ============================================================
# 3. HỎI USER THEO KIỂU NHẸ NHÀNG
# ============================================================
def generate_gentle_question(task: TodoCandidate) -> str:
    return (
        f"Nghe có vẻ nhiệm vụ **{task.action}** hơi lớn ha…\n"
        f"Nếu chia thành vài bước nhỏ thì có thể đỡ áp lực hơn.\n"
        f"Cậu muốn tớ gợi ý thử không?"
    )


# ============================================================
# 4. PHÁT HIỆN DEADLINE ĐƠN GIẢN TỪ TEXT
# ============================================================
def detect_deadline(text: str) -> Optional[str]:
    """
    V1: Regex đơn giản để nhận diện các deadline gần.
    """
    t = text.lower()

    if "mai" in t:
        return "mai"

    if "tối nay" in t or "hôm nay" in t:
        return "hôm nay"

    m = re.search(r"thứ\s*(\d+)", t)
    if m:
        return f"thứ {m.group(1)}"

    return None


# ============================================================
# 5. TỪ LỊCH SỬ (pipeline_history.json) → tìm nhiệm vụ sắp đến hạn
# ============================================================
def get_upcoming_tasks(history: List[Dict[str, Any]]) -> List[TodoCandidate]:
    """
    Input: lịch sử pipeline (list dict)
    Output: list nhiệm vụ có deadline (cho notification A,B,C,D)
    """
    results: List[TodoCandidate] = []

    for item in history:
        text = item.get("text", "").lower()

        # → dùng lại extract_tasks_from_text
        tasks = extract_tasks_from_text(text)

        for t in tasks:
            if t.deadline:       # chỉ lấy tasks có deadline
                results.append(t)

    return results
# ============================================================
# 6. TASK SẮP ĐẾN HẠN (Deadline Soon)
# ============================================================
def get_tasks_due_soon(history, hours=24):
    """
    Tìm các task có deadline nằm trong vòng X giờ tới.
    Vì deadline đang ở dạng 'mai', 'hôm nay', 'thứ 3',
    ta convert về dạng datetime đơn giản.
    """
    results = []
    now = datetime.now()

    for item in history:
        text = item.get("text", "")
        tasks = extract_tasks_from_text(text)

        for t in tasks:
            if not t.deadline:
                continue

            # Convert deadline text -> datetime (version đơn giản)
            dl = convert_deadline_to_datetime(t.deadline)

            if dl is None:
                continue

            diff_hours = (dl - now).total_seconds() / 3600
            if 0 < diff_hours <= hours:
                results.append(t)

    return results


# ============================================================
# 7. TASK ĐÃ QUÁ HẠN
# ============================================================
def get_overdue_tasks(history):
    """
    Tìm các task đã quá hạn (deadline < now).
    """
    results = []
    now = datetime.now()

    for item in history:
        text = item.get("text", "")
        tasks = extract_tasks_from_text(text)

        for t in tasks:
            if not t.deadline:
                continue

            dl = convert_deadline_to_datetime(t.deadline)

            if dl is None:
                continue

            if dl < now:
                results.append(t)

    return results


# ============================================================
# 8. Chuyển deadline dạng chữ → datetime
# ============================================================
def convert_deadline_to_datetime(deadline_str: str):
    """
    Ví dụ:
    - 'hôm nay'
    - 'tối nay'
    - 'mai'
    - 'thứ 3'
    
    Convert sang datetime để so sánh deadline.
    """
    now = datetime.now()
    dl = deadline_str.lower()

    # hôm nay
    if dl in ["hôm nay", "tối nay"]:
        return now.replace(hour=23, minute=59, second=0)

    # mai
    if dl == "mai":
        return now + timedelta(days=1)

    # thứ X
    m = re.search(r"thứ\\s*(\\d+)", dl)
    if m:
        target = int(m.group(1))
        today = now.weekday() + 2  # weekday(): Mon=0 → Thứ 2=2
        diff = (target - today) % 7
        if diff == 0:
            diff = 7
        return now + timedelta(days=diff)

    return None
