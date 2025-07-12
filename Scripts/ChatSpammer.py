import time
import win32api
import win32con
import win32gui
import win32process
import psutil
import threading

# Маппинг букв в VK-коды
VK_LETTERS = {
    'A': 0x41, 'B': 0x42, 'C': 0x43, 'D': 0x44, 'E': 0x45, 'F': 0x46, 'G': 0x47, 'H': 0x48, 'I': 0x49, 'J': 0x4A,
    'K': 0x4B, 'L': 0x4C, 'M': 0x4D, 'N': 0x4E, 'O': 0x4F, 'P': 0x50, 'Q': 0x51, 'R': 0x52, 'S': 0x53, 'T': 0x54,
    'U': 0x55, 'V': 0x56, 'W': 0x57, 'X': 0x58, 'Y': 0x59, 'Z': 0x5A,
}

def press_f22():
    """Simulate F22 key press"""
    win32api.keybd_event(win32con.VK_F22, 0, 0, 0)  # Key down
    time.sleep(0.1)
    win32api.keybd_event(win32con.VK_F22, 0, win32con.KEYEVENTF_KEYUP, 0)  # Key up

def is_cs2_active():
    try:
        hwnd = win32gui.GetForegroundWindow()
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        p = psutil.Process(pid)
        return p.name().lower() == "cs2.exe"
    except Exception:
        return False

def get_bind_key():
    try:
        with open("chatspammer_bind.flag", "r", encoding="utf-8") as f:
            key_name = f.read().strip().upper()
            if len(key_name) == 1:
                vk_code = VK_LETTERS.get(key_name)
                if vk_code:
                    return vk_code
            return None  # Нет бинда
    except Exception:
        return None  # В случае ошибки возвращаем None

def is_key_pressed(vk_code):
    return win32api.GetAsyncKeyState(vk_code) & 0x8000 != 0

def spam_f22():
    """Function to spam F22 key with 1 second interval"""
    while True:
        if spam_enabled and is_cs2_active():
            press_f22()
        time.sleep(1)  # 1 second interval

def main():
    global spam_enabled
    spam_enabled = False
    
    # Start spam thread
    spam_thread = threading.Thread(target=spam_f22, daemon=True)
    spam_thread.start()
    
    print("[info] Chat Spammer script started")
    print("[info] Press the configured bind key to toggle F22 spam")
    last_key_state = False
    
    while True:
        try:
            bind_key = get_bind_key()
            if bind_key is None:
                print("[warn] No valid bind key found in chatspammer_bind.flag. Spammer is inactive.")
                time.sleep(1)
                continue
            key_pressed = is_key_pressed(bind_key)
            
            if key_pressed and not last_key_state and is_cs2_active():
                spam_enabled = not spam_enabled
                status = "enabled" if spam_enabled else "disabled"
                print(f"[info] F22 spam {status}")
            
            last_key_state = key_pressed
            time.sleep(0.05)  # Small delay to prevent high CPU usage
            
        except Exception as e:
            print(f"[error] Main loop error: {e}")
            time.sleep(1)  # Longer delay on error

if __name__ == "__main__":
    main() 