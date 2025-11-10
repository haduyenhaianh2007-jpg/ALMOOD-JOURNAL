import os
import json
from datetime import datetime
from core.pipeline import run_ai_pipeline

# =============================
# 🎨 HÀM TRÌNH BÀY ĐẸP
# =============================
def print_pretty_pipeline(result, index=None):
    print("\n" + "=" * 75)
    if index is not None:
        print(f"🧪 TEST CASE {index}")
        print("=" * 75)

    # Input
    text = result.get("text", "")
    print(f"\n📝 Input:\n{text}\n")

    # Sentiment
    print(f"💬 Sentiment: {result.get('predicted_label', 'unknown')}")

    # Probabilities
    print(f"📊 Probabilities: {result.get('label_distribution', {})}")

    # Emotion
    emo = result.get("emotion_detail", "")
    if emo:
        print(f"🎭 Emotion Detail: {emo}")

    # Case type
    print(f"🧩 Case Type: {result.get('case_type', 'unknown')}")

    # Advice
    advice = result.get("advice_text", "")
    if advice:
        print(f"\n💡 Gemini Advice:\n{advice}\n")

    # Source
    src = result.get("advice_source", "")
    if src:
        print(f"📚 Source: {src}")

    # Timestamp
    print(f"\n⏰ Timestamp: {result.get('timestamp', '')}")
    print("=" * 75 + "\n")


# =============================
# 🚀 BẮT ĐẦU TEST PIPELINE
# =============================
def main(mock_mode=False):

    print("=== 🚀 BẮT ĐẦU TEST PIPELINE (mock_mode=False) ===")

    test_cases = [
        "chúng tôi không thể tham dự các cuộc thi về sáng tạo sinh viên bởi vì leader của chúng tôi nhập viện."

    ]

    all_results = []

    for idx, text in enumerate(test_cases, 1):
        print(f"\n=== TEST CASE {idx} ===")
        print(f"📘 User input: {text}")

        result = run_ai_pipeline(text, user_id="test_user_01")

        # Đảm bảo các trường luôn tồn tại
        result.setdefault("predicted_label", "unknown")
        result.setdefault("label_distribution", {"negative": 0, "neutral": 0, "positive": 0})
        result.setdefault("emotion_detail", "")
        result.setdefault("timestamp", str(datetime.now()))
        result.setdefault("case_type", "unknown")
        result.setdefault("advice_text", "")
        result.setdefault("advice_source", "")

        # 🎨 In đẹp
        print_pretty_pipeline(result, index=idx)

        all_results.append(result)

    # =============================
    # 💾 LƯU LOG
    # =============================
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "pipeline_log.json")

    print(f"📁 Đang lưu {len(all_results)} kết quả vào {log_file}...")

    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=4)

    print("✨ Đã lưu thành công!")


if __name__ == "__main__":
    main(mock_mode=False)
