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

BIND_FILE = 'trigger_bind.flag'
THRESHOLD = 20
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
    with open(BIND_FILE, 'r', encoding='utf-8') as f:
        key = f.read().strip().upper()
    return key

def get_pixel_color(x, y):
    color = ahk.pixel_get_color(int(x), int(y))
    color = color[2:]
    r = int(color[0:2], 16)
    g = int(color[2:4], 16)
    b = int(color[4:6], 16)
    return (r, g, b)

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

class TriggerBot:
    def __init__(self):
        self.active = False
        self.thread = None
        self.stop_event = threading.Event()

    def toggle(self):
        self.active = not self.active
        if self.active:
            print(f'TriggerBot ON')
            self.stop_event.clear()
            self.thread = threading.Thread(target=self.run, daemon=True)
            self.thread.start()
        else:
            print('TriggerBot OFF')
            self.stop_event.set()

    def run(self):
        x, y = ahk.mouse_position
        color1 = get_pixel_color(x+2, y+2)
        try:
            while not self.stop_event.is_set():
                time.sleep(0.001)
                if not is_cs2_active():
                    continue
                x, y = ahk.mouse_position
                color2 = get_pixel_color(x+2, y+2)
                if any(abs(c1 - c2) > THRESHOLD for c1, c2 in zip(color1, color2)):
                    ahk.send('{LButton}')
        finally:
            pass

def main():
    bot = TriggerBot()
    print(f'Запущен TriggerBot. Бинд: (читается из файла) [toggle]')
    prev_state = False
    last_bind = None
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
                    vk = VK_CODE.get(bind_key.upper(), 0x58)
                    print(f'Бинд обновлён: {bind_key} (VK={vk})')
                    last_mtime = mtime
            except Exception as e:
                pass  # файл может отсутствовать/быть недоступен
            last_file_check = now
        if vk is not None:
            state = win32api.GetAsyncKeyState(vk) & 0x8000
            if state and not prev_state:
                bot.toggle()
                time.sleep(0.2)  # антидребезг
            prev_state = state
        time.sleep(0.01)

if __name__ == '__main__':
    main()
