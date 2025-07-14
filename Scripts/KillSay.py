import win32api
import win32con
import win32pipe
import win32file
import json
import threading
import time
import win32gui
import win32process

# Constants
PIPE_NAME = r'\\.\pipe\gsi_pipe'
CS2_WINDOW_NAME = "Counter-Strike 2"

def is_cs2_window_active():
    """Check if CS2 window is active"""
    hwnd = win32gui.GetForegroundWindow()
    if hwnd:
        _, process_id = win32process.GetWindowThreadProcessId(hwnd)
        window_title = win32gui.GetWindowText(hwnd)
        return CS2_WINDOW_NAME in window_title
    return False

def simulate_f23_press():
    """Simulate F23 key press"""
    if is_cs2_window_active():
        # F23 virtual key code is 0x86
        win32api.keybd_event(0x86, 0, 0, 0)  # Key down
        time.sleep(0.05)  # Small delay
        win32api.keybd_event(0x86, 0, win32con.KEYEVENTF_KEYUP, 0)  # Key up

def monitor_kills():
    """Monitor kills through GSI pipe"""
    old_kills = None
    while True:
        try:
            handle = win32file.CreateFile(
                PIPE_NAME,
                win32file.GENERIC_READ,
                0, None,
                win32file.OPEN_EXISTING,
                0, None
            )
            try:
                result, data = win32file.ReadFile(handle, 65536)
                if isinstance(data, bytes):
                    gsi_data = json.loads(data.decode('utf-8'))
                else:
                    gsi_data = json.loads(data)
                current_kills = gsi_data.get('player', {}).get('match_stats', {}).get('kills', 0)
                # reset old_kills if match restarted (kills уменьшились)
                if old_kills is None or current_kills < old_kills:
                    old_kills = current_kills
                elif current_kills > old_kills:
                    simulate_f23_press()
                    old_kills = current_kills
            except Exception as e:
                print(f"[KillSay] Ошибка чтения пайпа: {e}")
                time.sleep(0.2)
            finally:
                try:
                    handle.Close()
                except Exception:
                    pass
        except Exception:
            # Если пайп не найден — ждем и пробуем снова
            time.sleep(0.5)
        time.sleep(0.03)

if __name__ == "__main__":
    print("KillSay script started. Monitoring kills...")
    monitor_kills()
