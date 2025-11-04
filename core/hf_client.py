"""
core/hf_client.py (v4 - Đã sửa lỗi URL, Xác thực, và Lỗi Gemini)
Module giao tiếp với API Space "tối ưu" và API Gemini.
"""
import google.generativeai as genai
from core.utils import clean_text, get_vn_timestamp
from core.utils import append_jsonl, read_jsonl
from core.prompts import SYSTEM_PROMPT
from datetime import datetime, timezone, timedelta
import requests
from openai import OpenAI  
from core.config import (
    HF_MODELS, 
    API_TOKEN, 
    TIMEOUT, 
    OPENAI_API_KEY, 
    GPT_RESPONSE_MODEL_ID,
    GOOGLE_API_KEY # <-- Key mới
)

# Header xác thực (Dùng cho cả API HF và API Space "Private")
HEADERS = {"Authorization": f"Bearer {API_TOKEN}"}

# === Cấu hình Gemini (Chạy 1 lần) ===
# (Sửa lỗi 'system_instruction' bằng cách đặt nó ở đây)
genai.configure(api_key=GOOGLE_API_KEY)
gemini_model = genai.GenerativeModel(
    'gemini-2.5-flash',
    system_instruction=SYSTEM_PROMPT # <-- Tính cách AI được đặt ở đây
)
# === Kết thúc Cấu hình Gemini ===


def query_model(model_name: str, text: str):
    """
    Gọi model "sentiment" (của bạn) HOẶC model "response" (Gemini).
    """
    text = clean_text(text)
    
    try:
        # --- Trường hợp 1: Model "sentiment" (Gọi API Space CỦA BẠN) ---
        # (Đây là Giai đoạn 3)
        if model_name == "sentiment":
            
            url = HF_MODELS.get(model_name)
            if not url or "https://" not in url:
                 return {"error": f"Lỗi Config: HF_MODELS['sentiment'] phải là 1 URL (https://.../predict). Kiểm tra core/config.py."}
            
            payload = {"text": text} # Payload chuẩn của FastAPI
            
            response = requests.post(
                url,
                headers=HEADERS, # Sửa lỗi 403 (Xác thực)
                json=payload,
                timeout=TIMEOUT
            )
            response.raise_for_status()
            data = response.json()
            
            label = data.get("label", "unknown")
            score = round(data.get("score", 0.0), 3)

            return {
                "label": label,
                "score": score,
                "model": url
            }

        # --- Trường hợp 2: Model "sentiment_detail" (Model 7-lớp tương lai) ---
        # (Logic này giống hệt "sentiment", nhưng gọi key khác)
        elif model_name == "sentiment_detail":
            url = HF_MODELS.get(model_name)
            if not url or "https://" not in url:
                return {"error": f"Model 7-lớp (sentiment_detail) chưa được deploy."}
            
            payload = {"text": text}
            response = requests.post(url, headers=HEADERS, json=payload, timeout=TIMEOUT)
            response.raise_for_status()
            data = response.json()
            # (Chúng ta chỉ cần 'label', không cần 'score')
            return {"label": data.get("label", "unknown")}

        # --- Trường hợp 3: Model "response" (Sửa lỗi 429 - Gọi Google Gemini) ---
        elif model_name == "response":
            
            response = gemini_model.generate_content(
                text, # 'text' ở đây chính là context_prompt
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                )
            )
            gemini_message = response.text
            
            return {
                "text": gemini_message.strip().replace("\\n", "\n"),
                "source": "google_gemini_2.5_flash",
                "timestamp": get_vn_timestamp() 
            }

        # --- Trường hợp 4: Lỗi ---
        else:
            return {"error": f"Model '{model_name}' không được hỗ trợ."}

    # --- Xử lý Lỗi chung (Timeout, v.v.) ---
    except requests.exceptions.Timeout:
        return {"error": f"Timeout (Quá 30s) khi gọi model {model_name}."}
    except requests.exceptions.RequestException as e:
        return {"error": f"Lỗi khi gọi model {model_name}: {e}"}
    except Exception as e:
        return {"error": f"Lỗi parse dữ liệu từ {model_name}: {e}"}