"""
core/hf_client.py (Giai đoạn 5 – Sentiment v2, không có 7 lớp)
"""
from dotenv import load_dotenv
load_dotenv()
import google.generativeai as genai
import os
from core.utils import clean_text, get_vn_timestamp
from core.prompts import SYSTEM_PROMPT
import requests
import torch
import numpy as np
import torch.nn.functional as F
from core.config import (
    API_TOKEN,
    TIMEOUT,
    OPENAI_API_KEY,
    GPT_RESPONSE_MODEL_ID,
    GOOGLE_API_KEY,
    SENTIMENT_API_URL,
    SENTIMENT_MODEL_NAME,
    LABELS,
    SOFTMAX_TEMPERATURE,
    ROUND_DECIMALS,
    EMOTION_MAP
)

# Header xác thực (cho cả API Hugging Face Space nếu private)
HEADERS = {"Authorization": f"Bearer {API_TOKEN}"}

# === Cấu hình Gemini ===
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
gemini_model = genai.GenerativeModel(
    'gemini-2.5-flash',
    system_instruction=SYSTEM_PROMPT
)

# === Hàm chính ===
def query_model(model_name: str, text: str):
    """
    Gọi model 'sentiment' hoặc 'response'.
    - Sentiment: gọi Hugging Face Space, tính softmax, trả tỉ lệ % từng nhãn.
    - Response: gọi Gemini để sinh phản hồi.
    """
    text = clean_text(text)
    
    try:
        # --- Model 1: Sentiment ---
        if model_name == "sentiment":
            url = SENTIMENT_API_URL
            payload = {"text": text}

            response = requests.post(url, headers=HEADERS, json=payload, timeout=TIMEOUT)
            response.raise_for_status()
            data = response.json()

            logits = data.get("raw_logits") or data.get("logits") or data.get("scores")
            label = data.get("predicted_label") or data.get("label")

            if logits:
                # Ép logits thành mảng phẳng 1D, tránh lỗi nested list
                try:
                    logits_tensor = torch.tensor(logits, dtype=torch.float32).flatten()
                    probs = F.softmax(logits_tensor / SOFTMAX_TEMPERATURE, dim=-1)
                    probs = probs.detach().cpu().numpy()  # chuyển sang numpy để tính toán dễ
                except Exception as e:
                    return {"error": f"Lỗi parse dữ liệu từ sentiment: {e}"}

                # Tính phần trăm mỗi nhãn
                label_distribution = {
                    LABELS[i]: round(float(p) * 100, ROUND_DECIMALS)
                    for i, p in enumerate(probs)
                }
                # Đảm bảo tổng = 100%
                total = sum(label_distribution.values())
                if total != 100:
                    correction = 100 - total
                    largest_label = max(label_distribution, key=label_distribution.get)
                    label_distribution[largest_label] = round(label_distribution[largest_label] + correction, ROUND_DECIMALS)

                predicted_label = max(label_distribution, key=label_distribution.get)
                emotion_detail = EMOTION_MAP.get(predicted_label, "")

                return {
                    "input": text,
                    "predicted_label": predicted_label,
                    "label_distribution": label_distribution,
                    "emotion_detail": emotion_detail,
                    "model": SENTIMENT_MODEL_NAME,
                    "timestamp": get_vn_timestamp(),
                }

            elif label:
                emotion_detail = EMOTION_MAP.get(label, "")
                print(f"[Sentiment] {label.upper()} (no logits) → 100%")
                return {
                    "input": text,
                    "predicted_label": label,
                    "label_distribution": {label: 100.0},
                    "emotion_detail": emotion_detail,
                    "model": SENTIMENT_MODEL_NAME,
                    "timestamp": get_vn_timestamp()
                }

            else:
                return {"error": f"Không tìm thấy logits hoặc label từ API {url}"}

        # --- Model 2: Response (Gemini) ---
        elif model_name == "response":
            response = gemini_model.generate_content(
                text,
                generation_config=genai.types.GenerationConfig(temperature=0.7),
            )
            gemini_message = response.text
            return {
                "text": gemini_message.strip().replace("\\n", "\n"),
                "source": "google_gemini_2.5_flash",
                "timestamp": get_vn_timestamp()
            }

        else:
            return {"error": f"Model '{model_name}' không được hỗ trợ."}

    except requests.exceptions.Timeout:
        return {"error": f"Timeout khi gọi model {model_name}."}
    except requests.exceptions.RequestException as e:
        return {"error": f"Lỗi khi gọi model {model_name}: {e}"}
    except Exception as e:
        return {"error": f"Lỗi parse dữ liệu từ {model_name}: {e}"}
