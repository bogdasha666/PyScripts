import time
import win32api
import win32con
import win32file
import json
import ctypes
import win32gui
import win32process
import psutil

PIPE_NAME = r'\\.\pipe\gsi_pipe'
VK_W = 0x57  # Виртуальный код клавиши W

# Проверка, зажата ли клавиша W
GetAsyncKeyState = ctypes.windll.user32.GetAsyncKeyState
def is_w_pressed():
    return (GetAsyncKeyState(VK_W) & 0x8000) != 0

def is_cs2_in_foreground():
    try:
        hwnd = win32gui.GetForegroundWindow()
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        p = psutil.Process(pid)
        return p.name().lower() == "cs2.exe"
    except Exception:
        return False

def press_w():
    win32api.keybd_event(VK_W, 0, 0, 0)
    time.sleep(0.02)
    win32api.keybd_event(VK_W, 0, win32con.KEYEVENTF_KEYUP, 0)

def get_round_start_state():
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
        round_info = gsi_data.get('round', {})
        # round.phase: 'freezetime', 'live', 'over', etc.
        # round.bomb: 'planted', ...
        # round.win_team: 'T', 'CT', ...
        # round: { 'phase': ..., ... }
        return round_info.get('phase') == 'live'
    except Exception:
        return False

print("AntiAFK активен. Ожидание старта раунда...")

old_round_start = False

try:
    while True:
        round_start = get_round_start_state()
        if round_start != old_round_start:
            if round_start:  # Новый раунд начался
                if is_cs2_in_foreground():
                    if not is_w_pressed():
                        print("[AntiAFK] Новый раунд! Имитация нажатия W.")
                        press_w()
                    else:
                        print("[AntiAFK] Новый раунд, но W уже зажата.")
                else:
                    print("[AntiAFK] Новый раунд, но окно cs2.exe не в фокусе.")
            old_round_start = round_start
        time.sleep(0.05)
except KeyboardInterrupt:
    print("Выход...")
