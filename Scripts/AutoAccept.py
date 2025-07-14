import os
import time
import threading
import win32api
import win32con
import win32gui
import win32process
import psutil
from PIL import ImageGrab
from steam_path_utils import find_csgo_log_path  # type: ignore

# === Настройки ===
LOG_PATH: str = find_csgo_log_path()  # type: ignore
if not LOG_PATH:
    print('[ОШИБКА]: Файл console.log не найден. Проверьте путь установки Steam и CS:GO.')
    exit(1)
TARGET_COLOR = (54, 183, 82)  # Цвет кнопки "Принять матч"
COLOR_TOLERANCE = 20  # Допуск по цвету
WAITING_TIME = 5  # Сколько секунд искать кнопку

# Проверка, что окно cs2.exe в фокусе

def is_cs2_in_foreground():
    try:
        hwnd = win32gui.GetForegroundWindow()
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        p = psutil.Process(pid)
        return p.name().lower() == "cs2.exe"
    except Exception:
        return False

# Координаты кнопки (примерно центр экрана, можно скорректировать)
def get_button_coords():
    screen_width = win32api.GetSystemMetrics(0)
    screen_height = win32api.GetSystemMetrics(1)
    x = int(screen_width / 2)
    y = int(screen_height / 2.2)
    return x, y

def is_color_similar(c1, c2, tolerance):
    return all(abs(a - b) <= tolerance for a, b in zip(c1, c2))

def get_pixel_color(x, y):
    img = ImageGrab.grab(bbox=(x, y, x+1, y+1))
    return img.getpixel((0, 0))

def click(x, y):
    win32api.SetCursorPos((x, y))
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, x, y, 0, 0)
    time.sleep(0.05)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, x, y, 0, 0)

def monitor_log(callback):
    """Следит за появлением строки 'Server confirmed all players' в логе."""
    with open(LOG_PATH, 'r', encoding='utf-8', errors='ignore') as f:
        # Перематываем в конец файла
        f.seek(0, os.SEEK_END)
        while True:
            line = f.readline()
            if not line:
                time.sleep(0.1)
                continue
            if 'Server confirmed all players' in line:
                callback()

def auto_accept():
    print('[*] Ожидание матча...')
    def on_match_found():
        print('[*] Найден матч! Ищу кнопку...')
        old_pos = win32api.GetCursorPos()
        start_time = time.time()
        accepted = False
        while time.time() - start_time < WAITING_TIME:
            if not is_cs2_in_foreground():
                print('CS2 не в фокусе')
                time.sleep(0.2)
                continue
            x, y = get_button_coords()
            color = get_pixel_color(x, y)
            print(f'Проверяю пиксель: {x}, {y}, цвет: {color}')
            if is_color_similar(color, TARGET_COLOR, COLOR_TOLERANCE):
                print('[*] Кнопка найдена, кликаю несколько раз!')
                # Наводим курсор в центр несколько раз для надежности
                for i in range(20):
                    win32api.SetCursorPos((x, y))
                    time.sleep(0.01)
                
                # Кликаем несколько раз для надежности
                for i in range(20):
                    click(x, y)
                    time.sleep(0.02)  # Небольшая пауза между кликами
                
                accepted = True
                break
            time.sleep(0.1)
        win32api.SetCursorPos(old_pos)
        if accepted:
            print('[+] Матч принят!')
        else:
            print('[!] Кнопка не найдена или окно CS2 не активно :(')

    threading.Thread(target=monitor_log, args=(on_match_found,), daemon=True).start()

if __name__ == '__main__':
    auto_accept()
    while True:
        time.sleep(1)
