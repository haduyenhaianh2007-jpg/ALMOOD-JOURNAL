# tests/dev_run_history_engine.py

from core.history_engine import build_past_context

def main():
    # giả sử hiện tại model đang detect: negative + case_type nào đó
    current_label = "negative"
    case_type = "consistent_negative"  # hoặc "mild_shift", "mixed", ...

    context = build_past_context(
        current_label=current_label,
        case_type=case_type,
        user_id=None,        # hiện tại 1 user, để None
        max_examples=3
    )

    print("===== BỐI CẢNH QUÁ KHỨ =====")
    print(context)
    print("============================")

if __name__ == "__main__":
    main()
