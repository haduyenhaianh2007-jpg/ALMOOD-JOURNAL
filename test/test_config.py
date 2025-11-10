"""
Unit test cho file config.py
Đảm bảo tất cả biến được định nghĩa và hoạt động đúng.
"""

import pytest
from core import config

def test_sentiment_config_exists():
    """Kiểm tra biến cấu hình chính có tồn tại"""
    assert hasattr(config, "SENTIMENT_API_URL")
    assert hasattr(config, "SENTIMENT_MODEL_NAME")
    assert hasattr(config, "CHUNK_SIZE")
    assert hasattr(config, "LABELS")

def test_chunk_size_value():
    """Kiểm tra giá trị chunk size"""
    assert isinstance(config.CHUNK_SIZE, int)
    assert config.CHUNK_SIZE > 0
    assert config.CHUNK_SIZE <= 1000  # Giới hạn hợp lý

def test_labels_content():
    """Kiểm tra danh sách nhãn sentiment"""
    labels = config.LABELS
    assert isinstance(labels, list)
    assert all(isinstance(l, str) for l in labels)
    assert "positive" in labels and "negative" in labels

def test_emotion_map_consistency():
    """Kiểm tra ánh xạ cảm xúc"""
    for label in config.LABELS:
        assert label in config.EMOTION_MAP, f"{label} thiếu trong EMOTION_MAP"

def test_get_vn_timestamp_format():
    """Kiểm tra hàm lấy timestamp theo múi giờ VN"""
    ts = config.get_vn_timestamp()
    # Định dạng YYYY-MM-DD HH:MM:SS
    assert len(ts) == 19 and ts[4] == "-" and ts[13] == ":", "Định dạng sai timestamp"
