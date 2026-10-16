import time
import win32gui
import win32process
import psutil
import tkinter
import os
from tkinter import filedialog
def is_target_active(selected_exe):
    hwnd = win32gui.GetForegroundWindow()
    process_info = win32process.GetWindowThreadProcessId(hwnd)
    thread_id, pid = process_info
    process = psutil.Process(pid)
    active_exe = process.exe()
    active_exe = os.path.normcase(active_exe)
    return selected_exe == active_exe
root = tkinter.Tk()
root.withdraw()
selected_exe = filedialog.askopenfilename(title="Выберите файл", filetypes=[("Программы", "*.exe")])
root.destroy()
selected_exe = os.path.normcase(selected_exe)
time.sleep(3)
print(is_target_active(selected_exe))