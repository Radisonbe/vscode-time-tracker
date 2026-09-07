import win32gui
import time
import threading
import pystray
import tkinter
from PIL import Image
def save_time(seconds):
    with open ('time_VSCODE.txt', 'w') as file:
        file.write(str(int(seconds)))
def load_time():
    try:
        with open ('time_VSCODE.txt', 'r') as file:
            clock = file.read()
            clock = int(clock)
        return clock
    except FileNotFoundError:
        return 0
    except ValueError:
        return 0
total_time = load_time()
def format_time(total_seconds):
    total_seconds = int(total_seconds)
    hours = total_seconds // 3600
    second_remaining = total_seconds % 3600
    minutes = second_remaining // 60
    seconds = second_remaining % 60
    result = str(hours).zfill(2) + ':' + str(minutes).zfill(2) + ':' + str(seconds).zfill(2)
    return result
def check_vscode():
    active_window = win32gui.GetForegroundWindow()
    window_name = win32gui.GetWindowText(active_window)
    is_vscode = 'Visual Studio Code' in window_name
    return is_vscode
def finish_session(start, total_time):
    end = time.time()
    time_now = end - start
    total_time = total_time + time_now
    save_time(total_time)
    return total_time, time_now
def checkpoint(last_save, total_time, current):
    session_part = current - last_save
    total_time += session_part
    save_time(total_time)
    start = current
    last_save = current
    return start, last_save, total_time
is_vscode = False  
root = tkinter.Tk()
root.withdraw()
statistics_window = None
stop_ivent = threading.Event()
def exit_program(icon, item):
    stop_ivent.set()
    icon.stop()
    root.after(0, root.quit)
def show_time(icon, item):
    root.after(0, show_statistick)
image = Image.open('icon.png')
menu = pystray.Menu(pystray.MenuItem('Выход', exit_program), pystray.MenuItem('Показать статистику', show_time))
icon = pystray.Icon('test', image, menu=menu)
display_time = total_time
def tracker_loop():
    was_vscode = False
    global total_time
    global display_time
    try:
        while not stop_ivent.is_set():
            is_vscode = check_vscode()
            if is_vscode and not was_vscode:
                start = time.time()
                last_save = start
            if is_vscode:
                current = time.time()
                if current - last_save >= 10:
                    start, last_save, total_time = checkpoint(last_save, total_time, current)
                current_time = current - start
                display_time = total_time + current_time
            if was_vscode and not is_vscode:
                total_time, time_now = finish_session(start, total_time)
                print('Общее время ' + format_time(total_time))
            time.sleep(0.1)
            was_vscode = is_vscode
    finally:
        if is_vscode:
            current_time = time.time() - start
            total_time = total_time + current_time
        save_time(total_time)
def show_statistick():
    global statistics_window
    if statistics_window is None:
        window = tkinter.Toplevel(root)
        window.title('Code Tracker')
        window_width = 300
        window_height = 200
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        margin = 50
        height = 200
        x = screen_width - window_width - margin
        y = screen_height - window_height - height
        window.geometry(f'{window_width}x{window_height}+{x}+{y}')
        window.configure(bg='#1e1e1e')
        window.overrideredirect(True)
        def click(event):
            x = event.x
            y = event.y
            a = event.x_root
            b = event.y_root
            w_x = window.winfo_x()
            w_y = window.winfo_y()
            print('координаты мыши внутри окна: ' + 'X = ' + str(x) + ' Y = ' + str(y))
            print('коордитаны мыши на экране: ' + 'X = ' + str(a) + ' Y ' + str(b))
            print('Окно: ' + 'X = ' + str(w_x) + ' Y = ' + str(w_y))
        def move(event):
            new_x = event.x_root - x
            new_y = event.y_root - y
            print('Координаты при перетаскивании: ' + 'X = ' + str(new_x) + ' Y = ' + str(new_y))
        window.bind('<Button-1>', click)
        window.bind('<B1-Motion>', move)
        title_label = tkinter.Label(window, text='Общее время: ', font=('Arial', 12), bg='#1e1e1e', fg='#aaaaaa')
        time_label = tkinter.Label(window, text=format_time(display_time), font=('Arial', 32), bg='#1e1e1e', fg='white')
        title_label.pack(pady=(25, 5))
        time_label.pack(pady=(5, 15))
        def update_time():
            time_label.config(text=format_time(display_time))
            window.after(100, update_time)
        def close_window():
            global statistics_window
            statistics_window = None
            window.destroy()
        window.protocol('WM_DELETE_WINDOW', close_window)
        statistics_window = window
        update_time()
thread1 = threading.Thread(target=tracker_loop)
thread1.start()
thread2 = threading.Thread(target=icon.run)
thread2.start()
root.mainloop()