"""
Cấu hình trung tâm cho hệ thống AI Core. (Cập nhật Giai đoạn 5 – Sentiment V2)
"""

import os
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta

# =============================
# 🔹 Load biến môi trường từ file .env
# =============================
load_dotenv()

# =============================
# 🔹 Cấu hình API & Model
# =============================

# ✅ Sử dụng API mới (Sentiment V2 – model đã fine-tune)
SENTIMENT_API_URL = "https://zonecb-my-sentiment-v2.hf.space/predict"

# ✅ Tên model sentiment đang dùng
SENTIMENT_MODEL_NAME = "Zonecb/my-phobert-sentiment-v2"

# Giữ nguyên cấu hình các model khác (nếu có)
HF_MODELS = {
    "tone": "uitnlp/visobert"  # (model tone cũ vẫn giữ để phòng dùng lại)
}

# =============================
# 🔹 Cấu hình khoá API
# =============================
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # Giữ nguyên
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")  # Giữ nguyên
GPT_RESPONSE_MODEL_ID = os.getenv("GPT_RESPONSE_MODEL_ID", "gpt-4o-mini")

# Token Hugging Face (nếu API private)
API_TOKEN = os.getenv("HF_API_TOKEN", "")

# =============================
# 🔹 Tham số hệ thống
# =============================
DEFAULT_TONE = "neutral"
MAX_LEN = 512
TIMEOUT = 30  # Cảnh báo: API có thể chậm ở lần gọi đầu
CONF_THRESHOLD = 0.6

# =============================
# 🔹 Tham số cho Sentiment Pipeline (Giai đoạn 5)
# =============================

# Nhiệt độ cho softmax (T = 1.0 là chuẩn Hugging Face)
SOFTMAX_TEMPERATURE = 1.0

# Cấu hình chunking: chia văn bản thành các phần nhỏ để phân tích cảm xúc chi tiết
CHUNK_SIZE = 300  # mỗi chunk tối đa 300 ký tự
ALWAYS_CHUNK = True  # luôn chunk dù văn bản ngắn hay dài

# Nhãn sentiment (theo thứ tự của model)
LABELS = ["negative", "neutral", "positive"]

# Ánh xạ cảm xúc chi tiết (rule-based)
EMOTION_MAP = {
    "positive": "vui vẻ, hạnh phúc, thoải mái, lạc quan",
    "neutral": "bình thường, cân bằng, ổn định",
    "negative": "buồn bã, lo lắng, căng thẳng, áp lực"
}

# Làm tròn phần trăm khi hiển thị label_distribution
ROUND_DECIMALS = 1

# =============================
# 🔹 Hàm tiện ích
# =============================

def get_vn_timestamp() -> str:
    """Trả về thời gian hiện tại ở múi giờ Việt Nam (UTC+7)."""
    return datetime.now(timezone(timedelta(hours=7))).strftime("%Y-%m-%d %H:%M:%S")

