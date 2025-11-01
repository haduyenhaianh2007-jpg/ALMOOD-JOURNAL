# Tên file: prepare_datasets_v2.py (Phiên bản v6 - Sửa lỗi WinError 1224)

import os
import pandas as pd
from datasets import load_dataset, concatenate_datasets, Dataset
from typing import Dict
from pyarrow.lib import ArrowInvalid

print("Tải thư viện... (Vui lòng chờ)")

# === KHỐI 1: CẤU HÌNH (Giữ nguyên) ===
PROCESSED_DATA_DIR = os.path.join("data", "processed")

ID_VSFC = "ura-hcmut/UIT-VSFC"
ID_VLSP = "ura-hcmut/vlsp2016"
ID_VSMEC = "ura-hcmut/UIT-VSMEC"
ID_GREENNODE = "GreenNode/emotion-vn"

SENTIMENT_NUMERIC_MAP: Dict[int, str] = {
    0: 'negative', 1: 'neutral', 2: 'positive'
}
EMOTION_TO_SENTIMENT_MAP: Dict[str, str] = {
    'Joy': 'positive', 'joy': 'positive',
    'Anger': 'negative', 'anger': 'negative',
    'Sadness': 'negative', 'sadness': 'negative', 'Sad': 'negative',
    'Fear': 'negative', 'fear': 'negative',
    'Disgust': 'negative', 'disgust': 'negative',
    'Surprise': 'neutral', 'surprise': 'neutral',
    'Neutral': 'neutral', 'neutral': 'neutral', 'Other': 'neutral'
}
EMOTION_NORMALIZE_MAP: Dict[str, str] = {
    'Joy': 'joy', 'joy': 'joy',
    'Anger': 'anger', 'anger': 'anger',
    'Sadness': 'sadness', 'sadness': 'sadness', 'Sad': 'sadness',
    'Fear': 'fear', 'fear': 'fear',
    'Disgust': 'disgust', 'disgust': 'disgust',
    'Surprise': 'surprise', 'surprise': 'surprise',
    'Neutral': 'neutral', 'neutral': 'neutral', 'Other': 'neutral'
}

# === KHỐI 2: HÀM HỖ TRỢ (Sửa lỗi kép) ===

def load_and_normalize(dataset_id: str, text_col: str, label_col: str, label_map: Dict = None) -> Dataset:
    print(f"  Đang tải {dataset_id}...")
    try:
        # === SỬA LỖI 1: Thêm trust_remote_code=True ===
        dataset_dict = load_dataset(dataset_id, trust_remote_code=True)
    
    except ArrowInvalid:
        print(f"    Cảnh báo: Gặp lỗi ArrowInvalid với {dataset_id}.")
        print("    Đang thử tải lại (force_redownload)...")
        try:
            dataset_dict = load_dataset(
                dataset_id, 
                download_mode="force_redownload",
                ignore_verifications=True,
                trust_remote_code=True # Thêm cả ở đây
            )
        except Exception as e:
            print(f"    LỖI KHI TẢI LẠI: {e}. Bỏ qua dataset này.")
            return None
            
    except Exception as e:
        # Bắt các lỗi khác (ví dụ: `trust_remote_code` bị yêu cầu)
        print(f"    LỖI KHI TẢI: {e}.")
        if "trust_remote_code" in str(e):
             print("    Lỗi này yêu cầu 'trust_remote_code=True'. Script v6 đã thêm, vui lòng kiểm tra lại.")
        return None
        
    dataset = concatenate_datasets([dataset_dict[split] for split in dataset_dict.keys()])
    
    if text_col not in dataset.column_names or label_col not in dataset.column_names:
        print(f"    LỖI: Dataset {dataset_id} thiếu cột '{text_col}' hoặc '{label_col}'.")
        print(f"    (Các cột tìm thấy là: {dataset.column_names})")
        return None

    # (Phần rename thông minh từ v4/v5)
    if text_col != "text":
        dataset = dataset.rename_column(text_col, "text")
    if label_col != "label_raw":
        dataset = dataset.rename_column(label_col, "label_raw")
    else:
        dataset = dataset.rename_column(label_col, "label_raw_temp")
        dataset = dataset.rename_column("label_raw_temp", "label_raw")
    
    dataset = dataset.select_columns(['text', 'label_raw'])
    
    def map_labels(example):
        raw_label = example['label_raw']
        example['label'] = label_map.get(raw_label, raw_label) if label_map else raw_label
        return example
        
    # === SỬA LỖI 2 (WinError 1224): Thêm 'load_from_cache_file=False' ===
    dataset = dataset.map(map_labels, load_from_cache_file=False)
    # === KẾT THÚC SỬA LỖI ===
    
    dataset = dataset.select_columns(['text', 'label'])
    return dataset

# === KHỐI 3: HÀM MAIN (Sửa lỗi 1224) ===

def main():
    print("Bắt đầu Giai đoạn 1: Tải và Chế biến Dữ liệu...")
    os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)
    
    # --- 1. Tải 4 "Nguyên liệu" ---
    ds_vsfc = load_and_normalize(ID_VSFC, 
                                 text_col='text', 
                                 label_col='label', 
                                 label_map=SENTIMENT_NUMERIC_MAP)
                                 
    ds_vlsp = load_and_normalize(ID_VLSP, 
                                 text_col='Data',
                                 label_col='Class',
                                 label_map=SENTIMENT_NUMERIC_MAP)
                                 
    ds_vsmec = load_and_normalize(ID_VSMEC, 
                                  text_col='Sentence',
                                  label_col='Emotion',
                                  label_map=None) 
                                 
    ds_greennode = load_and_normalize(ID_GREENNODE, 
                                      text_col='text', 
                                      label_col='label_text',
                                      label_map=None)
    
    all_datasets = {
        'vsfc': ds_vsfc, 'vlsp': ds_vlsp, 
        'vsmec': ds_vsmec, 'greennode': ds_greennode
    }
    loaded_datasets = {name: ds for name, ds in all_datasets.items() if ds is not None}
    print(f"\nĐã tải thành công {len(loaded_datasets)} / 4 bộ dataset.")
    if not loaded_datasets:
        print("Không có dataset nào được tải. Dừng script.")
        return

    # --- 2. Tạo Bộ Dataset 1 (Sentiment 3 Lớp) ---
    print("\nĐang xử lý Bộ Dataset 1 (Sentiment 3 Lớp)...")
    
    list_to_merge_3_lop = []
    
    if 'vsfc' in loaded_datasets:
        list_to_merge_3_lop.append(loaded_datasets['vsfc'])
    if 'vlsp' in loaded_datasets:
        list_to_merge_3_lop.append(loaded_datasets['vlsp'])
        
    def map_emotion_to_3_labels(example):
        example['label'] = EMOTION_TO_SENTIMENT_MAP.get(example['label'], None)
        return example
        
    # === SỬA LỖI 2 (WinError 1224): Thêm 'load_from_cache_file=False' ===
    if 'vsmec' in loaded_datasets:
        ds_3_lop_vsmec = loaded_datasets['vsmec'].map(map_emotion_to_3_labels, load_from_cache_file=False)
        list_to_merge_3_lop.append(ds_3_lop_vsmec)
    if 'greennode' in loaded_datasets:
        ds_3_lop_greennode = loaded_datasets['greennode'].map(map_emotion_to_3_labels, load_from_cache_file=False)
        list_to_merge_3_lop.append(ds_3_lop_greennode)
    # === KẾT THÚC SỬA LỖI ===

    if not list_to_merge_3_lop:
        print("Không có dataset Sentiment 3 Lớp nào được tải. Bỏ qua Bộ Dataset 1.")
    else:
        ds_sentiment_3_lop = concatenate_datasets(list_to_merge_3_lop)
        ds_sentiment_3_lop = ds_sentiment_3_lop.filter(lambda e: e['label'] is not None and e['text'] is not None)
        df_sentiment_3_lop = ds_sentiment_3_lop.to_pandas()
        df_sentiment_3_lop = df_sentiment_3_lop.drop_duplicates(subset=['text'])
        
        output_path_1 = os.path.join(PROCESSED_DATA_DIR, "sentiment_3_lop.csv")
        df_sentiment_3_lop.to_csv(output_path_1, index=False, encoding='utf-8')
        
        print(f"✅ Đã lưu Bộ Dataset 1 (3 Lớp) tại: {output_path_1}")
        print(f"   (Tổng cộng: {len(df_sentiment_3_lop)} mẫu)")
        print(f"   Phân bổ nhãn:\n{df_sentiment_3_lop['label'].value_counts()}\n")

    # --- 3. Tạo Bộ Dataset 2 (Emotion 7 Lớp) ---
    print("Đang xử lý Bộ Dataset 2 (Emotion 7 Lớp)...")
    
    list_to_merge_7_lop = []

    def normalize_emotion_labels(example):
        example['label'] = EMOTION_NORMALIZE_MAP.get(example['label'], None)
        return example
        
    # === SỬA LỖI 2 (WinError 1224): Thêm 'load_from_cache_file=False' ===
    if 'vsmec' in loaded_datasets:
        ds_7_lop_vsmec = loaded_datasets['vsmec'].map(normalize_emotion_labels, load_from_cache_file=False)
        list_to_merge_7_lop.append(ds_7_lop_vsmec)
    if 'greennode' in loaded_datasets:
        ds_7_lop_greennode = loaded_datasets['greennode'].map(normalize_emotion_labels, load_from_cache_file=False)
        list_to_merge_7_lop.append(ds_7_lop_greennode)
    # === KẾT THÚC SỬA LỖI ===

    if not list_to_merge_7_lop:
        print("Không có dataset Emotion 7 Lớp nào được tải. Bỏ qua Bộ Dataset 2.")
    else:
        ds_emotion_7_lop = concatenate_datasets(list_to_merge_7_lop)
        ds_emotion_7_lop = ds_emotion_7_lop.filter(lambda e: e['label'] is not None and e['text'] is not None)
        df_emotion_7_lop = ds_emotion_7_lop.to_pandas()
        df_emotion_7_lop = df_emotion_7_lop.drop_duplicates(subset=['text'])

        output_path_2 = os.path.join(PROCESSED_DATA_DIR, "emotion_7_lop.csv")
        df_emotion_7_lop.to_csv(output_path_2, index=False, encoding='utf-8')
        
        print(f"✅ Đã lưu Bộ Dataset 2 (7 Lớp) tại: {output_path_2}")
        print(f"   (Tổng cộng: {len(df_emotion_7_lop)} mẫu)")
        print(f"   Phân bổ nhãn:\n{df_emotion_7_lop['label'].value_counts()}\n")

    print("Hoàn thành Giai đoạn 1!")

# === KHỐI 4: ĐIỂM KHỞI CHẠY SCRIPT ===
if __name__ == "__main__":
    main()