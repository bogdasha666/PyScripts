import threading
import time
import random
import ctypes
import win32file
import win32api
import win32con
import json
import win32gui
import win32process
import psutil
from pynput.keyboard import Controller as KeyboardController, Key

keyboard = KeyboardController()

# Эти переменные должны быть динамическими в реальном скрипте
finish = False
auto_pistol_enabled = True
active_weapon = "glock"  # Пример оружия из GSI

PIPE_NAME = r'\\.\pipe\gsi_pipe'

# Список всех пистолетов CS2 (можно дополнить при необходимости)
PISTOL_WEAPONS = {
    "weapon_glock", "weapon_usp_silencer", "weapon_p250", "weapon_fiveseven", "weapon_deagle", "weapon_elite", "weapon_hkp2000", "weapon_tec9"  # и др.
}

# Проверка, зажата ли ЛКМ
def is_left_mouse_pressed():
    try:
        return ctypes.windll.user32.GetAsyncKeyState(0x01) & 0x8000 != 0
    except Exception as e:
        print(f"[!] Ошибка в GetAsyncKeyState: {e}")
        return False

# Эмуляция нажатия F16 через win32api
VK_F16 = 0x7F  # Виртуальный код клавиши F16

def press_f16():
    try:
        win32api.keybd_event(VK_F16, 0, 0, 0)
        time.sleep(0.01)
        win32api.keybd_event(VK_F16, 0, win32con.KEYEVENTF_KEYUP, 0)
    except Exception as e:
        print(f"[!] Ошибка при эмуляции клавиши F16: {e}")

def get_active_weapon_from_pipe():
    try:
        handle = win32file.CreateFile(
            PIPE_NAME,
            win32file.GENERIC_READ,
            0, None,
            win32file.OPEN_EXISTING,
            0, None)
        result, data = win32file.ReadFile(handle, 65536)
        handle.Close()
        gsi_data = json.loads(data.decode('utf-8'))
        weapons = gsi_data.get("player", {}).get("weapons", {})
        for weapon in weapons.values():
            if weapon.get("state") == "active":
                return weapon.get("name")
    except Exception:
        return None
    return None

# Проверка, что окно CS2 в фокусе
def is_cs2_in_foreground():
    try:
        hwnd = win32gui.GetForegroundWindow()
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        p = psutil.Process(pid)
        return p.name().lower() == "cs2.exe"
    except Exception:
        return False

def is_cursor_active():
    try:
        pt = win32gui.GetCursorPos()
        hwnd = win32gui.GetForegroundWindow()
        rect = win32gui.GetWindowRect(hwnd)
        width = rect[2] - rect[0]
        height = rect[3] - rect[1]
        center_x = rect[0] + width // 2
        center_y = rect[1] + height // 2
        return abs(pt[0] - center_x) > 5 or abs(pt[1] - center_y) > 5
    except Exception:
        return False

# Поток автопистолета
def auto_pistol():
    def run():
        global finish
        print("[+] Автопистолет запущен")
        while not finish:
            try:
                if auto_pistol_enabled and is_cs2_in_foreground():
                    active_weapon = get_active_weapon_from_pipe()
                    if active_weapon in PISTOL_WEAPONS:
                        if is_left_mouse_pressed() and not is_cursor_active():
                            press_f16()
            except Exception as e:
                print(f"[!] Ошибка в основном цикле: {e}")
            time.sleep(0.015625)  # 64 тика/сек
        print("[+] Автопистолет завершён")

    threading.Thread(target=run, daemon=True).start()

# Пример запуска
if __name__ == "__main__":
    auto_pistol()
    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        finish = True
        print("[*] Остановлено вручную")
