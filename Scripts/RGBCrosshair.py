import time
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

# Название окна CS2
WINDOW_NAME = "Counter-Strike 2"
# Виртуальный код клавиши F14 (используется для обновления crosshair)
# VK_F14 = 0x7D
# Вместо F14 используем F13
VK_F13 = 0x7C

# --- Флаги ---
enable_rgb = True         # Включение RGB-прицела
enable_f14_spam = True    # Включение спама F14 для обновления crosshair

def update_rgb_crosshair():
    """Обновляет конфиг crosshair с текущим RGB, только если цвет изменился"""
    print("[•] Поток RGB Crosshair запущен.")
    last_rgb = None
    while True:
        if not enable_rgb:
            time.sleep(1)
            continue
        try:
            r, g, b = synced_rgb()
            current_rgb = (r, g, b)
            if last_rgb == current_rgb:
                time.sleep(0.01)
                continue
            last_rgb = current_rgb
            content = (
                f"cl_crosshaircolor 5; "
                f"cl_crosshaircolor_r {r}; "
                f"cl_crosshaircolor_g {g}; "
                f"cl_crosshaircolor_b {b}\n"
            )
            cfg_dir = find_csgo_cfg_path()
            if not cfg_dir:
                print('[ОШИБКА]: Папка cfg не найдена. Проверьте путь установки Steam и CS:GO.')
                exit(1)
            cfg_path = os.path.join(cfg_dir, 'pyscripts1.cfg')
            with open(cfg_path, "w") as f:
                f.write(content)
        except Exception as e:
            print(f"[Ошибка записи файла]: {e}")
        time.sleep(0.01)

def find_cs2_window():
    """Возвращает дескриптор окна CS2"""
    return win32gui.FindWindow(None, WINDOW_NAME)

def is_window_in_focus(hwnd):
    """Проверяет, в фокусе ли окно CS2"""
    return hwnd and hwnd == win32gui.GetForegroundWindow()

def spam_f14():
    """Периодически нажимает F13, чтобы применить crosshair"""
    print("[•] Поток F13 спама запущен.")
    while True:
        if not enable_f14_spam:
            time.sleep(1)
            continue
        try:
            steps = load_steps_from_cfg()
            hwnd = find_cs2_window()
            if is_window_in_focus(hwnd):
                win32api.keybd_event(VK_F13, 0, 0, 0)
                time.sleep(steps)
                win32api.keybd_event(VK_F13, 0, win32con.KEYEVENTF_KEYUP, 0)
            time.sleep(steps)
        except Exception as e:
            print(f"[Ошибка симуляции клавиши]: {e}")
            time.sleep(1)

if __name__ == "__main__":
    if not os.path.isfile(os.path.join(find_csgo_cfg_path() or '', 'pyscripts1.cfg')):
        print(f"[ОШИБКА]: Файл не найден: {os.path.join(find_csgo_cfg_path() or '', 'pyscripts1.cfg')}")
    else:
        print("[✓] RGB Crosshair запущен.")
        if enable_rgb:
            threading.Thread(target=update_rgb_crosshair, daemon=True).start()
        else:
            print("[!] RGB обновление отключено.")
        if enable_f14_spam:
            threading.Thread(target=spam_f14, daemon=True).start()
        else:
            print("[!] F14 спам отключен.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n[!] Скрипт остановлен пользователем.")
