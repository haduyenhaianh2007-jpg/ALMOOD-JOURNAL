import json
from datetime import datetime, timedelta

HISTORY_PATH = "pipeline_history.json"

def generate_mock():
    now = datetime.now()
    
    history = [
        # A – 3 lần negative gần nhau
        {
            "text": "Hôm nay hơi buồn và chán nản.",
            "label": "negative",
            "timestamp": (now - timedelta(days=1)).isoformat()
        },
        {
            "text": "Vẫn cảm thấy mệt mỏi.",
            "label": "negative",
            "timestamp": (now - timedelta(days=2)).isoformat()
        },
        {
            "text": "Hôm qua stress thật sự.",
            "label": "negative",
            "timestamp": (now - timedelta(days=3)).isoformat()
        },

        # B – Detect deadline
        {
            "text": "Mai thi Toán khó quá.",
            "label": "neutral",
            "timestamp": (now - timedelta(days=2)).isoformat()
        },

        # C – success pattern
        {
            "text": "Nghe nhạc xong cảm thấy tốt hơn.",
            "label": "positive",
            "timestamp": (now - timedelta(days=4)).isoformat()
        }
    ]

    with open(HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)

    print("✔ Đã tạo pipeline_history.json với mock data hợp lệ")


if __name__ == "__main__":
    generate_mock()
