# Tên file: test/quick_test_pipeline.py
# (Phiên bản v2 - Sửa lỗi .jsonl + Thêm user_id)

import json
import os
import sys
from datetime import datetime

# Import 2 hàm đã được CẢI TIẾN
from core.pipeline import run_ai_pipeline, print_pipeline_result

# (Giữ nguyên Class Color...)
class Color:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"

# === KHỐI CẤU HÌNH LOG (Đã sửa) ===
LOG_DIR = "logs"
LOG_FILE_NAME = "pipeline_log.json" # <-- SỬA 1: Đổi tên thành .json
LOG_FILE_PATH = os.path.join(LOG_DIR, LOG_FILE_NAME)

# === (SỬA) KHỐI 1: HÀM LƯU LOG ===
def save_results_to_json(results_list: list, log_path: str):
    """Ghi toàn bộ list kết quả vào MỘT file .json."""
    print(f"\nĐang lưu {len(results_list)} kết quả vào {log_path}...")
    try:
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, "w", encoding="utf-8") as f:
            # Dùng json.dump() để lưu cả list (đẹp)
            json.dump(results_list, f, ensure_ascii=False, indent=4)
        print(f"{Color.OKGREEN}✅ Đã lưu thành công!{Color.ENDC}")
    except Exception as e:
        print(f"{Color.FAIL}❌ Lỗi khi lưu file JSON: {e}{Color.ENDC}")

# === (SỬA) KHỐI 2: HÀM XEM LOG ===
def view_logs(log_path=LOG_FILE_PATH):
    """Đọc lại log pipeline đã lưu (từ file .json)."""
    if not os.path.exists(log_path):
        print(f"{Color.FAIL}❌ Không tìm thấy file log nào tại: {log_path}{Color.ENDC}")
        return
    print(f"{Color.HEADER}\n=== 📘 ĐỌC LẠI LOG CŨ ({log_path}) ==={Color.ENDC}\n")
    try:
        with open(log_path, "r", encoding="utf-8") as f:
            logs = json.load(f) # <-- SỬA 2: Dùng json.load()
        
        if not isinstance(logs, list):
            print(f"{Color.FAIL}❌ File log có định dạng sai (không phải list).{Color.ENDC}")
            return
            
        for i, data in enumerate(logs, 1):
            print(f"{Color.OKBLUE}\n🧩 CASE {i}:{Color.ENDC}")
            print_pipeline_result(data) 
    except Exception as e:
        print(f"{Color.FAIL}❌ Lỗi khi đọc log: {e}{Color.ENDC}")

# === (SỬA) KHỐI 3: HÀM TEST ===
def test_pipeline():
    """Chạy test pipeline (v2 - có user_id)"""

    # (Giữ nguyên test cases của bạn)
    test_cases = [
        "Tôi muốn tự tử vì sắp thi rồi mà tôi khá stress do không cân bằng được việc học và làm ở lớp IT1 - ĐH Bách Khoa Hà Nội, do mọi người ở đây giỏi khiến tôi áp lực.",
        "Tôi rất nhớ nhà vì mẹ rất yêu tôi và tôi cũng vậy.",
        "Ngày mai mình sẽ nghỉ học vì mình không cảm thấy gì đặc biệt.",
        "Hôm nay mình vui lắm, được điểm cao môn Toán! 😄"
    ]

    print(f"{Color.HEADER}\n=== 🚀 BẮT ĐẦU TEST PIPELINE ==={Color.ENDC}")
    
    all_results = [] # Gom kết quả vào list

    for i, text in enumerate(test_cases, start=1):
        print(f"\n{Color.BOLD}--- TEST CASE {i} ---{Color.ENDC}")
        print(f"{Color.OKBLUE}User input:{Color.ENDC} {text}")

        # --- SỬA 3: Thêm user_id="test_user_01" ---
        # (Để kích hoạt hàm _get_user_history_summary trong pipeline.py)
        result = run_ai_pipeline(text, user_id="test_user_01")

        print_pipeline_result(result)
        all_results.append(result)

    # --- SỬA 4: Lưu file 1 LẦN DUY NHẤT ---
    save_results_to_json(all_results, LOG_FILE_PATH)

# === KHỐI 4: MAIN (Giữ nguyên) ===
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ["--view", "--view-log"]:
        view_logs()
    else:
        test_pipeline()