import win32file
import win32con
import win32gui
import win32api
import json
import time
import threading

PIPE_NAME = r'\\.\pipe\gsi_pipe'
PRIMARY_WEAPONS = {
    "weapon_ak47", "weapon_m4a1", "weapon_m4a1_silencer",
    "weapon_aug", "weapon_sg556", "weapon_famas", "weapon_galilar",
    "weapon_awp", "weapon_ssg08", "weapon_scar20", "weapon_g3sg1",
    "weapon_mp9", "weapon_mac10", "weapon_mp7", "weapon_ump45",
    "weapon_p90", "weapon_bizon", "weapon_m249", "weapon_negev",
    "weapon_nova", "weapon_xm1014", "weapon_mag7", "weapon_sawedoff"
}

CS2_WINDOW_TITLES = ["Counter-Strike 2", "Counter-Strike"]


def is_cs2_active():
    hwnd = win32gui.GetForegroundWindow()
    if hwnd:
        title = win32gui.GetWindowText(hwnd)
        for t in CS2_WINDOW_TITLES:
            if t.lower() in title.lower():
                return True
    return False


def press_f16():
    win32api.keybd_event(win32con.VK_F16, 0, 0, 0)
    time.sleep(0.05)
    win32api.keybd_event(win32con.VK_F16, 0, win32con.KEYEVENTF_KEYUP, 0)


def press_f17():
    win32api.keybd_event(win32con.VK_F17, 0, 0, 0)
    time.sleep(0.05)
    win32api.keybd_event(win32con.VK_F17, 0, win32con.KEYEVENTF_KEYUP, 0)


VK_LETTERS = {
    'A': 0x41, 'B': 0x42, 'C': 0x43, 'D': 0x44, 'E': 0x45, 'F': 0x46, 'G': 0x47, 'H': 0x48, 'I': 0x49, 'J': 0x4A,
    'K': 0x4B, 'L': 0x4C, 'M': 0x4D, 'N': 0x4E, 'O': 0x4F, 'P': 0x50, 'Q': 0x51, 'R': 0x52, 'S': 0x53, 'T': 0x54,
    'U': 0x55, 'V': 0x56, 'W': 0x57, 'X': 0x58, 'Y': 0x59, 'Z': 0x5A,
}

BIND_FLAG_PATH = 'xcarry_bind.flag'


def get_bind_vk():
    try:
        with open(BIND_FLAG_PATH, 'r', encoding='utf-8') as f:
            key = f.read().strip().upper()
            return VK_LETTERS.get(key, None)
    except Exception:
        return None


def check_primary_weapon_and_press_toggle():
    last_primary_weapon = None
    toggle_enabled = False
    last_key_state = False
    while True:
        vk_code = get_bind_vk()
        if vk_code is not None:
            key_state = win32api.GetAsyncKeyState(vk_code) & 0x8000
            if key_state and not last_key_state:
                toggle_enabled = not toggle_enabled
            last_key_state = key_state
        else:
            toggle_enabled = False
        if toggle_enabled:
            try:
                handle = win32file.CreateFile(
                    PIPE_NAME,
                    win32con.GENERIC_READ,
                    0, None,
                    win32con.OPEN_EXISTING,
                    0, None)
                result, data = win32file.ReadFile(handle, 65536)
                handle.Close()
                gsi_data = json.loads(data.decode('utf-8'))
                weapons = gsi_data.get('player', {}).get('weapons', {})
                # Найти первое primary-оружие в инвентаре (неважно активно или нет)
                primary_weapon = None
                for w in weapons.values():
                    if w.get('name') in PRIMARY_WEAPONS:
                        primary_weapon = w.get('name')
                        break
                if primary_weapon and is_cs2_active():
                    if last_primary_weapon != primary_weapon:
                        press_f17()
                last_primary_weapon = primary_weapon
            except Exception as e:
                time.sleep(0.1)
        time.sleep(0.01)


def main():
    t = threading.Thread(target=check_primary_weapon_and_press_toggle, daemon=True)
    t.start()
    print("[xcarry] Скрипт запущен. Ожидание данных из пайпа... (toggle mode)")
    while True:
        time.sleep(1)

if __name__ == "__main__":
    main()
