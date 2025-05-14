import tkinter as tk
from tkinter import messagebox
import subprocess
from datetime import datetime, timedelta
import re

TASK_NAME = "ShutdownTimerByTime"

def schedule_shutdown_at_time():
    hour = hour_entry.get()
    minute = minute_entry.get()
    try:
        hour = int(hour)
        minute = int(minute)
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError

        time_str = f"{hour:02d}:{minute:02d}"
        now = datetime.now()
        target_time = datetime.strptime(time_str, "%H:%M").replace(year=now.year, month=now.month, day=now.day)
        if target_time <= now:
            target_time += timedelta(days=1)

        # 예약 등록
        cmd = f'schtasks /create /tn "{TASK_NAME}" /tr "shutdown -s -t 0" /sc once /st {time_str} /f'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

        if "SUCCESS" in result.stdout.upper():
            messagebox.showinfo("예약 완료", f"{time_str}에 종료 예약이 설정되었습니다.")
        else:
            messagebox.showerror("예약 실패", f"명령 실패:\n{result.stdout}\n{result.stderr}")

    except ValueError:
        messagebox.showerror("입력 오류", "올바른 24시간제 시:분을 입력하세요.")

def cancel_shutdown_task():
    cmd = f'schtasks /delete /tn "{TASK_NAME}" /f'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if "SUCCESS" in result.stdout.upper():
        messagebox.showinfo("예약 취소", "✅ 종료 예약이 취소되었습니다.")
    else:
        messagebox.showinfo("예약 취소", f"⚠️ 예약된 작업이 없거나 이미 삭제됨:\n{result.stdout.strip()}")

def check_shutdown_status():
    cmd = f'schtasks /query /tn "{TASK_NAME}" /fo LIST /v'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    output = result.stdout

    if TASK_NAME.lower() not in output.lower():
        messagebox.showinfo("예약 상태", "❌ 예약된 종료 작업이 없습니다.")
        return

    # Start Time 추출 (다국어 대응)
    match = re.search(r"Start Time:\s*(.*)", output)
    if not match:
        match = re.search(r"시작 시간\s*:\s*(.*)", output)
    if not match:
        messagebox.showinfo("예약 상태", f"✅ 예약된 작업이 존재하지만 시작 시각 추출에 실패했습니다.\n\n{output}")
        return

    time_str = match.group(1).strip()
    try:
        # 12시간제 "오후 11:00:00" 형식 대응
        scheduled = datetime.strptime(time_str, "%p %I:%M:%S") if "오전" in time_str or "오후" in time_str else datetime.strptime(time_str, "%I:%M:%S %p")
        now = datetime.now()
        scheduled = scheduled.replace(year=now.year, month=now.month, day=now.day)
        if scheduled < now:
            scheduled += timedelta(days=1)
        diff = scheduled - now
        minutes_left = int(diff.total_seconds() // 60)
        messagebox.showinfo("예약 상태", f"✅ 종료 예약 시각: {scheduled.strftime('%H:%M')}\n남은 시간: 약 {minutes_left}분")
    except:
        messagebox.showinfo("예약 상태", f"✅ 예약된 종료 시각: {time_str}\n(시간 해석 실패)")

# GUI 구성
root = tk.Tk()
root.title("시간 지정 종료 예약기 (schtasks)")
root.geometry("350x240")

label = tk.Label(root, text="종료 시간 입력 (24시간제):")
label.pack(pady=10)

time_frame = tk.Frame(root)
time_frame.pack()

hour_entry = tk.Entry(time_frame, width=5)
hour_entry.insert(0, "23")
hour_entry.pack(side="left")
tk.Label(time_frame, text=" : ").pack(side="left")

minute_entry = tk.Entry(time_frame, width=5)
minute_entry.insert(0, "30")
minute_entry.pack(side="left")

btn_frame = tk.Frame(root)
btn_frame.pack(pady=15)

schedule_btn = tk.Button(btn_frame, text="종료 예약", command=schedule_shutdown_at_time, width=10)
schedule_btn.pack(side="left", padx=5)

cancel_btn = tk.Button(btn_frame, text="예약 취소", command=cancel_shutdown_task, width=10)
cancel_btn.pack(side="left", padx=5)

check_btn = tk.Button(root, text="예약 상태 확인", command=check_shutdown_status, width=30)
check_btn.pack(pady=10)

root.mainloop()