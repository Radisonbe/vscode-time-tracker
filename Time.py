import json
import win32gui
import time
import threading
import pystray
import queue
import customtkinter as ctk
from PIL import Image
data_lock = threading.Lock()
command_queue = queue.Queue()
def save_time(seconds): # Сохраняет общее время работы в файл
    with data_lock:
        try:
            with open ('tracker_data.json', 'r') as file:
                data = json.load(file)
        except FileNotFoundError:
            data = {}
        except json.JSONDecodeError:
            data = {}
        data["total_time"] = int(seconds)
        with open ('tracker_data.json', 'w') as file:
            json.dump(data, file)
def load_time(): # Загружает сохраненное время из файла # Если файла нет или в нем неправильные данные - возвращает 0
    with data_lock:
        try:
            with open ('tracker_data.json', 'r') as file:
                data = json.load(file)
            return data["total_time"]
        except FileNotFoundError:
            return 0
        except json.JSONDecodeError:
            return 0
        except KeyError:
            return 0
total_time = load_time()
def save_window_position(x, y): #Сохраняет позицию окна при закрытии кнопкой
    with data_lock:
        try:
            with open('tracker_data.json', 'r') as file:
                data = json.load(file)
        except FileNotFoundError:
            data = {}
        except json.JSONDecodeError:
            data = {}
        data["window_x"] = int(x)
        data["window_y"] = int(y)
        with open ('tracker_data.json', 'w') as file:
            json.dump(data, file)
def load_window_position(): #При следующем окрытии окна берет его позицию из Json файла
    with data_lock:
        try:
            with open('tracker_data.json', 'r') as file:
                data = json.load(file)
            return data['window_x'], data['window_y']
        except FileNotFoundError:
            return None
        except json.JSONDecodeError:
            return None
        except KeyError:
            return None
def format_time(total_seconds): # Переводит количество секунд в строку формата ЧЧ:ММ:СС
    total_seconds = int(total_seconds)
    hours = total_seconds // 3600
    second_remaining = total_seconds % 3600
    minutes = second_remaining // 60
    seconds = second_remaining % 60
    result = str(hours).zfill(2) + ':' + str(minutes).zfill(2) + ':' + str(seconds).zfill(2)
    return result
def check_vscode(): # Проверяет, является ли VS Code активным окном в данный момент
    active_window = win32gui.GetForegroundWindow()
    window_name = win32gui.GetWindowText(active_window)
    is_vscode = 'Visual Studio Code' in window_name
    return is_vscode
def finish_session(start, total_time): # Завершает текущую сессию работы в VS Code: # Считает её длительность, добавляя к общему времени и сохраняет результат
    end = time.time()
    time_now = end - start
    total_time = total_time + time_now
    save_time(total_time)
    return total_time
def checkpoint(last_save, total_time, current): # Промежуточно сохраняет время текущей сессиии, чтобы при аварийном закрытии программы потерялось как можно меньше времени
    session_part = current - last_save
    total_time += session_part
    save_time(total_time)
    start = current
    last_save = current
    return start, last_save, total_time  
root = ctk.CTk()
root.withdraw()
statistics_window = None
stop_event = threading.Event()
def exit_program(icon, item): # Полностью завершает программу из меню значка в трее
    command_queue.put("exit")
def show_time(icon, item): # Просит главный поток Tkinter открыть окно статистики
    command_queue.put("show")
def process_commands():
    try:
        command = command_queue.get_nowait()
        if command == "show":
            show_statistics()
        elif command == "exit":
            stop_event.set()
            icon.stop()
            root.quit()
            return
    except queue.Empty:
        pass
    root.after(100, process_commands)
image = Image.open('icon.png')
menu = pystray.Menu(pystray.MenuItem('Выход', exit_program), pystray.MenuItem('Показать статистику', show_time))
icon = pystray.Icon('test', image, menu=menu)
display_time = total_time
def tracker_loop(): # Основной цикл трекера. # Постоянно проверяет актвное окно и считает время, пока пользователь работает в VS Code.
    was_vscode = False
    is_vscode = False
    global total_time
    global display_time
    try:
        while not stop_event.is_set():
            is_vscode = check_vscode()
            if is_vscode and not was_vscode:  # Пользователь только что переключился на VS Code - начинаем новую сессию
                start = time.time()
                last_save = start
            if is_vscode: # Пока VS Code активен - обновляем текущее отображаемое время
                current = time.time()
                if current - last_save >= 10:
                    start, last_save, total_time = checkpoint(last_save, total_time, current)
                current_time = current - start
                display_time = total_time + current_time
            if was_vscode and not is_vscode: # Пользователь ушел из VS Code - завершаем и сохраняем сессию
                total_time = finish_session(start, total_time)
                display_time = total_time
                print('Общее время ' + format_time(total_time))
            time.sleep(0.1)
            was_vscode = is_vscode
    finally: # Даже при завершении программы сохраняем уже накопленное время
        if is_vscode:
            current_time = time.time() - start
            total_time = total_time + current_time
        save_time(total_time)
def show_statistics(): # Создает и показывает окно со статистикой, если оно еще не открыто
    global statistics_window
    if statistics_window is None:
        window = ctk.CTkToplevel(root)
        window.title('Code Tracker')
        window_width = 300
        window_height = 200
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        right_margin = 50
        bottom_margin = 200
        position = load_window_position()
        if position is None:
            x = screen_width - window_width - right_margin
            y = screen_height - window_height - bottom_margin
        else:
            x, y = position
        window.geometry(f'{window_width}x{window_height}+{x}+{y}')
        window.configure(fg_color='#15171c')
        window.overrideredirect(True)
        drag_x = 0
        drag_y = 0
        after_id = None
        stats_frame = ctk.CTkFrame(window, width=260, height=110, corner_radius=14, fg_color="#191C22", border_width=1, border_color='#2d3440')
        stats_frame.pack_propagate(False)
        stats_frame.place(relx=0.5, rely=0.5, anchor='center')
        def click(event): # Запоминает информацию о месте нажатия мыши
            nonlocal drag_x, drag_y
            drag_x = event.x_root - window.winfo_x()
            drag_y = event.y_root - window.winfo_y()
        def move(event): # Обрабатывает движение мыши с зажатой левой кнопкой
            new_x = event.x_root - drag_x
            new_y = event.y_root - drag_y
            window.geometry(f'+{new_x}+{new_y}')
        window.bind('<Button-1>', click)
        window.bind('<B1-Motion>', move)
        title_label = ctk.CTkLabel(stats_frame, text='ОБЩЕЕ ВРЕМЯ', font=('Segoe UI', 12), text_color="#bbc6e0", fg_color='transparent')
        time_label = ctk.CTkLabel(stats_frame, text=format_time(display_time), font=('Segoe UI', 34, 'bold'), text_color='#f2f2f2', fg_color='transparent')
        title_label.place(relx=0.5, rely=0.2, anchor='center')
        time_label.place(relx=0.5, rely=0.5, anchor='center')
        def update_time(): # Периодически обновляет текст таймера в окне
            nonlocal after_id
            time_label.configure(text=format_time(display_time))
            after_id = window.after(100, update_time)
        def close_window(): # Закрывает только окно статистики, но не всю программу
            nonlocal after_id
            global statistics_window
            statistics_window = None
            window_x = window.winfo_x()
            window_y = window.winfo_y()
            save_window_position(window_x, window_y)
            if after_id is not None:
                window.after_cancel(after_id)
            window.destroy()
        close_button = ctk.CTkButton(window, text='×', width=28, height=28, corner_radius=6, fg_color='transparent', hover_color='#3a2024', text_color="#99a0b1", font=('Segoe UI', 16), command=close_window)
        close_button.place(relx=1.0, x=-10, y=10, anchor='ne')
        hwnd = window.winfo_id()
        #print(window.winfo_id())
        region = win32gui.CreateRoundRectRgn(0, 0, window_width, window_height, 20, 20)
        win32gui.SetWindowRgn(hwnd, region, True)
        window.protocol('WM_DELETE_WINDOW', close_window)
        statistics_window = window
        update_time()
thread1 = threading.Thread(target=tracker_loop)
thread1.start()
thread2 = threading.Thread(target=icon.run)
thread2.start()
process_commands()
root.mainloop()