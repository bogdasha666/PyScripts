import time
import win32api
import win32con
import win32gui
import win32process
import psutil
from ahk import AHK

# VK-коды
VK_SPACE = win32con.VK_SPACE

# Маппинг букв в VK-коды (только англ буквы)
VK_LETTERS = {
    'A': 0x41, 'B': 0x42, 'C': 0x43, 'D': 0x44, 'E': 0x45, 'F': 0x46, 'G': 0x47, 'H': 0x48, 'I': 0x49, 'J': 0x4A,
    'K': 0x4B, 'L': 0x4C, 'M': 0x4D, 'N': 0x4E, 'O': 0x4F, 'P': 0x50, 'Q': 0x51, 'R': 0x52, 'S': 0x53, 'T': 0x54,
    'U': 0x55, 'V': 0x56, 'W': 0x57, 'X': 0x58, 'Y': 0x59, 'Z': 0x5A,
}

ahk = AHK()

def is_cs2_in_foreground():
    try:
        hwnd = win32gui.GetForegroundWindow()
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        p = psutil.Process(pid)
        return p.name().lower() == "cs2.exe"
    except Exception:
        return False

def get_bind_key():
    try:
        with open("jumpshoot_bind.flag", "r", encoding="utf-8") as f:
            key_name = f.read().strip().upper()
            if key_name == 'SPACE':
                return VK_SPACE
            if len(key_name) == 1:
                vk_code = VK_LETTERS.get(key_name)
                if vk_code:
                    return vk_code
            return None
    except Exception:
        return None

def is_key_pressed(vk_code):
    return win32api.GetAsyncKeyState(vk_code) & 0x8000 != 0

def press_space_and_lmb_ahk():
    ahk_script = '''
    Send, {Space down}
    Sleep, 50
    Send, {Space up}
    Sleep, 500
    Click
    '''
    ahk.run_script(ahk_script)

print("JumpShoot script started (AHK). Ожидание бинда...")

if __name__ == "__main__":
    last_key_state = False
    try:
        while True:
            bind_vk = get_bind_key()
            if bind_vk is None:
                time.sleep(0.5)
                continue
            key_pressed = is_key_pressed(bind_vk)
            cs2_fg = is_cs2_in_foreground()
            if key_pressed and not last_key_state and cs2_fg:
                print("Бинд нажат, выполняю press_space_and_lmb_ahk()")
                press_space_and_lmb_ahk()
                time.sleep(0.2)
            last_key_state = key_pressed
            time.sleep(0.01)
    except KeyboardInterrupt:
        print("Выход...")
