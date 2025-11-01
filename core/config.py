# core/config.py
"""
Cấu hình trung tâm cho hệ thống AI Core.
- Lưu thông tin model Hugging Face
- Đọc API token từ file .env
- Giúp mọi người làm việc an toàn, không lộ thông tin nhạy cảm
"""

import os
from dotenv import load_dotenv

# Load file .env để lấy biến môi trường (token, config bí mật)
load_dotenv()

# Danh sách model dùng trong hệ thống
HF_MODELS = {
    "sentiment": "5CD-AI/Vietnamese-Sentiment-visobert",                 # Model phân tích cảm xúc tiếng Việt

    "tone": "uitnlp/visobert"   # Model phân tích tone tiếng Việt (có thể đổi visobert)
}
# OpenAI configs
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GPT_RESPONSE_MODEL_ID = os.getenv("GPT_RESPONSE_MODEL_ID", "gpt-4o-mini")  # Model GPT dùng cho response
# Token Hugging Face — đọc tự động từ .env
API_TOKEN = os.getenv("HF_API_TOKEN", "")
#Tham số hệ thống
DEFAULT_TONE = "neutral"        # tone mặc định khi model không xác định được (neutral, positive, negative)
MAX_LEN = 512                   # Giới hạn độ dài input/output (tối đa token cho model)
TIMEOUT = 30                    # Thời gian chờ tối đa khi gọi API (giây)
CONF_THRESHOLD = 0.6            # Ngưỡng tin cậy tối thiểu cho sentiment / tone detection

