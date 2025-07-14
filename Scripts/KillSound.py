import win32api
import win32con
import win32pipe
import win32file
import json
import threading
import time
import win32gui
import win32process
import pygame

# Constants
PIPE_NAME = r'\\.\pipe\gsi_pipe'
CS2_WINDOW_NAME = "Counter-Strike 2"
KILLSOUND_PATH_FLAG = 'killsound_path.flag'
KILLSOUND_VOLUME_FLAG = 'killsound_volume.flag'

pygame.mixer.init()

def is_cs2_window_active():
    """Check if CS2 window is active"""
    hwnd = win32gui.GetForegroundWindow()
    if hwnd:
        _, process_id = win32process.GetWindowThreadProcessId(hwnd)
        window_title = win32gui.GetWindowText(hwnd)
        return CS2_WINDOW_NAME in window_title
    return False

def play_kill_sound():
    try:
        with open(KILLSOUND_PATH_FLAG, 'r', encoding='utf-8') as f:
            sound_path = f.read().strip()
        with open(KILLSOUND_VOLUME_FLAG, 'r', encoding='utf-8') as f:
            try:
                volume = float(f.read().strip())
            except Exception:
                volume = 1.0
        if sound_path:
            pygame.mixer.music.load(sound_path)
            pygame.mixer.music.set_volume(volume)
            pygame.mixer.music.play()
    except Exception as e:
        print(f"[KillSound] Ошибка воспроизведения звука: {e}")

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
                    play_kill_sound()
                    old_kills = current_kills
            except Exception as e:
                print(f"[KillSound] Ошибка чтения пайпа: {e}")
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
