# core/config.py
"""
Cấu hình trung tâm cho hệ thống AI Core. (Đã cập nhật Giai đoạn 4)
"""

import os
from dotenv import load_dotenv

# Load file .env để lấy biến môi trường
load_dotenv()

# === SỬA LỖI 410 (Dùng API "Tối ưu" của bạn) ===
# (API này chạy model 'Zonecb/my-phobert-sentiment-v1' đã fine-tune)
SENTIMENT_API_URL = "https://zonecb-my-sentiment-api.hf.space/predict"

HF_MODELS = {
    "sentiment": SENTIMENT_API_URL, # <-- SỬA: Trỏ đến API (Giai đoạn 3)
    
    # (Tương lai: Bạn sẽ deploy Model 2 (7-lớp) và đặt link API vào đây)
    "sentiment_detail": "LINK_API_MODEL_7_LOP_CUA_BAN_SAU_NAY", 
    
    "tone": "uitnlp/visobert" 
}

# === SỬA LỖI 429 (Chuyển sang Google) ===
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") # <-- THÊM: Đọc Google Key
GPT_RESPONSE_MODEL_ID = os.getenv("GPT_RESPONSE_MODEL_ID", "gpt-4o-mini") 

# Token Hugging Face (Dùng để xác thực API "Private" của bạn)
API_TOKEN = os.getenv("HF_API_TOKEN", "")

# Tham số hệ thống
DEFAULT_TONE = "neutral"
MAX_LEN = 512
TIMEOUT = 30 # (Lưu ý: API "ngủ đông" của bạn có thể lỗi ở lần đầu)
CONF_THRESHOLD = 0.6