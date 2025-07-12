import time
import ctypes
from ctypes import wintypes
import win32process
import win32gui
import win32api
import win32con
import psutil
import win32file
import json

# === НАСТРОЙКИ ===
press_duration_ms = 190  # Длительность зажатия F15
release_delay_ms = 190    # Пауза между нажатием

# === Константы для F15 ===
VK_F15 = 0x7E  # Virtual key code for F15

# === Имя пайпа ===
PIPE_NAME = r'\\.\pipe\gsi_pipe'

def press_f15():
    win32api.keybd_event(VK_F15, 0, 0, 0)

def release_f15():
    win32api.keybd_event(VK_F15, 0, win32con.KEYEVENTF_KEYUP, 0)

# === Проверка: активно ли окно cs2.exe ===
def is_cs2_in_foreground():
    try:
        hwnd = win32gui.GetForegroundWindow()
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        p = psutil.Process(pid)
        return p.name().lower() == "cs2.exe"
    except Exception:
        return False

def get_active_weapon_from_pipe():
    try:
        # Подключаемся к пайпу
        handle = win32file.CreateFile(
            PIPE_NAME,
            win32file.GENERIC_READ,
            0, None,
            win32file.OPEN_EXISTING,
            0, None)
        
        # Читаем данные из пайпа
        result, data = win32file.ReadFile(handle.handle, 65536)
        handle.Close()
        
        # Парсим JSON данные
        if isinstance(data, bytes):
            gsi_data = json.loads(data.decode('utf-8'))
        else:
            gsi_data = json.loads(data)
        weapons = gsi_data.get("player", {}).get("weapons", {})
        
        # Ищем активное оружие
        for weapon in weapons.values():
            if weapon.get("state") == "active":
                return weapon.get("name")
                
    except Exception as e:
        print(f"[ERROR] Pipe connection failed: {e}")
        return None
    return None

def main():
    print("Waiting for GSI pipe...")
    while True:
        try:
            active_weapon = get_active_weapon_from_pipe()
            if active_weapon == "weapon_revolver" and is_cs2_in_foreground():
                press_f15()
                time.sleep(press_duration_ms / 1000)
                release_f15()
                time.sleep(release_delay_ms / 1000)
            else:
                time.sleep(0.1)
        except Exception as e:
            print(f"[ERROR] {e}")
            time.sleep(1)

if __name__ == "__main__":
    main()
