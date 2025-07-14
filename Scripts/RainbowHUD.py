import time
import math
import win32api
import win32con
import win32gui
import threading
import os
from rgb_utils import synced_rgb
from steam_path_utils import find_csgo_cfg_path

def load_steps_from_cfg():
    try:
        with open('rgb.cfg', 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith('steps='):
                    return max(0.001, float(line.strip().split('=', 1)[1]))
    except Exception:
        pass
    return 0.01

cfg_dir = find_csgo_cfg_path()
if not cfg_dir:
    print('[ОШИБКА]: Папка cfg не найдена. Проверьте путь установки Steam и CS:GO.')
    exit(1)
cfg_path = os.path.join(cfg_dir, 'pyscripts2.cfg')

VK_F15 = 0x7D  # F14 key code
WINDOW_NAME = "Counter-Strike 2"

def closest_hud_color(r, g, b):
    hud_colors = {
        2: (255, 255, 255),
        3: (151, 201, 255),
        4: (37, 121, 255),
        5: (201, 101, 255),
        6: (255, 42, 37),
        7: (255, 114, 37),
        8: (255, 247, 37),
        9: (63, 255, 37),
        10: (114, 255, 219),
        11: (255, 158, 206),
    }
    def color_distance(c1, c2):
        return math.sqrt(sum((e1 - e2) ** 2 for e1, e2 in zip(c1, c2)))
    closest = min(hud_colors.items(), key=lambda item: color_distance((r, g, b), item[1]))
    return closest[0]

def update_rainbow_hud():
    last_hud_color = None
    while True:
        r, g, b = synced_rgb()
        hud_color = closest_hud_color(r, g, b)
        if last_hud_color == hud_color:
            time.sleep(0.01)
            continue
        last_hud_color = hud_color
        content = f"cl_hud_color {hud_color}\n"
        try:
            with open(cfg_path, "w") as f:
                f.write(content)
        except Exception as e:
            print(f"[Ошибка записи файла]: {e}")
        time.sleep(0.01)  # Увеличенный интервал

def find_cs2_window():
    return win32gui.FindWindow(None, WINDOW_NAME)

def is_window_in_focus(hwnd):
    return hwnd == win32gui.GetForegroundWindow()

def spam_f15():
    while True:
        steps = load_steps_from_cfg()
        hwnd = find_cs2_window()
        if hwnd and is_window_in_focus(hwnd):
            win32api.keybd_event(VK_F15, 0, 0, 0)
            time.sleep(steps)
            win32api.keybd_event(VK_F15, 0, win32con.KEYEVENTF_KEYUP, 0)
        time.sleep(steps)

if __name__ == "__main__":
    if not os.path.isfile(cfg_path):
        print(f"[ОШИБКА]: Файл не найден: {cfg_path}")
    else:
        print("[✓] Rainbow HUD активен.")
        threading.Thread(target=update_rainbow_hud, daemon=True).start()
        threading.Thread(target=spam_f15, daemon=True).start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n[!] Скрипт остановлен пользователем.")
