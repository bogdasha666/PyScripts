import time
import threading
import win32api
import win32con
import win32gui
import win32process
import psutil
from ahk import AHK
import string
import os

BIND_FILE = 'r8double_bind.flag'
ahk = AHK()

# Карта символов к виртуальным кодам клавиш (A-Z, 0-9)
VK_CODE = {ch: ord(ch) for ch in string.ascii_uppercase}
VK_CODE.update({
    '1': 0x31,
    '2': 0x32,
    '3': 0x33,
    '4': 0x34,
    '5': 0x35,
    '6': 0x36,
    '7': 0x37,
    '8': 0x38,
    '9': 0x39,
    '0': 0x30,
    # Можно добавить спецклавиши по необходимости
})

def get_bind_key():
    try:
        with open(BIND_FILE, 'r', encoding='utf-8') as f:
            key = f.read().strip().upper()
        return key
    except Exception:
        return ''

def is_cs2_active():
    hwnd = win32gui.GetForegroundWindow()
    if hwnd == 0:
        return False
    try:
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        proc = psutil.Process(pid)
        return proc.name().lower() == 'cs2.exe'
    except Exception:
        return False

def r8_double_action():
    ahk.send('{Blind}{LButton down}')
    time.sleep(0.001)
    ahk.send('{Blind}{LButton up}')
    ahk.send('{Blind}{LButton down}')
    time.sleep(0.026)
    ahk.send('{Blind}{LButton up}')
    ahk.send('{Blind}{RButton down}')
    time.sleep(0.28)
    ahk.send('{Blind}{LButton down}')
    time.sleep(0.30)
    ahk.send('{Blind}{LButton up}')
    ahk.send('{Blind}{RButton up}')

def main():
    print(f'R8 Double Python script запущен. Бинд читается из файла r8double_bind.flag. Для выхода закройте окно.')
    prev_state = False
    vk = None
    last_mtime = None
    last_file_check = 0
    FILE_CHECK_INTERVAL = 2.0  # секунды
    while True:
        now = time.time()
        if now - last_file_check > FILE_CHECK_INTERVAL:
            try:
                mtime = os.path.getmtime(BIND_FILE)
                if mtime != last_mtime:
                    bind_key = get_bind_key()
                    vk = VK_CODE.get(bind_key.upper(), 0xA4)  # по умолчанию LAlt
                    print(f'Бинд обновлён: {bind_key} (VK={vk})')
                    last_mtime = mtime
            except Exception:
                pass
            last_file_check = now
        if vk is not None and is_cs2_active():
            state = win32api.GetAsyncKeyState(vk) & 0x8000
            if state and not prev_state:
                threading.Thread(target=r8_double_action, daemon=True).start()
            prev_state = state
        else:
            prev_state = False
        time.sleep(0.01)

if __name__ == '__main__':
    main()
