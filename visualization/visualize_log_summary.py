# Tên file: visualize_log_summary.py
"""
Mô tả:
Script này là một CÔNG CỤ NỘI BỘ (Internal Tool) của team AI.

Chức năng:
Được thiết kế để xử lý SỐ LƯỢNG LOG LỚN (ví dụ: 50+, 500+).
Nó không vẽ chi tiết từng log, mà TÓM TẮT (Summarize) toàn bộ dữ liệu 
thành một Bảng điều khiển (Dashboard) gồm 2 biểu đồ:
1. Count Plot: Cho thấy SỐ LƯỢNG dự đoán của mỗi nhãn (POS, NEG, NEU).
2. Box Plot: Cho thấy SỰ PHÂN BỔ của điểm tin cậy (score) cho mỗi nhãn,
   giúp phát hiện các vấn đề về độ ổn định hoặc các điểm ngoại lai (outliers).

Mục đích:
Giúp team AI (Hải Anh) và Data (Linh)
báo cáo tổng quan về chất lượng mô hình khi chạy test hàng loạt.
"""

# === KHỐI 1: IMPORT THƯ VIỆN ===
import os  # Dùng cho các thao tác với Hệ điều hành (OS)
           # (ví dụ: kiểm tra thư mục, tạo đường dẫn file)
import glob  # Dùng để tìm kiếm file hàng loạt theo một "khuôn mẫu"
           # (ví dụ: tìm tất cả file *.json)
import json  # Dùng để đọc (parse) dữ liệu từ file JSON
import pandas as pd  # Thư viện xử lý dữ liệu dạng bảng (DataFrame)
import matplotlib.pyplot as plt  # Thư viện "nền tảng" để vẽ biểu đồ 2D
import seaborn as sns  # Thư viện "cấp cao" hơn, giúp vẽ biểu đồ
                       # thống kê (như boxplot, countplot) đẹp hơn
import numpy as np # Thư viện tính toán khoa học, 
                   # (Seaborn đôi khi cần numpy cho các tính toán thống kê)

# === KHỐI 2: CẤU HÌNH TRUNG TÂM ===

# --- TÌM ĐƯỜNG DẪN GỐC CỦA DỰ ÁN ---
# __file__ là đường dẫn tuyệt đối đến file script này
# (vd: /Users/haianh/project/visualization/visualize_log_summary.py)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# os.path.join(SCRIPT_DIR, '..') sẽ đi "lên" một cấp
# (vd: /Users/haianh/project)
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '..'))

# --- CẤU HÌNH ĐƯỜNG DẪN ĐỘNG (Dynamic Paths) ---
# Giờ chúng ta ghép đường dẫn GỐC với thư mục 'logs' một cách an toàn
LOG_DIRECTORY = os.path.join(PROJECT_ROOT, 'logs') 

# Và ghép đường dẫn GỐC với file output
OUTPUT_IMAGE_FILE = os.path.join(PROJECT_ROOT, 'sentiment_analysis_SUMMARY.png')

# (Nếu bạn dùng file all_logs, hãy đổi tên file output tương ứng)
# OUTPUT_IMAGE_FILE = os.path.join(PROJECT_ROOT, 'sentiment_analysis_chart_tong_hop.png')
# === KHỐI 3: HÀM CHỨC NĂNG CHÍNH ===

def visualize_summary(log_dir):
    """
    Hàm chính, thực hiện toàn bộ quy trình:
    1. Quét thư mục `log_dir` để tìm file.
    2. Đọc và tổng hợp dữ liệu JSON.
    3. Chuyển dữ liệu sang Pandas DataFrame.
    4. Vẽ 2 biểu đồ tóm tắt (Countplot và Boxplot) lên CÙNG 1 ảnh.
    """
    
    # --- 3.1. Tìm và Đọc tất cả file Log ---
    # (Logic này giống hệt file visualize_all_logs.py)
    json_pattern = os.path.join(log_dir, '*.json')
    log_files = glob.glob(json_pattern)

    if not log_files:
        print(f"Lỗi: Không tìm thấy file .json nào trong '{log_dir}'.")
        return
    
    all_data = []
    for file_path in log_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data_in_file = json.load(f)
                all_data.extend(data_in_file)
        except Exception as e:
            print(f"Cảnh báo: Lỗi khi đọc file {file_path}: {e}. Bỏ qua.")

    if not all_data:
        print("Lỗi: Không có dữ liệu hợp lệ nào được đọc.")
        return

    # --- 3.2. Trích xuất Dữ liệu cho Tóm tắt ---
    
    records = []
    for entry in all_data:
        if entry.get("status") == "success":
            # Với biểu đồ tóm tắt, chúng ta KHÔNG cần 'input_text'
            # Chúng ta chỉ cần 'label' và 'score'
            records.append({
                "label": entry['sentiment']['label'],
                "score": entry['sentiment']['score']
            })

    if not records:
        print("Lỗi: Không tìm thấy entry 'success' nào.")
        return

    # --- 3.3. Chuyển sang Pandas DataFrame ---
    df = pd.DataFrame(records)
    print(f"Đã xử lý {len(df)} kết quả 'success'. Bắt đầu vẽ biểu đồ tóm tắt...")

    # --- 3.4. VẼ BIỂU ĐỒ TÓM TẮT (PHẦN NÂNG CẤP) ---
    
    # 3.4.1. Cấu hình Font (Giống hệt file cũ)
    plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans']
    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['axes.unicode_minus'] = False 

    # 3.4.2. Khởi tạo khung biểu đồ (Figure và Subplots)
    # plt.subplots(rows, cols, figsize)
    # Chúng ta tạo MỘT 'figure' (ảnh) chứa 1 hàng, 2 cột (axes)
    # 'fig' là toàn bộ bức ảnh
    # 'ax1' là biểu đồ bên trái (axes[0])
    # 'ax2' là biểu đồ bên phải (axes[1])
    fig, (ax1, ax2) = plt.subplots(
        nrows=1, 
        ncols=2, 
        figsize=(16, 7) # Kích thước tổng (16 inch rộng, 7 inch cao)
    )
    
    # Đặt tiêu đề chung (Super Title) cho cả bức ảnh 'fig'
    fig.suptitle(f'Báo cáo Tóm tắt Phân tích Sentiment ({len(df)} lượt test)',
                 fontsize=18, 
                 y=1.02 # Đẩy tiêu đề lên cao một chút (trên 1.0)
    )

    # 3.4.3. Vẽ Biểu đồ 1 (Bên trái): Count Plot (Biểu đồ đếm)
    
    # 'order' để sắp xếp các cột theo thứ tự mong muốn
    label_order = ['POS', 'NEU', 'NEG']
    
    # sns.countplot: Tự động đếm số lần xuất hiện của mỗi giá trị trong cột 'x'
    sns.countplot(
        data=df, 
        x='label',         # Dữ liệu trục X là cột 'label'
        order=label_order, # Sắp xếp cột theo 'label_order'
        ax=ax1,            # Chỉ định vẽ lên 'ax1' (ô bên trái)
        palette={'POS': '#2ecc71', 'NEG': '#e74c3c', 'NEU': '#3498db'} # Tô màu
    )
    ax1.set_title('Tổng số lượng dự đoán', fontsize=14)
    ax1.set_xlabel('Nhãn Cảm xúc', fontsize=12)
    ax1.set_ylabel('Số lượng (Count)', fontsize=12)
    
    # Thêm số lượng lên trên đầu mỗi cột (annotation)
    for p in ax1.patches:
        ax1.annotate(
            f'{p.get_height()}', # Nội dung text (là chiều cao của cột)
            (p.get_x() + p.get_width() / 2., p.get_height()), # Tọa độ (x, y)
            ha='center',        # Căn giữa theo chiều ngang
            va='center',        # Căn giữa theo chiều dọc
            xytext=(0, 5),      # Đẩy text lên 5 pixel
            textcoords='offset points'
        )

    # 3.4.4. Vẽ Biểu đồ 2 (Bên phải): Box Plot (Biểu đồ hộp)
    
    # sns.boxplot: Hiển thị phân bổ dữ liệu
    # - Đường kẻ giữa hộp: Trung vị (median - 50%)
    # - Đáy và đỉnh hộp: Phân vị 25% (Q1) và 75% (Q3)
    # - Các "râu": Phạm vi dữ liệu (không tính ngoại lai)
    # - Các dấu chấm (nếu có): Điểm ngoại lai (Outliers)
    sns.boxplot(
        data=df, 
        x='label',         # Trục X là cột 'label'
        y='score',         # Trục Y là cột 'score' (phân bổ điểm)
        order=label_order, # Sắp xếp cột
        ax=ax2,            # Chỉ định vẽ lên 'ax2' (ô bên phải)
        palette={'POS': '#2ecc71', 'NEG': '#e74c3c', 'NEU': '#3498db'}
    )
    
    # (Tùy chọn) Thêm 'stripplot' để vẽ các điểm dữ liệu
    # Chồng lên 'boxplot' giúp xem rõ các điểm dữ liệu
    sns.stripplot(
        data=df, 
        x='label', 
        y='score', 
        order=label_order,
        ax=ax2,
        color='black', # Màu của các điểm
        size=3,        # Kích thước điểm
        alpha=0.5      # Độ trong suốt (giảm độ chói khi có nhiều điểm)
    )
    
    ax2.set_title('Phân bổ Độ tin cậy (Score) của Model', fontsize=14)
    ax2.set_xlabel('Nhãn Cảm xúc', fontsize=12)
    ax2.set_ylabel('Độ tin cậy (Score)', fontsize=12)
    ax2.set_ylim(0, 1.1) # Set trục Y từ 0 đến 1.1

    # --- 3.5. LƯU VÀ HIỂN THỊ ---
    
    # Căn chỉnh layout tự động để 2 biểu đồ và tiêu đề không bị đè lên nhau
    # rect=[left, bottom, right, top] để điều chỉnh khoảng đệm cho suptitle
    plt.tight_layout(rect=[0, 0.03, 1, 0.95]) 
    
    try:
        # Lưu toàn bộ 'figure' (chứa cả 2 biểu đồ) ra file
        plt.savefig(OUTPUT_IMAGE_FILE)
        print(f"\n===> THÀNH CÔNG! Đã lưu biểu đồ tóm tắt vào: {OUTPUT_IMAGE_FILE}")
    except Exception as e:
        print(f"Lỗi khi lưu file ảnh: {e}")
    
    plt.show() # Mở cửa sổ hiển thị biểu đồ

# === KHỐI 5: ĐIỂM KHỞI CHẠY SCRIPT ===
if __name__ == "__main__":
    # Kiểm tra thư mục 'logs' trước khi chạy
    if not os.path.exists(LOG_DIRECTORY):
        os.makedirs(LOG_DIRECTORY)
        print(f"Đã tạo thư mục '{LOG_DIRECTORY}'. Vui lòng thêm file log và chạy lại.")
    else:
        # Nếu thư mục tồn tại, gọi hàm chính
        visualize_summary(LOG_DIRECTORY)