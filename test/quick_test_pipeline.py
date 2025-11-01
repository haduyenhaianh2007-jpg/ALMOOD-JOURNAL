"""
======================================================
🎯 AI Mood Journal — Quick Pipeline Test
------------------------------------------------------
File này dùng để:
✅ Kiểm tra toàn bộ pipeline AI (sentiment + GPT)
✅ Hiển thị kết quả test đẹp mắt trong terminal (bằng rich)
✅ Ghi log JSON (để team AI phân tích lại sau)
✅ Cho phép xem lại log cũ nhanh bằng flag --view
------------------------------------------------------
Cấu trúc gọi:
    python -m test.quick_test_pipeline
    python -m test.quick_test_pipeline --view
======================================================

--- CẢI TIẾN (v2) ---
- Sửa logic để lưu log test ra MỘT file .json DUY NHẤT (chứa 1 list)
  thay vì file .jsonl (nhiều dòng).
- Sửa hàm view_logs để đọc file .json mới này.
--- HẾT CẢI TIẾN ---
"""

import json # <-- Import thư viện json chuẩn của Python
import os
import sys
from datetime import datetime

# -------------------------------------------------------
# 🔹 Import pipeline chính (điều phối sentiment + GPT)
# -------------------------------------------------------
from core.pipeline import run_ai_pipeline, print_pipeline_result

# -------------------------------------------------------
# 🔹 Import các hàm tiện ích chung
# -------------------------------------------------------
# (Chúng ta sẽ không dùng append_jsonl và read_jsonl từ utils nữa)
# from core.utils import append_jsonl, read_jsonl # <-- BỊ THAY THẾ


# -------------------------------------------------------
# 🖌️ (Tùy chọn) Màu fallback nếu máy chưa cài rich
# -------------------------------------------------------
class Color:
    HEADER = "\033[95m"   # Màu tím (thường dùng cho tiêu đề lớn)
    OKBLUE = "\033[94m"   # Màu xanh dương (dùng cho text bình thường)
    OKCYAN = "\033[96m"   # Màu xanh ngọc (dùng cho highlight nhẹ)
    OKGREEN = "\033[92m"  # Màu xanh lá (thường cho thông báo "OK" hoặc thành công)
    WARNING = "\033[93m"  # Màu vàng (cảnh báo, nhắc nhở)
    FAIL = "\033[91m"     # Màu đỏ (lỗi, thất bại)
    ENDC = "\033[0m"      # Reset lại màu về mặc định (bắt buộc để kết thúc đoạn)
    BOLD = "\033[1m"      # In đậm (dùng để nhấn mạnh)

# === KHỐI CẤU HÌNH LOG (Đã sửa) ===
LOG_DIR = "logs"
# --- SỬA 1: Đổi tên file log từ .jsonl sang .json ---
LOG_FILE_NAME = "pipeline_log.json"
LOG_FILE_PATH = os.path.join(LOG_DIR, LOG_FILE_NAME)


# ============================================================
#  1️. Hàm: save_results_to_json() (HÀM MỚI thay thế log_pipeline_result)
# ------------------------------------------------------------
# (Hàm này thay thế cho log_pipeline_result() cũ)
# Ghi lại TOÀN BỘ kết quả test (dạng list) vào 1 file .json duy nhất.
# ============================================================
def save_results_to_json(results_list: list, log_path: str):
    """
    Ghi toàn bộ list kết quả vào MỘT file .json.
    (Thay thế cho hàm append_jsonl)
    """
    print(f"\nĐang lưu {len(results_list)} kết quả vào {log_path}...")
    try:
        os.makedirs(os.path.dirname(log_path), exist_ok=True) # Tự tạo thư mục logs nếu chưa có
        # Mở file ở chế độ 'w' (write - ghi đè)
        with open(log_path, "w", encoding="utf-8") as f:
            # Dùng json.dump() để lưu cả list
            # ensure_ascii=False để giữ tiếng Việt
            # indent=4 để file .json dễ đọc (đẹp)
            json.dump(results_list, f, ensure_ascii=False, indent=4)
        print(f"{Color.OKGREEN}✅ Đã lưu thành công!{Color.ENDC}")
    except Exception as e:
        print(f"{Color.FAIL}❌ Lỗi khi lưu file JSON: {e}{Color.ENDC}")


# ============================================================
# 2. Hàm: view_logs() (ĐÃ SỬA)
# ------------------------------------------------------------
# (Hàm này được sửa để đọc file .json thay vì .jsonl)
# ============================================================
def view_logs(log_dir="logs"):
    """Đọc lại log pipeline đã lưu (từ file .json)"""
    # --- SỬA 2: Path giờ trỏ đến file .json ---
    log_file = os.path.join(log_dir, LOG_FILE_NAME) # Dùng LOG_FILE_NAME mới

    # Nếu chưa có log nào, in thông báo
    if not os.path.exists(log_file):
        print(f"{Color.FAIL}❌ Không tìm thấy file log nào tại: {log_file}{Color.ENDC}")
        return

    print(f"{Color.HEADER}\n=== 📘 ĐỌC LẠI LOG CŨ ({log_file}) ==={Color.ENDC}\n")

    try:
        # --- SỬA 3: Đọc file .json (1 lần) ---
        # Mở file ở chế độ 'r' (read)
        with open(log_file, "r", encoding="utf-8") as f:
            # Dùng json.load() để đọc 1 file JSON (nó sẽ là 1 list)
            logs = json.load(f) 
        
        # Đảm bảo logs là một list (như chúng ta đã lưu)
        if not isinstance(logs, list):
            print(f"{Color.FAIL}❌ File log có định dạng sai (không phải list).{Color.ENDC}")
            return
            
        # Hiển thị từng case một
        for i, data in enumerate(logs, 1):
            print(f"{Color.OKBLUE}\n🧩 CASE {i}:{Color.ENDC}")
            print_pipeline_result(data)  # Hàm này hiển thị bảng màu bằng rich

    except json.JSONDecodeError:
        print(f"{Color.FAIL}❌ File log {log_file} bị lỗi JSON.{Color.ENDC}")
    except Exception as e:
        print(f"{Color.FAIL}❌ Lỗi khi đọc log: {e}{Color.ENDC}")


# ============================================================
# 3. Hàm: test_pipeline() (ĐÃ SỬA)
# ------------------------------------------------------------
# (Hàm này được sửa để gom kết quả vào list, và chỉ lưu 1 lần)
# ============================================================
def test_pipeline():
    """Chạy test pipeline với nhiều input mẫu"""

    # Bộ test mẫu (bạn có thể thêm tuỳ ý)
    test_cases = [
            "Hải Anh đang tức giận vì bị bạn bè bỏ rơi trong buổi tiệc sinh nhật.",
            "Team mình vừa thắng giải cuộc thi lập trình quốc gia! Mình vui lắm luôn!",
            "Ngày mai mình sẽ nghỉ học vì mình không cảm thấy gì đặc biệt.",
    ] # Giữ nguyên các test case của bạn

    # In header bắt đầu test
    print(f"{Color.HEADER}\n=== 🚀 BẮT ĐẦU TEST PIPELINE ==={Color.ENDC}")

    # --- SỬA 4: Tạo 1 list rỗng để gom kết quả ---
    # Thay vì ghi từng dòng, chúng ta gom vào đây
    all_results = []

    # Vòng lặp chạy từng câu test
    for i, text in enumerate(test_cases, start=1):
        print(f"\n{Color.BOLD}--- TEST CASE {i} ---{Color.ENDC}")
        print(f"{Color.OKBLUE}User input:{Color.ENDC} {text}")

        # 1️. Gọi pipeline chính (chạy sentiment + GPT)
        result = run_ai_pipeline(text) # Gọi hàm từ pipeline.py

        # 2️. In kết quả đẹp bằng rich (hàm print_pipeline_result nằm trong pipeline.py)
        print_pipeline_result(result)

        # 3️. (ĐÃ SỬA) Thêm kết quả vào list (thay vì ghi log ngay)
        all_results.append(result)

    # --- SỬA 5: Lưu file 1 LẦN DUY NHẤT (sau khi vòng lặp kết thúc) ---
    # Gọi hàm (Khối 1) để lưu toàn bộ list `all_results`
    save_results_to_json(all_results, LOG_FILE_PATH)


# ============================================================
#  4. Entry Point (main)
# ------------------------------------------------------------
# (Logic này giữ nguyên, nhưng giờ nó sẽ gọi các hàm v2 đã sửa)
# ============================================================
if __name__ == "__main__":
    # Nếu user gọi "python -m test.quick_test_pipeline --view"
    if len(sys.argv) > 1 and sys.argv[1] in ["--view", "--view-log"]:
        view_logs() # Sẽ gọi hàm view_logs() (Khối 2) đã sửa
    # Ngược lại, chạy test mới
    else:
        test_pipeline() # Sẽ gọi hàm test_pipeline() (Khối 3) đã sửa