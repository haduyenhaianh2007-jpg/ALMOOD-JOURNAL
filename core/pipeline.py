# --- pipeline.py ---
# AI Mood Journal: Sentiment + Response Pipeline
# Phiên bản: v4.0 (simple emotion mapping + JSON logging)

import time
import torch
import torch.nn.functional as F

from core.hf_client import query_model
from core.config import (
    SENTIMENT_MODEL_NAME,
    ROUND_DECIMALS,
    SOFTMAX_TEMPERATURE,
    CHUNK_SIZE
)
from core.utils import (
    get_vn_timestamp,
    detect_sentiment_case,
    chunk_text,
)


# ======================== #
#  HÀM PHỤ TRỢ
# ======================== #
def print_pipeline_result(result):
    print("\n===== SENTIMENT PIPELINE RESULT =====")
    print(f"Input: {result['text']}")
    print(f"Predicted Label: {result['predicted_label']}")
    print(f"Distribution: {result['label_distribution']}")
    print(f"Emotion Detail: {result['emotion_detail']}")
    print(f"Case Type: {result['case_type']}")
    print(f"Advice: {result['advice_text']}")
    print(f"Timestamp: {result['timestamp']}")
    print("=====================================\n")


# ======================== #
#  PIPELINE CHÍNH
# ======================== #
def run_ai_pipeline(text: str, user_id: str = None):
    pipeline_start_time = get_vn_timestamp()
    start = time.time()
    print(f"⏳ Pipeline started at {pipeline_start_time}")

    # ------------------------------
    # BƯỚC 1: CHUNKING
    # ------------------------------
    chunks = chunk_text(text, chunk_size=CHUNK_SIZE)
    print(f"📘 Chunked into {len(chunks)} parts")

    all_chunk_results = []
    all_probs = []

    # ------------------------------
    # BƯỚC 2: SENTIMENT TỪNG CHUNK
    # ------------------------------
    for i, chunk in enumerate(chunks):
        print(f"\n--- Analyzing chunk {i+1}/{len(chunks)} ---")

        sentiment_result = query_model("sentiment", chunk)
        if "error" in sentiment_result:
            return {
                "status": "error",
                "error_message": f"Sentiment model failed on chunk {i+1}: {sentiment_result['error']}",
                "timestamp": pipeline_start_time,
            }
        # ==== FIX PROBS ROBUST ====

        def extract_probs(sr):
            """
            Trả về [neg, neu, pos] trong mọi trường hợp.
            """
            # CASE 1 — model trả probs
            if isinstance(sr.get("probs"), list) and len(sr["probs"]) == 3:
                p = sr["probs"]
                s = sum(p) or 1
                return [p[0]/s, p[1]/s, p[2]/s]

            # CASE 2 — trả label_distribution (%)
            dist = sr.get("label_distribution")
            if isinstance(dist, dict) and {"negative","neutral","positive"} <= set(dist):
                n = float(dist["negative"])
                u = float(dist["neutral"])
                p = float(dist["positive"])
                s = n + u + p or 1
                return [n/s, u/s, p/s]

            # CASE 3 — trả raw_logits
            logits = sr.get("raw_logits")
            if isinstance(logits, list) and len(logits) == 3:
                import math
                exp = [math.exp(x) for x in logits]
                s = sum(exp)
                return [exp[0]/s, exp[1]/s, exp[2]/s]

            # CASE 4 — fallback
            return [0.0, 0.0, 0.0]


        # ---- dùng extract_probs để không lỗi nữa ----
        probs = extract_probs(sentiment_result)

        label_distribution = {
            "negative": round(probs[0]*100, 2),
            "neutral":  round(probs[1]*100, 2),
            "positive": round(probs[2]*100, 2)
        }

        label = sentiment_result.get("predicted_label", "unknown")


        # ------------------------------
        # SIMPLE EMOTION MAPPING
        # ------------------------------
        neg, neu, pos = probs

        if pos > 0.8:
            emotion_detail = "vui vẻ"
        elif pos > 0.5:
            emotion_detail = "tích cực nhẹ"
        elif neu > 0.5:
            emotion_detail = "bình thường"
        elif neg > 0.8:
            emotion_detail = "rất tiêu cực"
        elif neg > 0.5:
            emotion_detail = "buồn bã"
        else:
            emotion_detail = "không rõ"

        # label_distribution cho từng chunk
        label_distribution = {
            "negative": round(probs[0] * 100, ROUND_DECIMALS),
            "neutral": round(probs[1] * 100, ROUND_DECIMALS),
            "positive": round(probs[2] * 100, ROUND_DECIMALS),
        }

        # Schema chuẩn cho detect_sentiment_case
        all_chunk_results.append({
            "text": chunk,
            "label": label,
            "probs": probs,
            "length": len(chunk),
            "emotion_detail": emotion_detail,
        })

        all_probs.append(probs)

    # ------------------------------
    # BƯỚC 3: TỔNG HỢP TOÀN VĂN BẢN
    # ------------------------------
    avg_probs = torch.tensor(all_probs).mean(dim=0).tolist()
    label_distribution = {
        "negative": round(avg_probs[0] * 100, ROUND_DECIMALS),
        "neutral": round(avg_probs[1] * 100, ROUND_DECIMALS),
        "positive": round(avg_probs[2] * 100, ROUND_DECIMALS),
    }

    predicted_label = max(label_distribution, key=label_distribution.get)

    # ------------------------------
    # BƯỚC 4: GỘP CẢM XÚC
    # ------------------------------
    emotion_set = []
    for c in all_chunk_results:
        e = c["emotion_detail"]
        if e not in emotion_set:
            emotion_set.append(e)

    emotion_detail_summary = ", ".join(emotion_set) if emotion_set else "không rõ"

    # ------------------------------
    # BƯỚC 5: NHẬN DIỆN CASE
    # ------------------------------
    case_type = detect_sentiment_case(all_chunk_results)
    print(f"🧠 Detected sentiment case: {case_type}")

    # ------------------------------
    # BƯỚC 6: SINH PHẢN HỒI
    # ------------------------------
    prompt = (
        f"Ngữ cảnh: {text}\n"
        f"Cảm xúc trung bình: {predicted_label} ({label_distribution})\n"
        f"Mô tả: {emotion_detail_summary}\n"
        f"Loại cảm xúc: {case_type}\n"
        f"Hãy viết một phản hồi ngắn gọn, ấm áp và tự nhiên cho người dùng."
    )

    response_result = query_model("response", prompt)

    if "error" in response_result:
        advice_text = "Mình đang hơi trục trặc một chút, nhưng mình vẫn ở đây để lắng nghe bạn 🌿."
        advice_source = "fallback"
    else:
        advice_text = response_result.get("text", "").strip()
        advice_source = response_result.get("source", "gemini_flash")

    # ------------------------------
    # BƯỚC 7: KẾT QUẢ CUỐI
    # ------------------------------
    final_result = {
        "status": "success",
        "text": text,
        "predicted_label": predicted_label,
        "label_distribution": label_distribution,
        "emotion_detail": emotion_detail_summary,
        "case_type": case_type,
        "advice_text": advice_text,
        "advice_source": advice_source,
        "timestamp": get_vn_timestamp(),
        "processing_time": round(time.time() - start, 2),
    }
    # ------------------------------
    # BƯỚC 8: APPEND JSON LỊCH SỬ
    # ------------------------------
    import json, os
    save_path = "pipeline_history.json"

    # Tạo file nếu chưa có
    if not os.path.exists(save_path):
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2)

    # Append kết quả vào file
    with open(save_path, "r+", encoding="utf-8") as f:
        data = json.load(f)
        data.append(final_result)
        f.seek(0)
        json.dump(data, f, ensure_ascii=False, indent=2)

    return final_result
