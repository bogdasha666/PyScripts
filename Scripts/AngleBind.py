import time
import win32api
import win32con
import win32gui
import win32process
import psutil

# Виртуальный код клавиши F19
VK_F19 = 0x82

# Маппинг букв в VK-коды (только англ буквы)
VK_LETTERS = {
    'A': 0x41, 'B': 0x42, 'C': 0x43, 'D': 0x44, 'E': 0x45, 'F': 0x46, 'G': 0x47, 'H': 0x48, 'I': 0x49, 'J': 0x4A,
    'K': 0x4B, 'L': 0x4C, 'M': 0x4D, 'N': 0x4E, 'O': 0x4F, 'P': 0x50, 'Q': 0x51, 'R': 0x52, 'S': 0x53, 'T': 0x54,
    'U': 0x55, 'V': 0x56, 'W': 0x57, 'X': 0x58, 'Y': 0x59, 'Z': 0x5A,
}

def press_key(vk_code):
    win32api.keybd_event(vk_code, 0, 0, 0)
    time.sleep(0.05)
    win32api.keybd_event(vk_code, 0, win32con.KEYEVENTF_KEYUP, 0)

def is_key_pressed(vk_code):
    return win32api.GetAsyncKeyState(vk_code) & 0x8000 != 0

def is_cs2_in_foreground():
    try:
        hwnd = win32gui.GetForegroundWindow()
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        p = psutil.Process(pid)
        return p.name().lower() == "cs2.exe"
    except Exception:
        return False

def get_toggle_key():
    try:
        with open("angle_bind.flag", "r", encoding="utf-8") as f:
            key_name = f.read().strip().upper()
            if len(key_name) == 1:
                vk_code = VK_LETTERS.get(key_name)
                if vk_code:
                    return vk_code
            return None  # Нет валидного бинда
    except Exception:
        return None  # В случае ошибки возвращаем None

print("Скрипт anglebind запущен")
print("Нажмите установленный бинд для активации F19")

last_key_state = False

try:
    while True:
        try:
            toggle_key = get_toggle_key()
            if toggle_key is None:
                print("Бинд не установлен или некорректен. Ожидание...")
                time.sleep(0.5)
                continue
            print(f"Текущий бинд: {toggle_key}")
            key_pressed = is_key_pressed(toggle_key)
            print(f"Клавиша нажата: {key_pressed}")
            cs2_fg = is_cs2_in_foreground()
            print(f"CS2 в фокусе: {cs2_fg}")

            if key_pressed and not last_key_state and cs2_fg:
                print("Активация F19")
                press_key(VK_F19)

            last_key_state = key_pressed
            time.sleep(0.05)
        except Exception as e:
            print(f"Ошибка в цикле: {e}")
except KeyboardInterrupt:
    print("Выход...")