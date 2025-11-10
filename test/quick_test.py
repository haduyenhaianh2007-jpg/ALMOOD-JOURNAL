# --- quick_test.py ---
# Test model Sentiment + Response riêng biệt (robust with any hf_client return)
# -------------------------------------------------------------------
import sys, os, time
import math

# Cho phép import core/* khi chạy từ thư mục tests/
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.hf_client import query_model
from core.config import ROUND_DECIMALS

try:
    import torch
    import torch.nn.functional as F
    _HAS_TORCH = True
except Exception:
    _HAS_TORCH = False

texts = [
    "Hôm nay tôi cảm thấy rất buồn, chẳng muốn làm gì cả.",
    "Mình vui lắm, vừa nhận được học bổng! 😄",
    "Tôi hơi lo lắng cho bài thi sắp tới.",
    "Mình nhớ mẹ, chỉ muốn về nhà ôm mẹ thôi.",
    "Tôi bực mình vì bị điểm thấp dù đã cố gắng.",
]

def _build_probs(sr):
    """
    Trả về probs dạng [neg, neu, pos] hoặc None nếu không thể suy ra.
    Ưu tiên: probs -> label_distribution(%) -> raw_logits(softmax).
    """
    # 1) probs
    p = sr.get("probs")
    if isinstance(p, (list, tuple)) and len(p) == 3 and any(x is not None for x in p):
        # Normalize nhẹ phòng sai số
        s = float(sum(p)) or 1.0
        return [float(p[0]) / s, float(p[1]) / s, float(p[2]) / s]

    # 2) label_distribution (%)
    dist = sr.get("label_distribution")
    if isinstance(dist, dict) and {"negative","neutral","positive"} <= set(dist.keys()):
        n = float(dist["negative"])
        u = float(dist["neutral"])
        p = float(dist["positive"])
        s = (n + u + p) or 1.0
        return [n/s, u/s, p/s]

    # 3) raw_logits
    logits = sr.get("raw_logits")
    if _HAS_TORCH and isinstance(logits, (list, tuple)) and len(logits) == 3:
        lt = torch.tensor(list(map(float, logits)), dtype=torch.float32)
        probs = F.softmax(lt, dim=-1).tolist()
        return probs

    return None

print("\n🚀=== TEST MODEL SENTIMENT + RESPONSE ===🚀\n")

for i, text in enumerate(texts, 1):
    print("\n" + "="*80)
    print(f"🧩 TEST CASE {i}")
    print(f"📜 Input: {text}")
    print("-"*80)

    t0 = time.time()

    # -------- Sentiment --------
    sentiment_result = query_model("sentiment", text)

    if isinstance(sentiment_result, dict) and "error" in sentiment_result:
        print(f"❌ Sentiment error: {sentiment_result.get('error')}")
        print(f"↪ Payload: {sentiment_result}")
        print(f"🕒 Time: {round(time.time()-t0, 2)}s")
        continue

    label = sentiment_result.get("predicted_label", "unknown")
    probs = _build_probs(sentiment_result)

    if probs is None:
        print("⚠️ Không nhận được xác suất từ hf_client. Payload gốc:")
        print(sentiment_result)
        label_distribution = {"negative": 0, "neutral": 0, "positive": 0}
    else:
        label_distribution = {
            "negative": round(probs[0]*100, ROUND_DECIMALS),
            "neutral":  round(probs[1]*100, ROUND_DECIMALS),
            "positive": round(probs[2]*100, ROUND_DECIMALS),
        }

    print(f"🧠 Sentiment: {label}")
    print(f"📊 Probabilities: {label_distribution}")

    # -------- Response --------
    # -------- Response --------
    prompt = (
        f"Ngữ cảnh: {text}\n"
        f"Cảm xúc người nói: {label}\n"
        f"Hãy viết phản hồi ngắn gọn, tự nhiên và ấm áp."
    )

    response_result = query_model("response", prompt)

    if isinstance(response_result, dict) and "error" in response_result:
        # Không in lỗi API dài dòng
        response_text = "(fallback) Hiện tại mô hình phản hồi đang tạm bận, nhưng mình vẫn ở đây để lắng nghe bạn 🌿."
        source = "fallback"
    else:
        response_text = (response_result or {}).get("text", "").strip() or "Không có phản hồi."
        source = "gemini"

    t1 = round(time.time() - t0, 2)

    print("\n💬 Gemini Response:")
    print(response_text)
    print(f"\n🕒 Time: {t1}s | Source: {source}")

