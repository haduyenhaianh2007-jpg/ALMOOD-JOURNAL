"""
test_hf_client.py
Unit test cho hf_client.py — kiểm tra logic xử lý mà không cần mạng.
"""

import sys, os #nhập module sys, truy cập các hàm và biến liên quan đến trình thông dịch Python và hệ điều hành
#nhập module os, cung cấp các hàm để tương tác với hệ điều hành
import pytest #framwork test tự động trong Python
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))) 
#Thêm đường dẫn tới thư mục gốc để import module core

from core.hf_client import query_model #import hàm query_model từ module core.hf_client

# --- Test sentiment (mock Hugging Face API) ---
def test_sentiment_model(monkeypatch): #kiểm tra hàm query_model với model sentiment nhưng không gọi API thật
    """Giả lập phản hồi từ Hugging Face, kiểm tra parse JSON và format."""
    import requests

    class MockResponse:
        def __init__(self): self.status_code = 200
        def raise_for_status(self): pass
        def json(self): return [{"label": "positive", "score": 0.98}]
        #Giống như server trả về: [{"label": "positive", "score": 0.98}]
    monkeypatch.setattr(requests, "post", lambda *a, **k: MockResponse())
    #Patch” tạm thời hàm requests.post thành mock function, để test chạy offline.
    result = query_model("sentiment", "I am happy!") #Gọi hàm thật, nhưng dữ liệu đầu vào và phản hồi đều giả.
    assert result["label"] == "positive"
    assert abs(result["score"] - 0.98) < 1e-3
#So sánh dữ liệu đầu ra có đúng định dạng không.
#Nếu sai, pytest sẽ báo lỗi: AssertionError.
#-----------------------------------------------------------#

# --- Test GPT response (mock OpenAI API) ---
def test_response_model(monkeypatch): #Kiểm tra nhánh GPT (response) trong query_model().
    """Giả lập phản hồi từ GPT client để kiểm tra format."""
    import core.hf_client as hf #nhập module hf_client nhưng gọi là hf để tránh trùng tên

    class MockChoices:
        def __init__(self):
            self.message = type("msg", (), {"content": "Xin chào, tôi là Student Mood GPT!"})
        #Giả lập gpt_response.choices[0].message.content.
    class MockResponse:
        def __init__(self): self.choices = [MockChoices()]
        #Giống như gpt_response thật từ API.
    class MockClient:
        def __init__(self, api_key=None): pass
        class chat:
            class completions:
                @staticmethod
                def create(*a, **k): return MockResponse()
         #Tạo client giả để trả về MockResponse.
    hf.OpenAI = MockClient #Gắn client giả vào module thật → query_model() sẽ chạy nhưng không gọi mạng.
    result = query_model("response", "Hello!")
    assert result["source"] == "student_mood_gpt"
    assert "text" in result
    #Kiểm tra JSON trả về đúng cấu trúc (text + model).
# --- Test lỗi model không tồn tại ---
def test_invalid_model():
    """Kiểm tra khi model không nằm trong config."""
    with pytest.raises(ValueError):
        query_model("unknown", "test")
#Kiểm tra xử lý ngoại lệ trong trường hợp model không có trong HF_MODELS
# -------------------------------------------------------
#  Cho phép chạy trực tiếp bằng lệnh:
# python -m test.test_hf_client
# -------------------------------------------------------
if __name__ == "__main__":
    import pytest
    # Chạy toàn bộ các test trong file này
    pytest.main(["-v", __file__])
