# ===============================================
# 📁 File: core/pipeline.py (ĐÃ VÁ LỖI)
# -----------------------------------------------
# Vai trò: “Nhạc trưởng” điều phối toàn bộ hệ thống AI Mood Journal.
# ===============================================

# Giữ nguyên các import của bạn
from core.utils import get_vn_timestamp, normalize_sentiment 
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from datetime import datetime, timedelta, timezone
from core.hf_client import query_model
from core.config import CONF_THRESHOLD, DEFAULT_TONE


# ==========================================================
#  Hàm phụ của bạn (Giữ nguyên)
# ==========================================================
def format_pipeline_output(
    status: str,
    user_text: str,
    sentiment_label: str,
    sentiment_score: float,
    sentiment_model: str,
    response_text: str,
    response_source: str,
    timestamp: str
):
    """Đảm bảo output JSON thống nhất cho backend, frontend, và test"""
    return {
        "status": status,
        "input_text": user_text,
        "sentiment": {
            "label": sentiment_label,
            "score": round(sentiment_score, 3),
            "model": sentiment_model,
        },
        "response": {
            "text": response_text.strip().replace("\\n", "\n"),
            "source": response_source,
        },
        "timestamp": timestamp,
    }

# ==========================================================
#  Hàm chính: Pipeline AI (ĐÃ VÁ LỖI)
# ==========================================================
def run_ai_pipeline(user_text: str):
    """
    Pipeline chính cho AI Mood Journal.
    Nhận text → phân tích cảm xúc → sinh phản hồi → gộp JSON.
    """

    pipeline_start_time = get_vn_timestamp()

    # ------------------------------------------------------
    # BƯỚC 1: PHÂN TÍCH CẢM XÚC (Giữ nguyên)
    # ------------------------------------------------------
    sentiment_result = query_model("sentiment", user_text)

    if "error" in sentiment_result:
        return {
            "status": "error",
            "error_message": f"Sentiment model failed: {sentiment_result['error']}",
            "timestamp": pipeline_start_time,
        }

    sentiment_label = normalize_sentiment(sentiment_result.get("label", DEFAULT_TONE))
    sentiment_score = sentiment_result.get("score", 0.0)

    if sentiment_score < CONF_THRESHOLD:
        sentiment_label = DEFAULT_TONE

    # ------------------------------------------------------
    # BƯỚC 2: SINH PHẢN HỒI (ĐÂY LÀ PHẦN SỬA LỖI)
    # ------------------------------------------------------
    
    # XÓA BỎ prompt cũ bị lỗi của bạn.
    # THAY THẾ bằng prompt "sạch" (chỉ chứa dữ liệu).
    # Prompt này khớp 100% với những gì SYSTEM_PROMPT (v3)
    # đang "mong đợi" được nhận.
    prompt = f"""
Người dùng vừa chia sẻ: "{user_text}"
Kết quả phân tích cảm xúc của chúng tôi là: {sentiment_label} (với độ tin cậy {sentiment_score:.2f}).
Dựa vào thông tin này, hãy phản hồi họ.
"""
    
    # Giờ chúng ta gọi GPT với prompt "sạch"
    response_result = query_model("response", prompt)

    # (Phần xử lý lỗi response giữ nguyên)
    if "error" in response_result:
        return {
            "status": "error",
            "error_message": f"Response model failed: {response_result['error']}",
            "timestamp": pipeline_start_time,
            "sentiment_data": {"label": sentiment_label, "score": sentiment_score}
        }

    advice_text = response_result.get("text", "").strip() or \
        "Mình chưa biết nên nói gì lúc này, nhưng mình vẫn ở đây để lắng nghe bạn 🌿."
    advice_source = response_result.get("source", "student_mood_gpt")

    # ------------------------------------------------------
    # BƯỚC 3: GỘP KẾT QUẢ (Giữ nguyên)
    # ------------------------------------------------------
    
    return format_pipeline_output(
        status="success",
        user_text=user_text,
        sentiment_label=sentiment_label,
        sentiment_score=sentiment_score,
        sentiment_model=sentiment_result.get("model"),
        response_text=advice_text,
        response_source=advice_source,
        timestamp=pipeline_start_time
    )

# ==========================================================
#  Hàm in ấn (Giữ nguyên)
# ==========================================================
console = Console()
def print_pipeline_result(result: dict):
    if not result or result.get("status") != "success":
        console.print("[bold red] Pipeline lỗi hoặc không có kết quả hợp lệ![/bold red]")
        return
    user_text = result.get("input_text", "")
    sentiment = result.get("sentiment", {})
    response = result.get("response", {})
    timestamp = result.get("timestamp", "")
    table = Table(show_header=True, header_style="bold cyan", expand=True)
    table.add_column("Trường thông tin", justify="right", style="bold yellow")
    table.add_column("Giá trị", style="white")
    table.add_row(" Input", user_text)
    table.add_row(" Sentiment", f"{sentiment.get('label', '')} ({sentiment.get('score', 0):.2f})")
    table.add_row(" GPT Response", response.get("text", "").strip())
    table.add_row(" Model", str(sentiment.get("model", "")))
    table.add_row(" Timestamp", timestamp)
    console.print(Panel.fit(table, title="🧩 AI Mood Journal Pipeline Result", border_style="bold green"))