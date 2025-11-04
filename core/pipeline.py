# ===============================================
# 📁 File: core/pipeline.py (v2 - Cải tiến "Trí nhớ" + 2-Model)
# -----------------------------------------------
# Vai trò: “Nhạc trưởng” điều phối
# ===============================================

from core.utils import get_vn_timestamp, normalize_sentiment 
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from datetime import datetime, timedelta, timezone
from core.hf_client import query_model
from core.config import CONF_THRESHOLD, DEFAULT_TONE

# === (CẢI TIẾN) KHỐI 2: HÀM MỚI (Mô phỏng Backend/DB) ===
def _get_user_history_summary(user_id: str) -> str:
    """
    (CHỨC NĂNG MÔ PHỎNG - Team Backend (An) sẽ triển khai thật)
    Truy vấn CSDL, lấy 3 nhật ký gần nhất của "user_id"
    Đây chính là "bối cảnh quá khứ" (state)
    """
    # (Tạm thời trả về data giả định)
    if user_id == "test_user_01": # (Dành cho test case)
        return "Tóm tắt bối cảnh quá khứ của người dùng:\n- 2025-11-03: Cảm xúc (positive).\n- 2025-11-02: Cảm xúc (negative)."
    return "Đây là lần đầu tiên người dùng chia sẻ."

# === (CẢI TIẾN) KHỐI 3: HÀM PHỤ (Thêm emotion_label) ===
def format_pipeline_output(
    status: str,
    user_text: str,
    sentiment_label: str,
    sentiment_score: float,
    sentiment_model: str,
    emotion_label: str, # <-- CẢI TIẾN
    response_text: str,
    response_source: str,
    timestamp: str
):
    return {
        "status": status,
        "input_text": user_text,
        "sentiment": {
            "label": sentiment_label,
            "score": round(sentiment_score, 3),
            "model": sentiment_model,
            "emotion_detail": emotion_label # <-- CẢI TIẾN
        },
        "response": {"text": response_text, "source": response_source,},
        "timestamp": timestamp,
    }

# === (CẢI TIẾN) KHỐI 4: HÀM CHÍNH (Pipeline v2) ===
def run_ai_pipeline(user_text: str, user_id: str = "default_user"):
    """
    Pipeline chính (v2 - Có "Trí nhớ" và 2 Model)
    """
    pipeline_start_time = get_vn_timestamp()
    emotion_label = None # Biến mới

    # --- BƯỚC 1: PHÂN TÍCH CẢM XÚC CHÍNH (MODEL 1) ---
    sentiment_result = query_model("sentiment", user_text) # Gọi API "tối ưu" của bạn

    if "error" in sentiment_result:
        return {"status": "error", "error_message": f"Sentiment model failed: {sentiment_result['error']}", "timestamp": pipeline_start_time,}

    sentiment_label = normalize_sentiment(sentiment_result.get("label", DEFAULT_TONE))
    sentiment_score = sentiment_result.get("score", 0.0)

    if sentiment_score < CONF_THRESHOLD:
        sentiment_label = DEFAULT_TONE

    # --- BƯỚC 2: PHÂN TÍCH CẢM XÚC CHI TIẾT (MODEL 2) (Cải tiến) ---
    # (Flow tối ưu: Chỉ gọi Model 2 nếu không phải là 'neutral')
    if sentiment_label in ["positive", "negative"]:
        emotion_result = query_model("sentiment_detail", user_text) # <-- Gọi Model 2
        
        if "error" not in emotion_result:
            emotion_label = emotion_result.get("label") 

    # --- BƯỚC 3: TẢI BỐI CẢNH (STATE) (Cải tiến) ---
    history_summary = _get_user_history_summary(user_id)

    # --- BƯỚC 4: TẠO PROMPT (v3 - Hoàn chỉnh) ---
    prompt = f"""
NỘI DUNG HIỆN TẠI:
Người dùng vừa chia sẻ: "{user_text}"
Cảm xúc chính được nhận diện là: {sentiment_label}
Cảm xúc chi tiết (nếu có): {emotion_label or 'Không xác định'}

BỐI CẢNH QUÁ KHỨ (STATE):
{history_summary}

NHIỆM VỤ:
Dựa vào cả BỐI CẢNH và NỘI DUNG HIỆN TẠI, hãy phản hồi họ.
"""
    
    # --- BƯỚC 5: SINH PHẢN HỒI (MODEL 3 - GEMINI) ---
    response_result = query_model("response", prompt)

    if "error" in response_result:
        return {"status": "error", "error_message": f"Response model failed: {response_result['error']}", "timestamp": pipeline_start_time, "sentiment_data": {"label": sentiment_label, "score": sentiment_score}}

    advice_text = response_result.get("text", "").strip() or \
        "Mình chưa biết nên nói gì lúc này, nhưng mình vẫn ở đây để lắng nghe bạn 🌿."
    advice_source = response_result.get("source", "google_gemini_2.5_flash")

    # --- BƯỚC 6: GỘP KẾT QUẢ ---
    return format_pipeline_output(
        status="success",
        user_text=user_text,
        sentiment_label=sentiment_label,
        sentiment_score=sentiment_score,
        sentiment_model=sentiment_result.get("model"),
        emotion_label=emotion_label, # <-- Gửi thêm data mới
        response_text=advice_text,
        response_source=advice_source,
        timestamp=pipeline_start_time
    )

# === (CẢI TIẾN) KHỐI 5: HÀM IN ẤN (v3) ===
console = Console()
def print_pipeline_result(result: dict):
    # (Đã có bản vá lỗi Debug)
    if not result or result.get("status") != "success":
        console.print("[bold red] Pipeline lỗi hoặc không có kết quả hợp lệ![/bold red]")
        if result and "error_message" in result:
            console.print(f"[bold yellow]Lỗi chi tiết (Debug):[/bold yellow] {result['error_message']}")
        return
    
    user_text = result.get("input_text", "")
    sentiment = result.get("sentiment", {})
    response = result.get("response", {})
    timestamp = result.get("timestamp", "")
    table = Table(show_header=True, header_style="bold cyan", expand=True)
    table.add_column("Trường thông tin", justify="right", style="bold yellow")
    table.add_column("Giá trị", style="white")
    table.add_row(" Input", user_text)
    
    # --- CẢI TIẾN: Hiển thị cả 2 model ---
    sentiment_main = f"{sentiment.get('label', '')} ({sentiment.get('score', 0):.2f})"
    sentiment_detail = str(sentiment.get('emotion_detail', 'N/A')) # N/A nếu là neutral
    table.add_row(" Sentiment (Chính)", sentiment_main)
    table.add_row(" Sentiment (Chi tiết)", sentiment_detail)
    # --- KẾT THÚC CẢI TIẾN ---
    
    table.add_row(" GPT Response", response.get("text", "").strip())
    table.add_row(" Model", str(sentiment.get("model", "")))
    table.add_row(" Timestamp", timestamp)
    console.print(Panel.fit(table, title="🧩 AI Mood Journal Pipeline Result", border_style="bold green"))