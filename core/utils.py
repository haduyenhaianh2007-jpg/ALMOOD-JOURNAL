"""
core/utils.py
-----------------------------------------
Chứa các hàm tiện ích dùng chung giữa:
- Team AI (pipeline, test)
- Team Backend (server, API)
-----------------------------------------
Mục tiêu: tái sử dụng, tránh lặp code, dễ bảo trì.
"""

from datetime import datetime, timezone, timedelta
import json
import os
import re
from typing import Any, Dict, List
import numpy as np
import re

def chunk_text(text, chunk_size=300):
    """
    Chia văn bản dài thành các đoạn nhỏ (chunk) theo câu, cụm ngữ nghĩa hoặc từ nối.
    - chunk_size: độ dài tối đa mỗi chunk (tính theo ký tự)
    """
    # Tách dựa theo dấu câu hoặc từ nối
    sentences = re.split(r'(?<=[.!?]) +|(?<=, )|(?<= nhưng )|(?<= mà )|(?<= nên )', text)

    chunks = []
    current_chunk = ""

    for sent in sentences:
        if len(current_chunk) + len(sent) <= chunk_size:
            current_chunk += " " + sent
        else:
            chunks.append(current_chunk.strip())
            current_chunk = sent

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks

# ============================================================
#  1. Hàm: get_vn_timestamp()
# ------------------------------------------------------------
# Lấy thời gian hiện tại theo múi giờ Việt Nam (UTC+7)
# Dùng để gắn timestamp vào log, response, hoặc database.
# ============================================================
def get_vn_timestamp() -> str:
    """Trả về timestamp giờ Việt Nam (ISO 8601 format)."""
    vn_time = datetime.now(timezone.utc) + timedelta(hours=7)
    return vn_time.strftime("%Y-%m-%d %H:%M:%S")

# ============================================================
# 2. Hàm: append_jsonl()
# ------------------------------------------------------------
# Ghi thêm 1 dòng dữ liệu JSON vào file .jsonl
# Dùng cho test log hoặc backend ghi log người dùng.
# ============================================================
def append_jsonl(path: str, data: Dict[str, Any]) -> None:
    """
    Ghi dữ liệu dạng JSON vào file .jsonl
    Mỗi dòng = 1 JSON object.
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
        f.write("\n")

# ============================================================
#  3. Hàm: read_jsonl()
# ------------------------------------------------------------
# Đọc toàn bộ dữ liệu từ file .jsonl -> list[dict]
# Dùng trong analyze_logs.py hoặc dashboard backend.
# ============================================================
def read_jsonl(path: str) -> List[Dict[str, Any]]:
    """Đọc toàn bộ file .jsonl, trả về danh sách các dict."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Không tìm thấy file log: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(line.strip()) for line in f if line.strip()]

# ============================================================
#  4. Hàm: clean_text()
# ------------------------------------------------------------
# Làm sạch text người dùng nhập (xóa ký tự lỗi, khoảng trắng thừa)
# Dùng trước khi gửi text cho GPT để tránh lỗi encoding.
# ============================================================
def clean_text(text: str) -> str:
    """
    Chuẩn hóa text:
    - Loại bỏ ký tự không in được
    - Giảm khoảng trắng
    - Xóa ký tự điều khiển (ẩn)
    """
    text = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

# ============================================================
#  5. Hàm: normalize_sentiment()
# ------------------------------------------------------------
# Chuẩn hóa nhãn cảm xúc model trả về cho thống nhất
# (ví dụ: "POS" → "positive", "NEG" → "negative", ...)
# ============================================================
def normalize_sentiment(label: str) -> str:
    """
    Chuyển nhãn sentiment về dạng thống nhất (chuẩn hóa)
    """
    mapping = {
        "POS": "positive",
        "NEG": "negative",
        "NEU": "neutral",
        "positive": "positive",
        "negative": "negative",
        "neutral": "neutral"
    }
    return mapping.get(label.strip().upper(), "neutral")

# ============================================================
#  6. Hàm: aggregate_consistent()
# ------------------------------------------------------------
# Khi các chunk cùng hướng cảm xúc 
#  Tính weighted mean theo độ dài chunk
#Ví dụ Có 2 chunk cùng positive [0.8, 0.9] → pos≈0.85
# ============================================================
def aggregate_consistent(chunks: List[Dict[str, Any]]) -> np.ndarray:
    """
    ✅ Định nghĩa:
        Khi các chunk đều có cảm xúc cùng hướng (đều pos hoặc neg).
    ⚙️ Dấu hiệu:
        - Các label trùng nhau hoặc tương đồng >80%.
    🧮 Chiến lược:
        Weighted mean theo độ dài chunk.
    🎯 Output:
        Vector xác suất trung bình (3 lớp).
    📘 Ví dụ:
        [pos=0.8, pos=0.9] → pos≈0.85
    """
    total_weight, weighted_probs = 0, np.zeros(3)
    for c in chunks:
        w = c["length"]
        weighted_probs += np.array(c["probs"]) * w
        total_weight += w
    return weighted_probs / total_weight


# ============================================================
#  7. Hàm: aggregate_mild_shift()
# ------------------------------------------------------------
# Khi các chunk lệch nhẹ (positive ↔ neutral).
#Khi câu văn xét trên 1 vấn đề/đối tượng/khía cạnh nhưng có sự thay đổi cảm xúc nhẹ từ pos/neg sang neutral hoặc ngược lại.
#Không có sự đảo cực từ positive sang negative hoặc ngược lại.  
#Ví dụ A có 2 chunk: 
#chunk 1: positive [0.7, 0.2, 0.1] có độ dài 20
#chunk 2: neutral [0.3, 0.1, 0.6] ( pos/neu/neg) có độ dài 30
# → cảm xúc nghiêng nhẹ về positive do chunk 1 có độ dài ngắn hơn
#Tính toán probs của VD A:
#Tính độ rõ nét của mỗi chunk: công thức I = max_prob - mean_prob
#I1 = 0.7 - (0.7+0.2+0.1)/3 = 0.4667
#I2 = 0.6 - (0.3+0.1+0.6)/3 = 0.4
#Trọng số w = độ dài * (1 + I)
#w1 = 20 * (1 + 0.4667) = 29.334
#w2 = 30 * (1 + 0.4) = 42   
#Tổng trọng số w = w1 + w2 = 71.334
#Tính weighted mean probs: probs_label = Tổng (probs_chuck_i * w_i) / Tổng trọng số w ( i chạy từ 1 tới n chunk)
#pos = (0.7 * 29.334 + 0.3 * 42) / 71.334 = 0.487
#neu = (0.2 * 29.334 + 0.1 * 42) / 71.334 = 0.147
#neg = (0.1 * 29.334 + 0.6 * 42) / 71.334 = 0.366
# ============================================================
def aggregate_mild_shift(chunks: List[Dict[str, Any]]) -> np.ndarray:
    """
    ✅ Định nghĩa:
        Khi cảm xúc lệch nhẹ, không đảo cực.
    ⚙️ Dấu hiệu:
        - Các nhãn khác nhau nhưng không đối cực.
        - Chênh xác suất top-2 < 0.4
    🧮 Chiến lược:
        Weighted mean + intensity (1 + độ tự tin)
    🎯 Output:
        Cảm xúc nghiêng nhẹ về phía mạnh hơn.
    """
    total_weight, weighted_probs = 0, np.zeros(3)
    for c in chunks:
        probs = np.array(c["probs"])
        intensity = np.max(probs) - np.mean(probs)
        w = c["length"] * (1 + intensity)
        weighted_probs += probs * w
        total_weight += w
    return weighted_probs / total_weight


# ============================================================
#  8. Hàm: aggregate_polarity_shift()
# ------------------------------------------------------------
# Khi cảm xúc đảo cực rõ ràng → lấy chunk sau cùng.
#Ví dụ Có 2 chunk:
#chunk 1: positive [0.9, 0.05, 0.05]
#chunk 2: negative [0.1, 0.1, 0.8]
# → cảm xúc chính là negative (chunk 2) 
#Suy ra probs của VD:
#probs = [0.1, 0.1, 0.8]
# ============================================================
def aggregate_polarity_shift(chunks: List[Dict[str, Any]]) -> np.ndarray:
    """
    ✅ Định nghĩa:
        Khi cảm xúc đảo cực rõ (vui rồi buồn).
    ⚙️ Dấu hiệu:
        - Có liên từ đảo chiều (“nhưng”, “tuy nhiên”).
        - Chunk cuối mang hướng trái ngược.
    🧮 Chiến lược:
        Lấy xác suất chunk sau cùng.
    🎯 Output:
        Cảm xúc chính (label chunk cuối).
    """
    return chunks[-1]["probs"]


# ============================================================
#  9. Hàm: aggregate_uncertain()
# ------------------------------------------------------------
# Khi model không chắc chắn → neutral + flag.
#Ví dụ Có 2 chunk:
#chunk 1: neutral [0.4, 0.3, 0.3]
#chunk 2: neutral [0.35, 0.4, 0.25]
# → cảm xúc chính là neutral (low confidence)   
#Tính probs của VD:
#probs = [0.33, 0.34, 0.33]
# ============================================================
def aggregate_uncertain(chunks: List[Dict[str, Any]]):
    """
    ✅ Định nghĩa:
        Khi xác suất các nhãn gần nhau.
    ⚙️ Dấu hiệu:
        - max_prob - second_max_prob < 0.1
    🧮 Chiến lược:
        Trả về neutral (low confidence)
    🎯 Output:
        ([neutral=1.0], "uncertain")
    """
    return np.array([0.33, 0.34, 0.33]), "uncertain"


# ============================================================
#  10. Hàm: aggregate_multi_sentiment()
# ------------------------------------------------------------
# Khi có >=2 cảm xúc mạnh độc lập → dùng summarization.
#Dùng khi câu có chứa 2 vấn đề, 2 khía cạnh, 2 đối tượng khác nhau với cảm xúc riêng biệt, khác nhau.
#Ví dụ Có 2 chunk: 
#chunk 1: positive [0.8, 0.1, 0.1] có độ dài 25
#chunk 2: negative [0.1, 0.2, 0.7] có độ dài 35
# → cảm xúc chính là mixed_sentiment do có 2 cảm xúc mạnh song song 
#Tính probs của VD: ( Cách tính tương tự aggregate_consistent)
#probs = [0.45, 0.15, 0.4]
# ============================================================
def aggregate_multi_sentiment(chunks: List[Dict[str, Any]]):
    """
    ✅ Định nghĩa:
        Có >=2 cảm xúc mạnh độc lập, không phủ định nhau.
    ⚙️ Dấu hiệu:
        - ≥2 chunk có xác suất > 0.6 ở 2 label khác nhau.
    🧮 Chiến lược:
        Trung bình có trọng số + gắn flag “mixed_sentiment”.
    🎯 Output:
        (avg_probs, "mixed_sentiment")
    """
    total_weight, weighted_probs = 0, np.zeros(3)
    for c in chunks:
        w = c["length"]
        weighted_probs += np.array(c["probs"]) * w
        total_weight += w
    avg_probs = weighted_probs / total_weight
    return avg_probs, "mixed_sentiment"
# ============================================================
# 11. Hàm: detect_sentiment_case()
# ------------------------------------------------------------
# Nhận vào danh sách các chunk (mỗi chunk có probs, label, length, text)
# Trả về loại trường hợp cảm xúc:
#   - consistent
#   - mild_shift
#   - polarity_shift
#   - uncertain
#   - multi_sentiment
# ============================================================

def detect_sentiment_case(chunks: list) -> str:
    """
    ✅ Mục đích:
        Tự động xác định loại cảm xúc của văn bản dựa trên kết quả các chunk.

    ✅ Input (ví dụ):
        chunks = [
            {"text": "Hôm nay tôi rất vui", "probs": [0.82, 0.12, 0.06], "label": "positive", "length": 12},
            {"text": "nhưng tôi không về nhà nên hơi nhớ mẹ", "probs": [0.08, 0.20, 0.72], "label": "negative", "length": 29}
        ]

    ✅ Output:
        "consistent", "mild_shift", "polarity_shift", "uncertain", hoặc "multi_sentiment"

    ------------------------------------------------------------
    ⚙️ Logic phát hiện:

    1️⃣ UNCERTAIN
        - Nếu max_prob - second_max_prob < 0.1 với hầu hết chunk
        → model không chắc chắn → "uncertain"

    2️⃣ CONSISTENT
        - Nếu tất cả label giống nhau (hoặc sai khác <15%)
        → cùng hướng cảm xúc → "consistent"

    3️⃣ POLARITY SHIFT
        - Nếu có từ nối chuyển hướng (nhưng, tuy nhiên, song, mặc dù, trái lại)
          và label chunk cuối khác hẳn label đầu (pos ↔ neg)
        → "polarity_shift"

    4️⃣ MULTI SENTIMENT
        - Nếu có ≥2 chunk có nhãn khác nhau với xác suất > 0.6
          mà không có từ nối phủ định → song song nhiều cảm xúc
        → "multi_sentiment"

    5️⃣ MILD SHIFT
        - Nếu khác nhau nhẹ (positive ↔ neutral hoặc neutral ↔ negative)
        → "mild_shift"
    ------------------------------------------------------------
    """

    # ---- Tiền xử lý
    labels = [c["label"] for c in chunks]
    probs = [c["probs"] for c in chunks]
    texts = " ".join([c["text"] for c in chunks]).lower()

    # ---- 1. Trường hợp uncertain
    def is_uncertain_chunk(p):
        sorted_p = sorted(p, reverse=True)
        return (sorted_p[0] - sorted_p[1]) < 0.1
    if all(is_uncertain_chunk(p) for p in probs):
        return "uncertain"

    # ---- 2. Trường hợp consistent
    if len(set(labels)) == 1:
        return "consistent"

    # ---- 3. Trường hợp polarity shift
    connectors = ["nhưng", "tuy nhiên", "song", "trái lại", "mặc dù"]
    if any(conn in texts for conn in connectors):
        if labels[0] != labels[-1] and (
            ("positive" in labels and "negative" in labels)
        ):
            return "polarity_shift"

    # ---- 4. Trường hợp multi_sentiment
    strong_chunks = [c for c in chunks if max(c["probs"]) > 0.6]
    strong_labels = list({c["label"] for c in strong_chunks})
    if len(strong_labels) >= 2:
        return "multi_sentiment"

    # ---- 5. Trường hợp mild_shift
    return "mild_shift"