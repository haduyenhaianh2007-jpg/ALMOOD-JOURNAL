"""
core/utils.py
-----------------------------------------
Chứa các hàm tiện ích dùng chung giữa:
- Team AI (pipeline, test)
- Team Backend (server, API)
-----------------------------------------
Mục tiêu: tái sử dụng, tránh lặp code, dễ bảo trì.
"""

from datetime import datetime, timezone, timedelta # thời gian chuẩn
import json # đọc/ghi JSON
import os # thao tác file hệ thống
import re # xử lý text
from typing import Any, Dict, List # chú thích kiểu
# ============================================================
#  1. Hàm: get_vn_timestamp()
# ------------------------------------------------------------
# Lấy thời gian hiện tại theo múi giờ Việt Nam (UTC+7)
# Dùng để gắn timestamp vào log, response, hoặc database.
# ============================================================
def get_vn_timestamp() -> str:
    """Trả về timestamp giờ Việt Nam (ISO 8601 format)."""
    vn_time = datetime.now(timezone.utc) + timedelta(hours=7)
    return vn_time.strftime("%Y-%m-%d %H:%M:%S")

# ============================================================
#  2. Hàm: append_jsonl()
# ------------------------------------------------------------
# Ghi thêm 1 dòng dữ liệu JSON vào file .jsonl
# Dùng cho test log hoặc backend ghi log người dùng.
# ============================================================
def append_jsonl(path: str, data: Dict[str, Any]) -> None:
    """
    Ghi dữ liệu dạng JSON vào file .jsonl
    Mỗi dòng = 1 JSON object.
    """
    os.makedirs(os.path.dirname(path), exist_ok=True) # Tạo thư mục nếu chưa có
    with open(path, "a", encoding="utf-8") as f:# Mở file ở chế độ append
        json.dump(data, f, ensure_ascii=False)# Ghi JSON
        f.write("\n")# Xuống dòng sau mỗi object

# ============================================================
#  3. Hàm: read_jsonl()
# ------------------------------------------------------------
# Đọc toàn bộ dữ liệu từ file .jsonl -> list[dict]
# Dùng trong analyze_logs.py hoặc dashboard backend.
# ============================================================
def read_jsonl(path: str) -> List[Dict[str, Any]]:
    """Đọc toàn bộ file .jsonl, trả về danh sách các dict."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Không tìm thấy file log: {path}")# lỗi nếu file không tồn tại
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(line.strip()) for line in f if line.strip()]# đọc từng dòng, bỏ dòng trống

# ============================================================
#  4. Hàm: clean_text()
# ------------------------------------------------------------
# Làm sạch text người dùng nhập (xóa ký tự lỗi, khoảng trắng thừa)
# Dùng trước khi gửi text cho GPT để tránh lỗi encoding.
# ============================================================
def clean_text(text: str) -> str:
    """
    Chuẩn hóa text:
    - Loại bỏ ký tự không in được
    - Giảm khoảng trắng
    - Xóa ký tự điều khiển (ẩn)
    """
    text = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", text)# xóa ký tự điều khiển
    text = re.sub(r"\s+", " ", text).strip()# giảm khoảng trắng
    return text

# ============================================================
#  5. Hàm: normalize_sentiment()
# ------------------------------------------------------------
# Chuẩn hóa nhãn cảm xúc model trả về cho thống nhất
# (ví dụ: "POS" → "positive", "NEG" → "negative", ...)
# ============================================================
def normalize_sentiment(label: str) -> str: # chuẩn hóa nhãn cảm xúc
    """
    Chuyển nhãn sentiment về dạng thống nhất (chuẩn hóa)
    """
    mapping = {
        "POS": "positive",
        "NEG": "negative",
        "NEU": "neutral",
        "positive": "positive",
        "negative": "negative",
        "neutral": "neutral"
    }
    return mapping.get(label.strip().upper(), "neutral")# mặc định về neutral nếu không khớp
