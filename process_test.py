import time
import win32gui
import win32process
import psutil
import tkinter
import os
import json
from tkinter import filedialog
from tkinter import messagebox
is_file = os.path.isfile("process_settings.json")
def select_program():
    root = tkinter.Tk()
    root.withdraw()
    selected_exe = filedialog.askopenfilename(title="Выберите файл", filetypes=[("Программы", "*.exe")])
    root.destroy()
    selected_exe = os.path.normcase(selected_exe)
    if selected_exe != "":
        settings = {
            "tracked_exe": selected_exe
            }
        with open("process_settings.json", "w", encoding="utf-8") as file:
            json.dump(settings, file, ensure_ascii=False, indent=4)
    else:
        print("Файл не выбран.")
    return selected_exe
if is_file:
    with open("process_settings.json", "r", encoding="utf-8") as file:
        selected_exe = json.load(file)["tracked_exe"]
    if not os.path.isfile(selected_exe):
        messagebox.showerror("Ошибка", "Файл не найден. Пожалуйста, выберите файл заново.")
        selected_exe = select_program()
else:
    selected_exe = select_program()
def is_target_active(selected_exe):
    hwnd = win32gui.GetForegroundWindow()
    process_info = win32process.GetWindowThreadProcessId(hwnd)
    thread_id, pid = process_info
    try:
        process = psutil.Process(pid)
        active_exe = process.exe()
        active_exe = os.path.normcase(active_exe)
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return False
    return selected_exe == active_exe
time.sleep(3)
if selected_exe != "":
    print(is_target_active(selected_exe))