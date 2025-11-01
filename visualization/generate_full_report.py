# Tên file: visualization/generate_full_report.py
"""
Script "Master Report"
Mục đích:
1. Đọc tất cả file log TRONG 1 LẦN.
2. Tạo ra CẢ HAI biểu đồ (chi tiết VÀ tóm tắt).
3. Lưu cả hai biểu đồ vào MỘT FILE PDF DUY NHẤT (mỗi biểu đồ 1 trang).
"""

# === KHỐI 1: IMPORT THƯ VIỆN ===
import os
import glob
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
# IMPORT MỚI: Thư viện để ghi PDF đa trang
from matplotlib.backends.backend_pdf import PdfPages

# === KHỐI 2: CẤU HÌNH ĐƯỜNG DẪN (Robust Path Config) ===

# Đường dẫn tuyệt đối đến file script này
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Đi "lên" một cấp để lấy thư mục gốc của dự án
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '..'))

# Cấu hình đường dẫn động (Dynamic Paths)
LOG_DIRECTORY = os.path.join(PROJECT_ROOT, 'logs') 
# Tên file PDF báo cáo
OUTPUT_PDF_FILE = os.path.join(PROJECT_ROOT, 'AI_Sentiment_Full_Report.pdf')

# Cấu hình Font (cho tất cả biểu đồ)
plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans']
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['axes.unicode_minus'] = False 

# === KHỐI 3: HÀM TẢI DỮ LIỆU (Chỉ chạy 1 lần) ===
def load_log_data(log_dir):
    """
    Quét thư mục log_dir, đọc tất cả file .json,
    trích xuất record 'success' và trả về một Pandas DataFrame.
    Trả về None nếu có lỗi.
    """
    json_pattern = os.path.join(log_dir, '*.json')
    log_files = glob.glob(json_pattern)
    if not log_files:
        print(f"Lỗi: Không tìm thấy file .json nào trong '{log_dir}'.")
        return None
    
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
        return None

    records = []
    for entry in all_data:
        if entry.get("status") == "success":
            records.append({
                "input_text": entry['input_text'],
                "label": entry['sentiment']['label'],
                "score": entry['sentiment']['score']
            })
    
    if not records:
        print("Lỗi: Không tìm thấy entry 'success' nào.")
        return None
        
    print(f"Đã tải {len(records)} kết quả 'success'. Bắt đầu tạo báo cáo...")
    return pd.DataFrame(records)

# === KHỐI 4: HÀM VẼ CÁC BIỂU ĐỒ ===
# (Các hàm này sẽ trả về đối tượng 'Figure' thay vì tự động show)

def create_all_logs_figure(df):
    """
    Tạo biểu đồ CHI TIẾT (giống visualize_all_logs.py)
    Trả về đối tượng Figure của Matplotlib.
    """
    # Làm ngắn text để hiển thị
    df['text_display'] = [f"({i+1}) {text[:40]}..." for i, text in enumerate(df['input_text'])]
    
    num_records = len(df)
    # Tạo Figure (fig)
    fig = plt.figure(figsize=(12, max(6, num_records * 0.8))) 
    
    # Vẽ lên Figure
    sns.barplot(
        data=df,
        x='score',
        y='text_display',
        hue='label',
        palette={'POS': '#2ecc71', 'NEG': '#e74c3c', 'NEU': '#3498db'},
        dodge=False
    )
    plt.title(f'Báo cáo Chi tiết Sentiment ({num_records} lượt test)', fontsize=16)
    plt.xlabel('Độ tin cậy (Score)', fontsize=12)
    plt.ylabel('Nội dung Input (Rút gọn)', fontsize=12)
    plt.xlim(0, 1.1)
    # (Bỏ qua phần ghi số liệu để biểu đồ sạch hơn, 
    # bạn có thể thêm lại code 'for p in barplot.patches...' ở đây nếu muốn)
    plt.legend(title='Cảm xúc', loc='lower right')
    plt.tight_layout()
    
    return fig # Trả về đối tượng Figure

def create_summary_figure(df):
    """
    Tạo biểu đồ TÓM TẮT (giống visualize_log_summary.py)
    Trả về đối tượng Figure của Matplotlib.
    """
    num_records = len(df)
    # Tạo Figure (fig) và 2 Axes (ax1, ax2)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))
    fig.suptitle(f'Báo cáo Tóm tắt Phân tích Sentiment ({num_records} lượt test)',
                 fontsize=18, y=1.02)
    
    label_order = ['POS', 'NEU', 'NEG']
    
    # --- Biểu đồ 1: Count Plot ---
    sns.countplot(
        data=df, x='label', order=label_order, ax=ax1,
        palette={'POS': '#2ecc71', 'NEG': '#e74c3c', 'NEU': '#3498db'}
    )
    ax1.set_title('Tổng số lượng dự đoán', fontsize=14)
    # (Bỏ qua phần annotation số trên cột cho ngắn gọn,
    # bạn có thể thêm lại code 'for p in ax1.patches...' ở đây)
    
    # --- Biểu đồ 2: Box Plot ---
    sns.boxplot(
        data=df, x='label', y='score', order=label_order, ax=ax2,
        palette={'POS': '#2ecc71', 'NEG': '#e74c3c', 'NEU': '#3498db'}
    )
    sns.stripplot(
        data=df, x='label', y='score', order=label_order, ax=ax2,
        color='black', size=3, alpha=0.5
    )
    ax2.set_title('Phân bổ Độ tin cậy (Score)', fontsize=14)
    ax2.set_ylim(0, 1.1)
    
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    
    return fig # Trả về đối tượng Figure

# === KHỐI 5: HÀM MAIN (ĐIỂM KHỞI CHẠY) ===
if __name__ == "__main__":
    
    # 1. Tải dữ liệu
    df = load_log_data(LOG_DIRECTORY)
    
    # 2. Kiểm tra nếu data tải thành công
    if df is not None:
        
        # 3. Mở file PDF để ghi
        # 'with ... as pdf:' sẽ tự động tạo và đóng file PDF
        print(f"Đang tạo báo cáo PDF... lưu tại {OUTPUT_PDF_FILE}")
        with PdfPages(OUTPUT_PDF_FILE) as pdf:
            
            # --- Trang 1: Biểu đồ Tóm tắt ---
            fig_summary = create_summary_figure(df)
            pdf.savefig(fig_summary) # Lưu fig_summary vào 1 trang PDF
            plt.close(fig_summary)   # Đóng figure này lại để giải phóng bộ nhớ
            print("Đã thêm Trang 1 (Tóm tắt) vào PDF.")

            # --- Trang 2: Biểu đồ Chi tiết ---
            fig_all_logs = create_all_logs_figure(df)
            pdf.savefig(fig_all_logs) # Lưu fig_all_logs vào 1 trang PDF mới
            plt.close(fig_all_logs)   # Đóng figure này lại
            print("Đã thêm Trang 2 (Chi tiết) vào PDF.")

        print(f"\n===> THÀNH CÔNG! Đã tạo báo cáo tại: {OUTPUT_PDF_FILE}")