import time
import win32api
import win32con
import win32gui
import win32process
import psutil
from pynput import keyboard

# VK-коды
VK_A = 0x41
VK_D = 0x44
VK_F19 = 0x82

# Путь к конфигу
CFG_PATH = r"C:\Program Files (x86)\Steam\steamapps\common\Counter-Strike Global Offensive\game\csgo\cfg\pyscripts7.cfg"

# Константы для yaw
RATIO = 4306.22 / 180  # 23.9234444444
def angle_to_yaw(angle):
    return angle * RATIO

def is_cs2_in_foreground():
    try:
        hwnd = win32gui.GetForegroundWindow()
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        p = psutil.Process(pid)
        # Можно заменить на свой вариант поиска окна, если нужно
        return p.name().lower() in ("cs2.exe", "csgo.exe")
    except Exception:
        return False

def simulate_f19_press():
    win32api.keybd_event(VK_F19, 0, 0, 0)
    time.sleep(0.03)
    win32api.keybd_event(VK_F19, 0, win32con.KEYEVENTF_KEYUP, 0)

def write_yaw(angle):
    yaw = angle_to_yaw(angle)
    content = f"yaw {yaw:.4f} 1 0\n"
    try:
        with open(CFG_PATH, "w", encoding="utf-8") as f:
            f.write(content)
    except Exception as e:
        print(f"[Ошибка записи файла]: {e}")

# Состояния для предотвращения спама
key_states = {VK_A: False, VK_D: False}
last_pressed = None  # VK_A или VK_D

print("[INFO] Скрипт запущен. Спамит F19 и пишет yaw при A/D в CS2 окне.")

def on_press(key):
    global last_pressed
    try:
        if not is_cs2_in_foreground():
            return
        vk = key.vk if hasattr(key, 'vk') else None
        if vk in (VK_A, VK_D):
            if not key_states[vk]:  # Только на первое нажатие
                key_states[vk] = True
                last_pressed = vk
                simulate_f19_press()
                if vk == VK_A:
                    write_yaw(-22.5)
                elif vk == VK_D:
                    write_yaw(22.5)
    except Exception as e:
        print(f"[on_press] {e}")

def on_release(key):
    global last_pressed
    try:
        vk = key.vk if hasattr(key, 'vk') else None
        if vk in (VK_A, VK_D):
            key_states[vk] = False
            # Если другая клавиша зажата — переключить yaw
            other_vk = VK_D if vk == VK_A else VK_A
            if key_states[other_vk]:
                last_pressed = other_vk
                simulate_f19_press()
                if other_vk == VK_A:
                    write_yaw(-22.5)
                elif other_vk == VK_D:
                    write_yaw(22.5)
            else:
                last_pressed = None
    except Exception as e:
        print(f"[on_release] {e}")

with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
    listener.join()
