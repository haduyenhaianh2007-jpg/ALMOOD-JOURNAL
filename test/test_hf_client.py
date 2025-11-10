"""
Unit test cho hf_client.py (phiên bản sentiment v2)
Đảm bảo hoạt động ổn định với cấu trúc trả về mới (predicted_label, label_distribution, ...).
"""

import sys, os
import pytest

# Thêm đường dẫn để import core
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.hf_client import query_model


# --- TEST 1: Sentiment model ---
def test_sentiment_model(monkeypatch):
    """Giả lập phản hồi từ Hugging Face Space, kiểm tra tính toán softmax & cấu trúc."""
    import requests

    class MockResponse:
        def __init__(self):
            self.status_code = 200
        def raise_for_status(self): pass
        def json(self):
            return {"predicted_label": "positive", "raw_logits": [[-0.5, 0.2, 2.3]]}

    monkeypatch.setattr(requests, "post", lambda *a, **k: MockResponse())

    result = query_model("sentiment", "Hôm nay tôi rất vui!")

    # Kiểm tra key & dữ liệu
    assert "predicted_label" in result
    assert isinstance(result["label_distribution"], dict)
    assert abs(sum(result["label_distribution"].values()) - 100) < 1e-3
    print("\n[TEST SENTIMENT]", result)


# --- TEST 2: Response (Gemini) ---
def test_response_model(monkeypatch):
    """Giả lập phản hồi từ Gemini để test format."""
    import core.hf_client as hf

    class MockGenerativeModel:
        def generate_content(self, text, generation_config=None):
            class Resp:
                text = "Xin chào, tôi là Student Mood GPT!"
            return Resp()

    hf.gemini_model = MockGenerativeModel()

    result = query_model("response", "Hello!")
    assert "text" in result
    assert result["source"] == "google_gemini_2.5_flash"
    print("\n[TEST RESPONSE]", result)


# --- TEST 3: Model không tồn tại ---
def test_invalid_model():
    """Kiểm tra xử lý khi model không nằm trong danh sách hỗ trợ."""
    result = query_model("unknown", "test")
    assert "error" in result
    assert "không được hỗ trợ" in result["error"]
    print("\n[TEST INVALID]", result)


# --- Cho phép chạy trực tiếp ---
if __name__ == "__main__":
    pytest.main(["-v", __file__])
