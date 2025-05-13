import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pyautogui
import pygetwindow as gw
import threading
import time
import json
import ctypes

ctypes.windll.user32.SetProcessDPIAware()  # DPI 스케일 문제 방지

class MacroApp:
    def __init__(self, root):
        self.root = root
        self.root.title("고급 매크로 실행기")
        self.actions = []  # [(type, data_dict)]

        # 좌표 실시간 확인창
        coord_frame = tk.Frame(root)
        coord_frame.pack(pady=3)
        tk.Label(coord_frame, text="현재 마우스 좌표:").pack(side="left")
        self.coord_label = tk.Label(coord_frame, text="(0, 0)", font=("Consolas", 10))
        self.coord_label.pack(side="left")

        tk.Button(coord_frame, text="좌표 고정 (F8)", command=self.capture_position).pack(side="left", padx=10)
        self.fixed_label = tk.Label(coord_frame, text="고정 좌표: 없음", font=("Consolas", 10))
        self.fixed_label.pack(side="left")

        self.update_mouse_position()
        self.root.bind('<F8>', lambda e: self.capture_position())

        # 윈도우 선택
        self.window_label = tk.Label(root, text="실행 대상 창:")
        self.window_label.pack()

        self.window_combo = ttk.Combobox(root, state="readonly")
        self.window_combo.pack(fill='x', padx=5, pady=5)

        tk.Button(root, text="창 목록 새로고침", command=self.refresh_window_list).pack(pady=2)
        self.refresh_window_list()

        # 입력행 조작 버튼들
        button_frame = tk.Frame(root)
        button_frame.pack(pady=5)

        tk.Button(button_frame, text="마우스 입력행 추가", command=self.add_mouse_row).pack(side='left', padx=5)
        tk.Button(button_frame, text="키보드 입력행 추가", command=self.add_keyboard_row).pack(side='left', padx=5)
        tk.Button(button_frame, text="선택한 행 수정", command=self.edit_selected_row).pack(side='left', padx=5)
        tk.Button(button_frame, text="선택한 행 삭제", command=self.delete_selected_row).pack(side='left', padx=5)
        tk.Button(button_frame, text="▲ 위로 이동", command=self.move_row_up).pack(side='left', padx=5)
        tk.Button(button_frame, text="▼ 아래로 이동", command=self.move_row_down).pack(side='left', padx=5)

        # 저장/불러오기 버튼
        file_frame = tk.Frame(root)
        file_frame.pack(pady=5)
        tk.Button(file_frame, text="저장", command=self.save_actions).pack(side='left', padx=5)
        tk.Button(file_frame, text="불러오기", command=self.load_actions).pack(side='left', padx=5)

        # 입력 테이블
        self.tree = ttk.Treeview(root, columns=("type", "detail", "repeat"), show="headings")
        self.tree.heading("type", text="동작종류")
        self.tree.heading("detail", text="세부내용")
        self.tree.heading("repeat", text="반복횟수")
        self.tree.pack(fill='both', expand=True, padx=5, pady=5)

        # 실행 버튼
        tk.Button(root, text="실행하기", command=self.start_macro).pack(pady=10)

    def update_mouse_position(self):
        x, y = pyautogui.position()
        self.coord_label.config(text=f"({x}, {y})")
        self.root.after(100, self.update_mouse_position)

    def capture_position(self):
        x, y = pyautogui.position()
        self.fixed_label.config(text=f"고정 좌표: ({x}, {y})")

    def refresh_window_list(self):
        self.window_combo['values'] = [w.title for w in gw.getWindowsWithTitle("") if w.title.strip() != ""]
        if self.window_combo['values']:
            self.window_combo.current(0)

    def add_mouse_row(self):
        self.edit_row_dialog("마우스")

    def add_keyboard_row(self):
        self.edit_row_dialog("키보드")

    def delete_selected_row(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("선택 필요", "삭제할 행을 선택해주세요.")
            return
        index = self.tree.index(selected[0])
        del self.actions[index]
        self.tree.delete(selected[0])

    def move_row_up(self):
        selected = self.tree.selection()
        if not selected:
            return
        index = self.tree.index(selected[0])
        if index == 0:
            return
        self.actions[index - 1], self.actions[index] = self.actions[index], self.actions[index - 1]
        values = self.tree.item(selected[0])['values']
        self.tree.delete(selected[0])
        self.tree.insert('', index - 1, values=values)
        self.tree.selection_set(self.tree.get_children()[index - 1])

    def move_row_down(self):
        selected = self.tree.selection()
        if not selected:
            return
        index = self.tree.index(selected[0])
        if index >= len(self.actions) - 1:
            return
        self.actions[index + 1], self.actions[index] = self.actions[index], self.actions[index + 1]
        values = self.tree.item(selected[0])['values']
        self.tree.delete(selected[0])
        self.tree.insert('', index + 1, values=values)
        self.tree.selection_set(self.tree.get_children()[index + 1])

    def edit_selected_row(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("선택 필요", "수정할 행을 선택해주세요.")
            return
        index = self.tree.index(selected[0])
        action_type, data = self.actions[index]
        self.edit_row_dialog(action_type, data, index)

    def edit_row_dialog(self, action_type, data=None, index=None):
        row_frame = tk.Toplevel(self.root)
        row_frame.title("입력행 수정" if index is not None else f"{action_type} 입력행 추가")

        if action_type == "마우스":
            tk.Label(row_frame, text="X 좌표:").grid(row=0, column=0)
            x_entry = tk.Entry(row_frame)
            x_entry.grid(row=0, column=1)

            tk.Label(row_frame, text="Y 좌표:").grid(row=1, column=0)
            y_entry = tk.Entry(row_frame)
            y_entry.grid(row=1, column=1)

            tk.Label(row_frame, text="반복 횟수:").grid(row=2, column=0)
            repeat_entry = tk.Entry(row_frame)
            repeat_entry.grid(row=2, column=1)

            if data:
                x_entry.insert(0, data['x'])
                y_entry.insert(0, data['y'])
                repeat_entry.insert(0, data['repeat'])
            else:
                repeat_entry.insert(0, "1")

            def submit():
                try:
                    x = int(x_entry.get())
                    y = int(y_entry.get())
                    repeat = int(repeat_entry.get())
                    detail = f"x={x}, y={y} 클릭"
                    new_data = {"x": x, "y": y, "repeat": repeat}
                    if index is not None:
                        self.actions[index] = ("마우스", new_data)
                        self.tree.item(self.tree.get_children()[index], values=("마우스", detail, repeat))
                    else:
                        self.actions.append(("마우스", new_data))
                        self.tree.insert('', 'end', values=("마우스", detail, repeat))
                    row_frame.destroy()
                except ValueError:
                    messagebox.showerror("오류", "숫자를 정확히 입력해주세요.")

            tk.Button(row_frame, text="저장", command=submit).grid(row=3, columnspan=2, pady=5)

        elif action_type == "키보드":
            tk.Label(row_frame, text="키 입력 순서 (예: ctrl+shift+tab, tab, tab, enter):").grid(row=0, column=0, columnspan=2)
            key_entry = tk.Entry(row_frame, width=50)
            key_entry.grid(row=1, column=0, columnspan=2)

            tk.Label(row_frame, text="반복 횟수:").grid(row=2, column=0)
            repeat_entry = tk.Entry(row_frame)
            repeat_entry.grid(row=2, column=1)

            if data:
                key_entry.insert(0, ', '.join(data['keys']))
                repeat_entry.insert(0, data['repeat'])
            else:
                repeat_entry.insert(0, "1")

            def submit():
                try:
                    key_sequence = [k.strip() for k in key_entry.get().split(',') if k.strip()]
                    repeat = int(repeat_entry.get())
                    detail = ' -> '.join(key_sequence)
                    new_data = {"keys": key_sequence, "repeat": repeat}
                    if index is not None:
                        self.actions[index] = ("키보드", new_data)
                        self.tree.item(self.tree.get_children()[index], values=("키보드", detail, repeat))
                    else:
                        self.actions.append(("키보드", new_data))
                        self.tree.insert('', 'end', values=("키보드", detail, repeat))
                    row_frame.destroy()
                except ValueError:
                    messagebox.showerror("오류", "숫자를 정확히 입력해주세요.")

            tk.Button(row_frame, text="저장", command=submit).grid(row=3, columnspan=2, pady=5)

    def save_actions(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json")])
        if not file_path:
            return
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.actions, f, ensure_ascii=False, indent=2)
            messagebox.showinfo("저장 완료", "입력 리스트가 저장되었습니다.")
        except Exception as e:
            messagebox.showerror("오류", f"저장 중 오류 발생: {e}")

    def load_actions(self):
        file_path = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
        if not file_path:
            return
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.actions = json.load(f)
            self.tree.delete(*self.tree.get_children())
            for action_type, data in self.actions:
                if action_type == "마우스":
                    detail = f"x={data['x']}, y={data['y']} 클릭"
                elif action_type == "키보드":
                    detail = ' -> '.join(data['keys'])
                self.tree.insert('', 'end', values=(action_type, detail, data['repeat']))
            messagebox.showinfo("불러오기 완료", "입력 리스트를 불러왔습니다.")
        except Exception as e:
            messagebox.showerror("오류", f"불러오기 중 오류 발생: {e}")

    def focus_window(self, title):
        win = next((w for w in gw.getWindowsWithTitle(title) if w.title == title), None)
        if win:
            win.activate()
            time.sleep(0.5)
            return True
        return False

    def execute_actions(self):
        target_title = self.window_combo.get()
        if not self.focus_window(target_title):
            messagebox.showerror("오류", "지정한 창을 찾을 수 없습니다.")
            return

        for action_type, data in self.actions:
            for _ in range(data["repeat"]):
                if action_type == "마우스":
                    pyautogui.click(data["x"], data["y"])
                elif action_type == "키보드":
                    for key_combo in data["keys"]:
                        keys = [k.strip() for k in key_combo.split('+')]
                        pyautogui.hotkey(*keys)
                        time.sleep(0.1)
                time.sleep(0.3)

        messagebox.showinfo("완료", "매크로 실행이 완료되었습니다.")

    def start_macro(self):
        threading.Thread(target=self.execute_actions).start()

if __name__ == '__main__':
    root = tk.Tk()
    app = MacroApp(root)
    root.mainloop()
