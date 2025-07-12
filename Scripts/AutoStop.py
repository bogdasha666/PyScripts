from pynput import keyboard
import threading
import time
import win32gui
import win32process
import psutil
import random

# Универсальный маппинг букв (только англ) в VK-коды
VK_LETTERS = {
    'a': 0x41, 'b': 0x42, 'c': 0x43, 'd': 0x44, 'e': 0x45, 'f': 0x46, 'g': 0x47, 'h': 0x48, 'i': 0x49, 'j': 0x4A,
    'k': 0x4B, 'l': 0x4C, 'm': 0x4D, 'n': 0x4E, 'o': 0x4F, 'p': 0x50, 'q': 0x51, 'r': 0x52, 's': 0x53, 't': 0x54,
    'u': 0x55, 'v': 0x56, 'w': 0x57, 'x': 0x58, 'y': 0x59, 'z': 0x5A,
    'A': 0x41, 'B': 0x42, 'C': 0x43, 'D': 0x44, 'E': 0x45, 'F': 0x46, 'G': 0x47, 'H': 0x48, 'I': 0x49, 'J': 0x4A,
    'K': 0x4B, 'L': 0x4C, 'M': 0x4D, 'N': 0x4E, 'O': 0x4F, 'P': 0x50, 'Q': 0x51, 'R': 0x52, 'S': 0x53, 'T': 0x54,
    'U': 0x55, 'V': 0x56, 'W': 0x57, 'X': 0x58, 'Y': 0x59, 'Z': 0x5A,
}

# Состояние клавиш
keys_state = {'a': False, 'd': False}
controller = keyboard.Controller()

# Флаг, чтобы игнорировать свои нажатия
suppress_output = False

# Виртуальные коды клавиш (VK)
VK_A = 0x41  # клавиша A
VK_D = 0x44  # клавиша D

# Глобальный флаг активности автотопа
is_autostop_active = False

# Получение бинда из файла
def get_toggle_bind():
    try:
        with open('autostop_bind.flag', 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('//'):
                    return line[0].lower()
    except Exception:
        pass
    return None

# Текущий бинд и время последней проверки
_toggle_bind = get_toggle_bind()
_last_bind_check = 0

# Проверка бинда с авто-обновлением (раз в 0.5 сек)
def get_current_toggle_bind():
    global _toggle_bind, _last_bind_check
    now = time.time()
    if now - _last_bind_check > 0.5:
        new_bind = get_toggle_bind()
        if new_bind != _toggle_bind:
            print(f"[autostop] Бинд изменён на: {new_bind}")
            _toggle_bind = new_bind
        _last_bind_check = now
    return _toggle_bind

def get_current_toggle_bind_vk():
    """Возвращает VK-код текущего бинда (с учётом русских и англ. букв)"""
    bind = get_current_toggle_bind()
    if not bind:
        return None
    return VK_LETTERS.get(bind, None)

def is_cs2_active():
    """Проверяет, активно ли окно cs2.exe"""
    try:
        hwnd = win32gui.GetForegroundWindow()
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        process = psutil.Process(pid)
        return process.name().lower() == "cs2.exe"
    except Exception:
        return False

def press_opposite(key_char):
    global suppress_output
    if key_char == 'a':
        opposite_vk = VK_D
        opposite_name = 'd'
    else:
        opposite_vk = VK_A
        opposite_name = 'a'

    # Генерация случайной задержки от 0.11 до 0.9 секунд
    hold_time = random.uniform(0.11, 0.09)

    print(f"Нажимаем противоположную клавишу '{opposite_name}' на {hold_time:.2f} секунд")
    suppress_output = True
    controller.press(keyboard.KeyCode.from_vk(opposite_vk))
    time.sleep(hold_time)
    controller.release(keyboard.KeyCode.from_vk(opposite_vk))
    suppress_output = False
    print(f"Отпускаем противоположную клавишу '{opposite_name}'")

def on_press(key):
    global suppress_output, is_autostop_active
    if suppress_output or not is_cs2_active():
        return

    toggle_bind = get_current_toggle_bind()
    toggle_bind_vk = get_current_toggle_bind_vk()
    # Toggle режим по бинду (по символу или по VK)
    try:
        key_char = getattr(key, 'char', None)
        mapped_char = key_char.lower() if key_char else None
        if (mapped_char and mapped_char == toggle_bind) or (toggle_bind_vk and hasattr(key, 'vk') and key.vk == toggle_bind_vk):
            is_autostop_active = not is_autostop_active
            print(f"[autostop] {'Включено' if is_autostop_active else 'Выключено'} (бинд: {toggle_bind.upper()})")
            return
    except AttributeError:
        pass

    if not is_autostop_active:
        return

    try:
        if key.vk == VK_A:
            keys_state['a'] = True
            if keys_state['d']:
                keys_state['d'] = False
        elif key.vk == VK_D:
            keys_state['d'] = True
            if keys_state['a']:
                keys_state['a'] = False
    except AttributeError:
        pass

def on_release(key):
    global suppress_output
    if suppress_output or not is_cs2_active() or not is_autostop_active:
        return

    try:
        if key.vk == VK_A and keys_state['a']:
            keys_state['a'] = False
            threading.Thread(target=press_opposite, args=('a',), daemon=True).start()
        elif key.vk == VK_D and keys_state['d']:
            keys_state['d'] = False
            threading.Thread(target=press_opposite, args=('d',), daemon=True).start()
    except AttributeError:
        pass

def start_listener():
    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()

def main():
    listener_thread = threading.Thread(target=start_listener)
    listener_thread.daemon = True
    listener_thread.start()

    print("Скрипт запущен. Работает только в окне cs2.exe. Нажми 'Ctrl+C' для выхода.")
    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nСкрипт завершён.")

if __name__ == "__main__":
    main()
