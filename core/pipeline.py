# --- pipeline.py ---
# AI Mood Journal: Sentiment + Response Pipeline
# Phiên bản: v4.0 (simple emotion mapping + JSON logging)

import time
import torch
import torch.nn.functional as F
from core.history_engine import build_past_context
# 🆕 To-Do Engine
from core.todo_engine import (
    extract_tasks_from_text,
    generate_gentle_question,
    create_todo_plan
)

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
    # BƯỚC 5.5: ĐỌC LẠI HISTORY → TẠO BỐI CẢNH QUÁ KHỨ
    # ------------------------------
    history_context = build_past_context(
        current_label=predicted_label,
        case_type=case_type,
        #user_id=user_id,
    )
    print("📚 History context:")
    print(history_context)
    # ============================================
    # 🆕 BƯỚC 5.6: TODO ENGINE – PHÁT HIỆN NHIỆM VỤ
    # ============================================

    todo_candidates = extract_tasks_from_text(
        text,
        context_tags=[case_type] if case_type else []
    )

    print("🆕 [To-Do] Nhiệm vụ phát hiện:", todo_candidates)

    todo_question = None
    best_task = None

    # Nếu có nhiệm vụ → sinh câu hỏi nhẹ nhàng
    if todo_candidates:
        best_task = max(todo_candidates, key=lambda x: x.confidence)
        todo_question = generate_gentle_question(best_task)
        print("\n🆕 [To-Do] Câu hỏi nhẹ nhàng:")
        print(todo_question)

    # ------------------------------
   # ------------------------------
   # ------------------------------
    # BƯỚC 6: SINH PHẢN HỒI VÀ PHÂN LOẠI TOPIC (GỘP 2 TRONG 1)
    # ------------------------------
    import json # Cần import để đọc JSON
    print("🤖 Calling unified model for response and topic...")

    # PROMPT NÀY PHẢI KHỚP VỚI ĐỊNH DẠNG TRONG prompts.py
    prompt = (
        f"NỘI DUNG HIỆN TẠI: Người dùng vừa chia sẻ: \"{text}\"\n"
        f"Cảm xúc chính được nhận diện là: {predicted_label} (Phân bố: {label_distribution})\n"
        f"Cảm xúc chi tiết (nếu có): {emotion_detail_summary}\n"
        f"(Bối cảnh/Loại cảm xúc hiện tại: {case_type})\n"
        f"(BỐI CẢNH QUÁ KHỨ: {history_context})\n"
        f"NHIỆM VỤ: Dựa vào cả BỐI CẢNH và NỘI DUNG HIỆN TẠI, hãy phản hồi họ."
    )
    # 🆕 Nếu có nhiệm vụ → yêu cầu LLM hỏi user theo kiểu nhẹ nhàng
    if todo_question:
        prompt += (
            "\n\n=== GỢI Ý NHIỆM VỤ ===\n"
            f"{todo_question}\n"
            "Nếu người dùng đồng ý, hãy trả lời: 'Ok, mình tạo kế hoạch nhé!'\n"
        )

    # --- Khởi tạo giá trị mặc định ---
    fallback_advice = "Mình đang hơi trục trặc một chút, nhưng mình vẫn ở đây để lắng nghe bạn 🌿."
    advice_text = fallback_advice
    topic_label = "không xác định"
    advice_source = "fallback"
    
    # --- Gọi Model 1 LẦN DUY NHẤT ---
    response_result = query_model("response", prompt)

    if "error" in response_result:
        print(f"⚠️ Lỗi model response: {response_result['error']}")
        # Lỗi, giữ nguyên giá trị mặc định
    else:
        raw_text = response_result.get("text", "").strip()
        advice_source = response_result.get("source", "gemini_flash")
        # Nếu advice_text chứa JSON (vì model có thể trả toàn bộ trong 1 chuỗi)
        if raw_text.strip().startswith("{") and "response" in raw_text:
            try:
                inner_data = json.loads(raw_text)
                advice_text = inner_data.get("response", fallback_advice).strip()
                topic_label = inner_data.get("topic", "không xác định").strip()
                print(f"✅ Đã tách topic bên trong advice_text: {topic_label}")
            except Exception as e:
                print(f"⚠️ Lỗi parse advice_text nội bộ: {e}")

        try:
                    # --- LẦN 1: Parse JSON thẳng ---
            json_start = raw_text.find('{')
            json_end = raw_text.rfind('}') + 1
            if json_start == -1 or json_end == 0:
                raise json.JSONDecodeError("Không tìm thấy JSON object", raw_text, 0)

            json_str = raw_text[json_start:json_end]

            # --- Chuẩn hóa khóa JSON ---
            json_str = json_str.replace(" response:", ' "response":')
            json_str = json_str.replace("response:", ' "response":')
            json_str = json_str.replace(" topic:", ' "topic":')
            json_str = json_str.replace("topic:", ' "topic":')

            data = json.loads(json_str)

           # --- Parse và tách JSON lồng nhau ---
            try:
                # Nếu advice_text là JSON string, parse thêm 1 lớp nữa
                advice_raw = data.get("response", "")
                if advice_raw.strip().startswith("{"):
                    inner = json.loads(advice_raw)
                    advice_text = inner.get("response", fallback_advice).strip()
                    topic_label = inner.get("topic", "không xác định").strip()
                    print(f"✅ Đã lấy topic từ lớp JSON trong advice_text: {topic_label}")
                else:
                    advice_text = advice_raw or fallback_advice
                    topic_label = data.get("topic", "không xác định").strip()

            except Exception as e:
                print(f"⚠️ Lỗi khi parse advice_text lồng nhau: {e}")
                advice_text = fallback_advice
                topic_label = "không xác định"

            if not advice_text:
                advice_text = fallback_advice
            print(f"👍 Response parsed (Lần 1).")

        except (json.JSONDecodeError, Exception) as e:
            # --- LẦN 2: Thử parse lại bằng cách làm sạch chuỗi ---
            print(f"⚠️ Lỗi parse JSON lần 1 ({e}). Thử lại với replace...")
            try:
                # Làm sạch ký tự đặc biệt và escape ký tự xuống dòng
                cleaned = raw_text.replace("\r", "").replace("\n", "\\n").strip()
                cleaned = cleaned.replace("```json", "").replace("```", "")

                json_start = cleaned.find('{')
                json_end = cleaned.rfind('}') + 1
                if json_start == -1 or json_end <= 0:
                    raise ValueError("Không tìm thấy JSON object trong lần 2")

                json_str = cleaned[json_start:json_end]

                # Escape ký tự đặc biệt để tránh lỗi JSON
                import re
                json_str = re.sub(r'(?<=\{|,)\s*(\w+):', r'"\1":', json_str)

                # Thử parse lại
                data = json.loads(json_str)

                advice_text = data.get("response", fallback_advice).strip()
                topic_label = data.get("topic", "không xác định").strip()
                advice_source = response_result.get("source", "gemini_flash")
                print(f"✅ JSON parsed thành công (Lần 2). Topic: {topic_label}")

            except Exception as e2:
                print(f"⚠️ Lỗi parse JSON lần 2 ({e2}). Fallback về raw text.")
                advice_text = raw_text.replace("```json", "").replace("```", "").strip()
                if not advice_text:
                    advice_text = fallback_advice
                topic_label = "không xác định"
                print(f"👍 Fallback: Set advice to raw text. Topic: {topic_label}")



                # --- FIX BỔ SUNG: Tự động trích topic từ advice_text nếu còn dạng chuỗi JSON ---
        if isinstance(advice_text, str) and advice_text.strip().startswith("{") and "topic" in advice_text:
            try:
                inner = json.loads(advice_text)
                advice_text = inner.get("response", advice_text).strip()
                topic_label = inner.get("topic", topic_label).strip()
                print(f"✅ Đã tách topic từ advice_text (fix cuối): {topic_label}")
            except Exception as e:
                print(f"⚠️ Không thể parse topic trong advice_text (fix cuối): {e}")

        # ------------------------------
    # ------------------------------
    # ============================================
    # 🆕 BƯỚC 7: USER ĐỒNG Ý → TẠO TO-DO PLAN
    # ============================================
        todo_plan = None

        if todo_question:
            user_reply = advice_text.lower().strip()

            need_plan = any(k in user_reply for k in [
                "ok", "oke", "đồng ý", "tạo kế hoạch", "làm đi", "yes"
            ])

            if need_plan and best_task:
                todo_plan = create_todo_plan(best_task, text)
                print("🆕 [To-Do] Đã tạo kế hoạch:", todo_plan)
 # BƯỚC 8: KẾT QUẢ CUỐI

    final_result = {
        "todo_candidates": [
    {
        "action": t.action,
        "description": t.description,
        "confidence": t.confidence,
        "context_tags": t.context_tags,
    }
    for t in todo_candidates
],

        "todo_question": todo_question,

        "todo_plan": {
            "main_task": todo_plan.main_task,
            "subtasks": todo_plan.subtasks,
            "deadline": todo_plan.deadline,
            "timeline": todo_plan.timeline,
        } if todo_plan else None,

        "status": "success",
        "text": text,
        "predicted_label": predicted_label,
        "label_distribution": label_distribution,
        "emotion_detail": emotion_detail_summary,
        "topic": topic_label,
        "case_type": case_type,
        "advice_text": advice_text,
        "advice_source": advice_source,
        "timestamp": get_vn_timestamp(),
        "processing_time": round(time.time() - start, 2),
    }
    
   # =========================
# BƯỚC 8: APPEND LỊCH SỬ KHÔNG GHI ĐÈ
# =========================
    import os, json

    save_path = "pipeline_history.json"

    try:
        # --- FIX TOPIC TRƯỚC ---
        advice_raw = final_result.get("advice_text", "")
        topic_label = final_result.get("topic", "không xác định")

        if isinstance(advice_raw, str) and advice_raw.strip().startswith("{"):
            try:
                inner = json.loads(advice_raw)
                final_result["advice_text"] = inner.get("response", advice_raw)
                final_result["topic"] = inner.get("topic", topic_label)
                print(f"✅ Đã lấy topic nội bộ: {final_result['topic']}")
            except Exception as e:
                print(f"⚠️ Lỗi parse advice_text nội bộ: {e}")

        # --- TẠO FILE NẾU CHƯA CÓ ---
        if not os.path.exists(save_path):
            with open(save_path, "w", encoding="utf-8") as f:
                json.dump([], f, ensure_ascii=False, indent=2)

        # --- APPEND DỮ LIỆU MỚI ---
        with open(save_path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                if not isinstance(data, list):
                    data = []
            except json.JSONDecodeError:
                data = []

        # Thêm bản ghi mới
        data.append(final_result)

        # --- GHI LẠI (OVERWRITE TOÀN BỘ LIST) ---
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print("✅ Đã lưu kết quả mới vào pipeline_history.json")

    except Exception as e:
        print(f"⚠️ Lỗi khi ghi dữ liệu lịch sử: {e}")

    return final_result

