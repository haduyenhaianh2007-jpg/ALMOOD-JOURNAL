# Tên file: visualize_all_logs.py
"""
Mô tả:
Script này là một CÔNG CỤ NỘI BỘ (Internal Tool) của team AI.

Chức năng:
1. Tự động QUÉT (scan) thư mục `LOG_DIRECTORY` (mặc định là 'logs/').
2. TÌM TẤT CẢ các file log có đuôi .json.
3. ĐỌC và TỔNG HỢP (aggregate) dữ liệu từ tất cả file đó.
4. Trích xuất các kết quả 'sentiment' (cảm xúc) thành công.
5. Dùng Pandas, Matplotlib và Seaborn để VẼ một biểu đồ cột ngang.
6. HIỂN THỊ (show) biểu đồ và LƯU (save) lại thành file ảnh.

Mục đích:
Giúp team AI và Data đánh giá chất lượng của mô hình sentiment
qua nhiều lượt test khác nhau.
"""

# === KHỐI 1: IMPORT THƯ VIỆN ===
import os  # Dùng cho các thao tác với Hệ điều hành (OS) 
           # (ví dụ: kiểm tra thư mục, tạo đường dẫn file)
import glob  # Dùng để tìm kiếm file hàng loạt theo một "khuôn mẫu"
           # (ví dụ: tìm tất cả file *.json)
import json  # Dùng để đọc (parse) dữ liệu từ file JSON
import pandas as pd  # Thư viện mạnh nhất để xử lý dữ liệu dạng bảng
                   # (Chúng ta dùng cấu trúc DataFrame của nó)
import matplotlib.pyplot as plt  # Thư viện "nền tảng" để vẽ biểu đồ 2D
import seaborn as sns  # Thư viện "cấp cao" hơn, giúp vẽ biểu đồ
                       # thống kê đẹp hơn (dựa trên Matplotlib)

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

def visualize_all_logs_in_directory(log_dir):
    """
    Hàm chính, thực hiện toàn bộ quy trình:
    1. Quét thư mục `log_dir` để tìm file.
    2. Đọc và tổng hợp dữ liệu JSON.
    3. Chuyển dữ liệu sang Pandas DataFrame.
    4. Vẽ, tinh chỉnh và lưu biểu đồ.
    """
    
    # --- 3.1. Tìm và Đọc tất cả file Log ---
    
    # Tạo một "khuôn mẫu" (pattern) tìm kiếm.
    # os.path.join sẽ tự động xử lý dấu '/' (Mac/Linux) hoặc '\' (Windows)
    # Kết quả sẽ là chuỗi: 'logs/*.json'
    json_pattern = os.path.join(log_dir, '*.json')
    
    # glob.glob(pattern) sẽ tìm và trả về một LIST
    # chứa đường dẫn (chuỗi) của tất cả file khớp.
    log_files = glob.glob(json_pattern)

    # Kiểm tra phòng thủ: Nếu không tìm thấy file nào
    if not log_files:
        print(f"Lỗi: Không tìm thấy file .json nào trong thư mục '{log_dir}'.")
        print("Vui lòng kiểm tra lại biến 'LOG_DIRECTORY' hoặc đảm bảo bạn đã lưu log.")
        return # Dừng hàm

    print(f"Tìm thấy {len(log_files)} file log. Đang tổng hợp...")
    
    # Khởi tạo một list rỗng để *gộp* dữ liệu từ *nhiều* file
    all_data = [] 
    
    # Vòng lặp qua từng đường dẫn file (ví dụ: 'logs/log1.json', 'logs/log2.json'...)
    for file_path in log_files:
        try:
            # Mở file ở chế độ 'r' (read) với mã hóa 'utf-8' (chuẩn cho Tiếng Việt)
            # 'with open(...)' là cách chuẩn, nó tự động đóng file
            with open(file_path, 'r', encoding='utf-8') as f:
                # json.load(f) đọc file và chuyển chuỗi JSON thành cấu trúc Python
                # (Dựa trên file log bạn gửi, đây sẽ là một LIST các DICT)
                data_in_file = json.load(f)
                
                # Dùng .extend() để nối các phần tử của 'data_in_file'
                # vào list 'all_data'.
                # (Không dùng .append() vì nó sẽ tạo list lồng nhau)
                all_data.extend(data_in_file) 
        except json.JSONDecodeError:
            print(f"Cảnh báo: File {file_path} bị lỗi JSON hoặc rỗng. Bỏ qua.")
        except Exception as e:
            print(f"Cảnh báo: Lỗi không xác định khi đọc file {file_path}: {e}. Bỏ qua.")

    # Kiểm tra phòng thủ: Nếu các file log đều lỗi hoặc rỗng
    if not all_data:
        print("Lỗi: Không có dữ liệu hợp lệ nào được đọc từ các file log.")
        return

    # --- 3.2. Trích xuất và Chuẩn hóa Dữ liệu ---
    
    # List mới này chỉ chứa dữ liệu đã được *làm sạch* và *chuẩn hóa*
    # để sẵn sàng đưa vào Pandas
    records = [] 
    
    # Dùng enumerate() để lấy cả (i = số thứ tự) và (entry = nội dung)
    for i, entry in enumerate(all_data):
        # Dùng .get() để lấy giá trị an toàn (nếu key không tồn tại, trả về None)
        # Chỉ xử lý những entry chạy 'success'
        if entry.get("status") == "success":
            
            # Cắt ngắn 'input_text' (lấy 40 ký tự đầu) để hiển thị
            # trên trục Y của biểu đồ cho đẹp, không bị quá dài.
            # Thêm (i+1) ở đầu để phân biệt các dòng test (ví dụ: '(1) Em buồn...')
            input_text_short = f"({i+1}) " + entry['input_text'][:40] + "..."
            
            # Tạo một dict mới với cấu trúc "phẳng" (flat) 
            # mà Pandas/Seaborn rất thích
            records.append({
                "text_display": input_text_short, # Tên sẽ hiển thị trên biểu đồ
                "label": entry['sentiment']['label'], # (POS, NEG, NEU)
                "score": entry['sentiment']['score']  # (0.0 -> 1.0)
            })

    # Kiểm tra phòng thủ: Nếu không có record 'success' nào
    if not records:
        print("Lỗi: Không tìm thấy entry nào có status 'success' trong các file log.")
        return

    # --- 3.3. Chuyển đổi sang Pandas DataFrame ---
    
    # pd.DataFrame(records) nhận vào 1 list các dict
    # và tự động biến nó thành 1 bảng (DataFrame)
    # Các keys (text_display, label, score) sẽ là tên cột
    df = pd.DataFrame(records)
    print(f"Đã xử lý {len(df)} kết quả 'success'. Bắt đầu vẽ biểu đồ...")

    # --- 3.4. Vẽ Biểu đồ (Dùng Seaborn và Matplotlib) ---
    
    # 3.4.1. Cấu hình Font (BẮT BUỘC để hiển thị Tiếng Việt)
    # Chỉ định cho Matplotlib thử tìm font 'Arial' hoặc 'DejaVu Sans'
    # (Đây là các font "sans-serif" phổ biến có hỗ trợ Unicode/Tiếng Việt)
    plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans']
    plt.rcParams['font.family'] = 'sans-serif'
    # Sửa lỗi hiển thị dấu '-' (nếu dữ liệu có số âm)
    plt.rcParams['axes.unicode_minus'] = False 

    # 3.4.2. Khởi tạo khung biểu đồ (Figure)
    # figsize=(width, height) tính bằng inch
    # Chiều cao (height) được tính động (dynamic) dựa trên số record
    # (0.8 inch cho mỗi record) để đảm bảo các thanh không bị dính vào nhau.
    # 'max(6, ...)' để đảm bảo chiều cao tối thiểu là 6 inch (nếu có ít record)
    plt.figure(figsize=(12, max(6, len(records) * 0.8))) 
    
    # 3.4.3. Dùng Seaborn để vẽ (barh = biểu đồ cột ngang)
    barplot = sns.barplot(
        data=df,         # Nguồn dữ liệu
        x='score',         # Cột 'score' sẽ nằm trên trục X (ngang)
        y='text_display',  # Cột 'text_display' sẽ nằm trên trục Y (dọc)
        hue='label',       # Dùng cột 'label' (POS/NEG/NEU) để *TÔ MÀU*
        
        # 'palette' (bảng màu) định nghĩa màu cụ thể cho từng nhãn 'hue'
        # Đảm bảo 'NEG' luôn là Đỏ, 'POS' luôn là Xanh
        palette={'POS': '#2ecc71', 'NEG': '#e74c3c', 'NEU': '#3498db'}, 
        
        # 'dodge=False' = Không tách các cột ra (vì ta chỉ có 1 giá trị/hàng)
        dodge=False        
    )
    
    # 3.4.4. Tinh chỉnh (Tiêu đề, Nhãn trục)
    plt.title(f'Tổng hợp Kết quả Sentiment (Từ {len(all_data)} lượt test)', fontsize=16)
    plt.xlabel('Độ tin cậy (Score)', fontsize=12)
    plt.ylabel('Nội dung Input (Rút gọn)', fontsize=12)
    
    # Set giới hạn trục X từ 0 đến 1.1 (thay vì 1.0)
    # để nhãn số "1.000" không bị 'chạm' vào rìa phải của biểu đồ
    plt.xlim(0, 1.1) 
    
    # 3.4.5. Thêm nhãn giá trị (Annotation) vào từng cột
    # 'barplot.patches' là một list chứa tất cả các đối tượng "cột"
    for p in barplot.patches:
        # Với biểu đồ ngang, 'p.get_width()' chính là giá trị 'score' (độ dài cột)
        width = p.get_width() 
        
        # plt.text() dùng để viết chữ lên biểu đồ
        plt.text(
            # Vị trí X: ở cuối cột (width) + một khoảng đệm nhỏ (0.01)
            x=width + 0.01, 
            # Vị trí Y: ở tọa độ Y (get_y) + một nửa chiều cao (get_height / 2)
            # => Tức là *chính giữa* cột theo chiều dọc
            y=p.get_y() + p.get_height() / 2, 
            # Nội dung text: format số 'score', lấy 3 chữ số thập phân (vd: 0.775)
            s=f'{width:.3f}', 
            # Căn lề dọc (Vertical Alignment) = 'center'
            va='center'
        )

    # 3.4.6. Hoàn thiện
    plt.legend(title='Cảm xúc', loc='lower right') # Hiển thị bảng chú giải màu
    plt.tight_layout() # Tự động "co giãn" các thành phần để không bị đè lên nhau

    # --- 3.5. Lưu và Hiển thị ---
    try:
        # Lưu "khung tranh" (figure) hiện tại thành file ảnh
        plt.savefig(OUTPUT_IMAGE_FILE)
        print(f"\n===> THÀNH CÔNG! Đã lưu biểu đồ vào file: {OUTPUT_IMAGE_FILE}")
    except Exception as e:
        print(f"Lỗi khi lưu file ảnh: {e}")
    
    # Mở một cửa sổ pop-up để *hiển thị* biểu đồ cho bạn xem
    plt.show() 

# === KHỐI 4: ĐIỂM KHỞI CHẠY SCRIPT ===
# Đây là "entry-point" (điểm vào) chuẩn của 1 script Python.
# Code bên trong khối 'if' này SẼ CHẠY khi bạn gõ:
#   python visualize_all_logs.py
# và SẼ KHÔNG CHẠY nếu file này được 'import' bởi một file khác.
if __name__ == "__main__":
    
    # Bước kiểm tra cuối: Thư mục 'logs' có tồn tại không?
    if not os.path.exists(LOG_DIRECTORY):
        # Nếu không, tạo ra nó
        os.makedirs(LOG_DIRECTORY) 
        print(f"Đã tạo thư mục '{LOG_DIRECTORY}'.")
        print(f"Vui lòng di chuyển các file .json log của bạn vào đó và chạy lại script.")
    else:
        # Nếu thư mục tồn tại, gọi hàm chính để bắt đầu
        visualize_all_logs_in_directory(LOG_DIRECTORY)