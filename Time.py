import json
import win32gui
import time
import threading
import pystray
import tkinter
import queue
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
    return total_time, time_now
def checkpoint(last_save, total_time, current): # Промежуточно сохраняет время текущей сессиии, чтобы при аварийном закрытии программы потерялось как можно меньше времени
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
def exit_program(icon, item): # Полностью завершает программу из меню значка в трее
    command_queue.put("exit")
def show_time(icon, item): # Просит главный поток Tkinter открыть окно статистики
    command_queue.put("show")
def process_commands():
    try:
        command = command_queue.get_nowait()
        if command == "show":
            show_statistick()
        elif command == "exit":
            stop_ivent.set()
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
    global total_time
    global display_time
    try:
        while not stop_ivent.is_set():
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
                total_time, time_now = finish_session(start, total_time)
                print('Общее время ' + format_time(total_time))
            time.sleep(0.1)
            was_vscode = is_vscode
    finally: # Даже при завершении программы сохраняем уже накопленное время
        if is_vscode:
            current_time = time.time() - start
            total_time = total_time + current_time
        save_time(total_time)
def show_statistick(): # Создает и показывает окно со статистикой, если оно еще не открыто
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
        position = load_window_position()
        if position is None:
            x = screen_width - window_width - margin
            y = screen_height - window_height - height
        else:
            x, y = position
        window.geometry(f'{window_width}x{window_height}+{x}+{y}')
        window.configure(bg='#1e1e1e')
        window.overrideredirect(True)
        drag_x = 0
        drag_y = 0
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
        title_label = tkinter.Label(window, text='Общее время: ', font=('Arial', 12), bg='#1e1e1e', fg='#aaaaaa')
        time_label = tkinter.Label(window, text=format_time(display_time), font=('Arial', 32), bg='#1e1e1e', fg='white')
        title_label.pack(pady=(25, 5))
        time_label.pack(pady=(5, 15))
        def update_time(): # Периодически обновляет текст таймера в окне
            time_label.config(text=format_time(display_time))
            window.after(100, update_time)
        def close_window(): # Закрывает только окно статистики, но не всю программу
            global statistics_window
            statistics_window = None
            window_x = window.winfo_x()
            window_y = window.winfo_y()
            save_window_position(window_x, window_y)
            window.destroy()
        close_button = tkinter.Button(window, text='×', font=('Arial', 15), bg='#1e1e1e', fg='#aaaaaa', relief='flat', borderwidth=0, highlightthickness=0, activebackground='#1e1e1e', activeforeground='#aaaaaa', command=close_window)
        close_button.place(x=270, y=8, width=20, height= 20)
        def close_enter(event): #Меняет цвет вокрук кнопки закрытия при наведении на неё
            close_button.config(bg="#492E2E")
        def close_leave(event): #Меняет цвет кнопки закрытия обратно
            close_button.config(bg='#1e1e1e')
        close_button.bind('<Enter>', close_enter)
        close_button.bind('<Leave>', close_leave)
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