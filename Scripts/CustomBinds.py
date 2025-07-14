import os
import time
import win32api
import win32con
from threading import Thread
import win32gui
import win32process
import psutil
import win32file
import win32pipe
import json
from steam_path_utils import find_csgo_cfg_path

# VK codes
VK_F24 = 0x87  # F24 virtual-key code

# Special keys mapping
SPECIAL_KEYS = {
    'ESCAPE': win32con.VK_ESCAPE,
    'TAB': win32con.VK_TAB,
    'CAPS': win32con.VK_CAPITAL,
    'SHIFT': win32con.VK_SHIFT,
    'CTRL': win32con.VK_CONTROL,
    'ALT': win32con.VK_MENU,
    'SPACE': win32con.VK_SPACE,
    'ENTER': win32con.VK_RETURN,
    'BACKSPACE': win32con.VK_BACK,
    'DELETE': win32con.VK_DELETE,
    'HOME': win32con.VK_HOME,
    'END': win32con.VK_END,
    'PAGEUP': win32con.VK_PRIOR,
    'PAGEDOWN': win32con.VK_NEXT,
    'INSERT': win32con.VK_INSERT,
    'F1': win32con.VK_F1,
    'F2': win32con.VK_F2,
    'F3': win32con.VK_F3,
    'F4': win32con.VK_F4,
    'F5': win32con.VK_F5,
    'F6': win32con.VK_F6,
    'F7': win32con.VK_F7,
    'F8': win32con.VK_F8,
    'F9': win32con.VK_F9,
    'F10': win32con.VK_F10,
    'F11': win32con.VK_F11,
    'F12': win32con.VK_F12,
    'F24': VK_F24,
    # Media keys
    'MEDIANEXT': 0xB0,  # VK_MEDIA_NEXT_TRACK
    'MEDIAPREVIOUS': 0xB1,  # VK_MEDIA_PREV_TRACK
    'MEDIASTOP': 0xB2,  # VK_MEDIA_STOP
    'MEDIAPLAY': 0xB3,  # VK_MEDIA_PLAY_PAUSE
    'VOLUMEUP': 0xAF,  # VK_VOLUME_UP
    'VOLUMEDOWN': 0xAE,  # VK_VOLUME_DOWN
    'VOLUMEMUTE': 0xAD,  # VK_VOLUME_MUTE
}

# Track key states to prevent multiple triggers
key_states = {}

cfg_dir = find_csgo_cfg_path()
if not cfg_dir:
    print('[ОШИБКА]: Папка cfg не найдена. Проверьте путь установки Steam и CS:GO.')
    exit(1)
CUSTOMBIND_CFG_PATH = os.path.join(cfg_dir, 'pyscripts12.cfg')
PIPE_NAME = r'\\.\pipe\gsi_pipe'

def get_vk_code(key):
    # First check if it's a special key
    if key.upper() in SPECIAL_KEYS:
        return SPECIAL_KEYS[key.upper()]
    
    # If it's a single character, convert it to VK code
    if len(key) == 1:
        return ord(key.upper())
    
    # If we can't determine the VK code, return None
    return None

def read_bind_file(filename):
    try:
        if os.path.exists(filename):
            with open(filename, "r", encoding="utf-8") as f:
                return f.read().strip()
    except Exception:
        pass
    return None

def is_key_pressed(vk_code):
    if vk_code is None:
        return False
    return win32api.GetAsyncKeyState(vk_code) & 0x8000 != 0

def simulate_key_press(vk_code):
    if vk_code is None:
        return
    # Press and release with a small delay
    win32api.keybd_event(vk_code, 0, 0, 0)
    time.sleep(0.05)  # Increased delay for more reliable key press
    win32api.keybd_event(vk_code, 0, win32con.KEYEVENTF_KEYUP, 0)
    time.sleep(0.05)  # Added delay after release

def write_custombind_cfg(line):
    try:
        with open(CUSTOMBIND_CFG_PATH, "w", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception as e:
        print(f"Error writing to custombind.cfg: {e}")

def handle_bind(bind_file, f_key, key_name):
    try:
        bind = read_bind_file(bind_file)
        if not bind:
            return

        vk_code = get_vk_code(bind)
        if vk_code is None:
            print(f"Invalid key code for {key_name}: {bind}")
            return

        current_state = is_key_pressed(vk_code)
        previous_state = key_states.get(key_name, False)
        
        # Only trigger on key press, not hold
        if current_state and not previous_state:
            simulate_key_press(f_key)
            time.sleep(0.1)  # Cooldown between triggers
        
        key_states[key_name] = current_state
    except Exception as e:
        print(f"Error in handle_bind for {key_name}: {e}")

def handle_longjump_bind():
    handle_bind_with_cfg("longjump_bind.flag", VK_F24, "longjump", "+lj")

def handle_jumpthrow_bind():
    handle_bind_with_cfg("jumpthrow_bind.flag", VK_F24, "jumpthrow", "+jt")

def get_last_digit_of_player_id():
    try:
        handle = win32file.CreateFile(
            PIPE_NAME,
            win32file.GENERIC_READ | win32file.GENERIC_WRITE,
            0, None,
            win32file.OPEN_EXISTING,
            0, None)
        result, data = win32file.ReadFile(handle, 65536)
        handle.Close()
        gsi_data = json.loads(data.decode('utf-8'))
        player = gsi_data.get('player', {})
        player_id = player.get('id')
        if player_id is None:
            return '0'
        # Если id — число, берем последнюю цифру
        return str(player_id)[-1]
    except Exception as e:
        # print(f"Ошибка чтения player_id из пайпа: {e}")
        return '0'

def get_local_player_slot():
    try:
        handle = win32file.CreateFile(
            PIPE_NAME,
            win32file.GENERIC_READ | win32file.GENERIC_WRITE,
            0, None,
            win32file.OPEN_EXISTING,
            0, None)
        result, data = win32file.ReadFile(handle, 65536)
        handle.Close()
        gsi_data = json.loads(data.decode('utf-8') if isinstance(data, bytes) else data)
        player = gsi_data.get('player', {})
        slot = player.get('observer_slot')
        if slot is None:
            return '0'
        return str(slot)
    except Exception as e:
        # print(f"Ошибка чтения observer_slot из пайпа: {e}")
        return '0'

def handle_selfkick_bind():
    try:
        if not is_cs2_active():
            return
        bind = read_bind_file("selfkick_bind.flag")
        if not bind:
            return
        vk_code = get_vk_code(bind)
        if vk_code is None:
            print(f"Invalid key code for selfkick: {bind}")
            return
        current_state = is_key_pressed(vk_code)
        previous_state = key_states.get("selfkick", False)
        if current_state and not previous_state:
            # 1. status
            write_custombind_cfg("status")
            simulate_key_press(VK_F24)
            time.sleep(0.25)
            # 2. callvote kick <slot>
            slot = get_local_player_slot()
            cfg_line = f"callvote kick {slot}"
            write_custombind_cfg(cfg_line)
            simulate_key_press(VK_F24)
            time.sleep(0.1)
        key_states["selfkick"] = current_state
    except Exception as e:
        print(f"Error in handle_selfkick_bind: {e}")

def is_cs2_active():
    try:
        hwnd = win32gui.GetForegroundWindow()
        if hwnd == 0:
            return False
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        proc = psutil.Process(pid)
        exe = proc.name().lower()
        return exe == "cs2.exe"
    except Exception:
        return False

def handle_bind_with_cfg(bind_file, f_key, key_name, cfg_line):
    try:
        if not is_cs2_active():
            return
        bind = read_bind_file(bind_file)
        if not bind:
            return

        vk_code = get_vk_code(bind)
        if vk_code is None:
            print(f"Invalid key code for {key_name}: {bind}")
            return

        current_state = is_key_pressed(vk_code)
        previous_state = key_states.get(key_name, False)
        
        # Only trigger on key press, not hold
        if current_state and not previous_state:
            write_custombind_cfg(cfg_line)
            simulate_key_press(f_key)
            time.sleep(0.1)  # Cooldown between triggers
        
        key_states[key_name] = current_state
    except Exception as e:
        print(f"Error in handle_bind_with_cfg for {key_name}: {e}")

def bind_thread():
    while True:
        try:
            # Check for longjump bind
            if os.path.exists("longjump_bind.flag"):
                handle_longjump_bind()
            
            # Check for jumpthrow bind
            if os.path.exists("jumpthrow_bind.flag"):
                handle_jumpthrow_bind()
            
            # Check for selfkick bind
            if os.path.exists("selfkick_bind.flag"):
                handle_selfkick_bind()
            
            time.sleep(0.01)  # Small delay to prevent high CPU usage
        except Exception as e:
            print(f"Error in bind thread: {e}")
            time.sleep(1)  # Longer delay on error

# Start the bind thread
Thread(target=bind_thread, daemon=True).start()

if __name__ == "__main__":
    # Keep the script running
    while True:
        time.sleep(1)
