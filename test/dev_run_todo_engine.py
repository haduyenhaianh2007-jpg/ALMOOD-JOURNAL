"""
dev_run_todo_engine.py
Test basic cho core/todo_engine.py

Chạy:
    python dev_run_todo_engine.py
"""

from core.todo_engine import (
    extract_tasks_from_text,
    generate_gentle_question,
    create_todo_plan,
)

# ===============================
# 1. Input nhật ký test
# ===============================
sample_texts = [
    "Mai thi Toán rồi mà chưa ôn gì cả.",
    "Deadline bài thuyết trình tối nay mà slide chưa làm.",
    "Không biết sao nữa, bài tập lớn phải nộp tuần này.",
]

print("\n===============================")
print("🔍 TEST TRÍCH TASK")
print("===============================")

for text in sample_texts:
    print(f"\n📝 Nhật ký: {text}")
    tasks = extract_tasks_from_text(text)

    if not tasks:
        print("→ Không phát hiện nhiệm vụ nào.")
        continue

    for task in tasks:
        print(f"→ Nhiệm vụ phát hiện: {task.action} (conf={task.confidence})")

        # =============================
        # 2. Test câu hỏi nhẹ nhàng
        # =============================
        question = generate_gentle_question(task)
        print("\n💬 Câu hỏi nhẹ nhàng AI hỏi user:")
        print(question)

        # =============================
        # 3. Test tạo kế hoạch To-Do
        # =============================
        plan = create_todo_plan(task, text)

        print("\n📌 Kế hoạch sinh ra:")
        print(f"Main task: {plan.main_task}")
        print(f"Subtasks: {plan.subtasks}")
        print(f"Deadline: {plan.deadline}")
        print(f"Timeline: {plan.timeline}")
        print("--------------------------------------------")
