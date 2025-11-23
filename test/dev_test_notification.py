# dev_test_notification.py
# ---------------------------------------------------------
# File test độc lập cho Notification Engine
# Giúp kiểm tra 4 loại notification A/B/C/D mà không cần chạy toàn pipeline.
# ---------------------------------------------------------

from core.notification_engine import generate_notification
from pprint import pprint
import time

print("================= TEST NOTIFICATION ENGINE =================")
print("Mỗi lần chạy sẽ kiểm tra tuần tự A → B → C → D")
print("Nếu đủ điều kiện → trả về thông báo đầu tiên (1 thông báo/lần)")
print("------------------------------------------------------------\n")

# Hàm chạy test nhiều lần (mô phỏng cập nhật theo thời gian)
def run_test(loop_times=1, delay=1):
    for i in range(loop_times):
        print(f"\n--- Lần test thứ {i+1} ---")
        notif = generate_notification()
        if notif:
            print("\n🔔 Thông báo được tạo:")
            pprint(notif)
        else:
            print("\n(✓) Không có thông báo nào cần gửi.")
        time.sleep(delay)

# Mặc định chạy 1 lần\-run_test(loop_times=1, delay=1)

print("\n================= KẾT THÚC TEST =================")
