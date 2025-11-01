"""
core/hf_client.py
Module giao tiếp với Hugging Face API và GPT API.
- Gọi model sentiment / tone / response.
- Trả kết quả dạng JSON chuẩn.
"""
from core.utils import clean_text, get_vn_timestamp
from core.utils import append_jsonl, read_jsonl
from core.prompts import SYSTEM_PROMPT
from datetime import datetime, timezone, timedelta
import requests
from openai import OpenAI  
from core.config import HF_MODELS, API_TOKEN, TIMEOUT, OPENAI_API_KEY, GPT_RESPONSE_MODEL_ID  

# Header xác thực
HEADERS = {"Authorization": f"Bearer {API_TOKEN}"}

def query_model(model_name: str, text: str):
    text = clean_text(text)

    """
    Gọi model Hugging Face hoặc GPT tương ứng.
    Trả về dict: {label, score, text, model}
    """
    #Lấy model ID từ config( nếu có)
    model_id = HF_MODELS.get(model_name)
    #Chỉ raise lỗi nếu model_name không phải GPT cũng không nằm trong HF_MODELS
    if not model_id and model_name != "response":
        raise ValueError(f"Model '{model_name}' không tồn tại trong HF_MODELS.")

    url = f"https://api-inference.huggingface.co/models/{model_id}"
    payload = {"inputs": text}

    try:
        # --- Nếu là model Hugging Face ---
        if model_name in ["sentiment", "tone"]:
            response = requests.post(
                url,
                headers=HEADERS,
                json=payload,
                timeout=TIMEOUT
            )
            response.raise_for_status()
            data = response.json()

            # Trích xuất label & score
            # Một số model Hugging Face trả về list lồng nhau [[{...}]], nên cần kiểm tra kỹ.
            if isinstance(data,list):
                #Nếu list rỗng
                if not data:
                    return {"error": f"Không có dữ liệu trả về từ model {model_name}."} 
                #Nếu là list lông nhau
                if isinstance(data[0], list):
                    result = data[0][0]
                else:
                    result = data[0]
            else:
                result = data
            #Bảo vệ lỗi nếu không có key label/score
            label = result.get("label", "unknown")
            score = round(result.get("score", 0.0), 3)

            return {
                "label": label,      # Nhãn phân loại
                "score": score,      # Điểm tin cậy
                "model": model_id    # Model ID
            }
        # --- Nếu là GPT response model ---
        elif model_name == "response":
            #Gọi Student Mood GPT qua OpenAI client
            client = OpenAI(api_key=OPENAI_API_KEY)
            # === Prompt định nghĩa tính cách Student Mood GPT ===
            
            gpt_response = client.chat.completions.create(
                model=GPT_RESPONSE_MODEL_ID,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": text},
                ],
            )


            gpt_message = gpt_response.choices[0].message.content.strip()
            cleaned_text = (
                gpt_message
                .encode('utf-8', 'ignore')  # đảm bảo mã hóa
                .decode('utf-8')            # chuyển lại string
                .replace("\\n", "\n")       # chuyển \n thành thật sự xuống dòng
                .replace("\u200d", "")      # xóa ký tự invisible joiner
                .strip()                    # loại bỏ khoảng trắng dư
            )
            # --- Lấy thời gian Việt Nam ---
            vn_time = datetime.now(timezone.utc) + timedelta(hours=7)
            formatted_time = vn_time.strftime("%d/%m/%Y %H:%M:%S")
            return {
                "text": gpt_message.strip().replace("\\n", "\n"),   # xuống dòng thật
                "source": "student_mood_gpt",
                "timestamp": formatted_time
            }

        # --- Nếu chưa biết loại model ---
        else:
            return {"error": f"Model '{model_name}' không được hỗ trợ."}

    except requests.exceptions.Timeout:
        return {"error": f"Timeout khi gọi model {model_name}."}
    except requests.exceptions.RequestException as e:
        return {"error": f"Lỗi khi gọi model {model_name}: {e}"}
    except Exception as e:
        return {"error": f"Lỗi parse dữ liệu từ {model_name}: {e}"}
    return format_response("response", gpt_message)
def format_response(model_name, message_text):
    """Tạo JSON chuẩn để frontend dùng trực tiếp"""
    from datetime import datetime, timedelta, timezone

    vn_time = datetime.now(timezone.utc) + timedelta(hours=7)
    formatted_time = vn_time.strftime("%d/%m/%Y %H:%M:%S")

    return {
        "model": model_name,
        "text": message_text.strip().replace("\\n", "\n"),
        "source": "student_mood_gpt",
        "timestamp": formatted_time
    }
