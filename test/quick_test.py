"""
quick_test.py
Test nhanh pipeline thật — dùng để xem model phản hồi thế nào.
"""

import sys, os
# Thêm đường dẫn tới thư mục gốc để import module core
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.hf_client import query_model

# --- Test sentiment ---
texts = [
    "Hôm nay tôi được 10 điểm!",
    "Tôi áp lực quá, tôi muốn tự tử.",
   
]

print("\n=== TEST SENTIMENT (Hugging Face) ===")
for i, text in enumerate(texts, 1):
    print(f"\n[Text {i}] {text}")
    print("→", query_model("sentiment", text))

print("\n=== TEST RESPONSE (Student Mood GPT) ===")
response = query_model("response", "Hôm nay em được 10 điểm toán.")

# In ra đẹp hơn:
print("\n--- RESPONSE ---")
print(response["text"])
print(f"\n Source: {response['source']}")
print(f" Time: {response['timestamp']}")