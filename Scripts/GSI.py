from flask import Flask, request
import json
import os
import platform
import threading
import win32pipe
import win32file
import pywintypes
import time
from typing import cast

app = Flask(__name__)

# Цветовые пресеты ANSI (R, G, B)
color_header = "\033[38;2;202;102;255m"     # #ca66ff (заголовки)
color_info = "\033[38;2;122;255;222m"       # #7affde (информация)
color_error = "\033[38;2;255;59;56m"        # #ff3b38
color_warning = "\033[38;2;255;249;56m"     # #fff938
color_loading = "\033[38;2;122;255;222m"    # #7affde
color_input = "\033[38;2;136;136;136m"      # #888888
color_active = "\033[38;2;65;255;40m"       # #41ff28
color_reset = "\033[0m"

def clear_console():
    if platform.system() == "Windows":
        os.system("cls")
    else:
        os.system("clear")

@app.route('/', methods=['POST'])
def gsi_listener():
    data = request.get_json()
    if not data:
        print(f"{color_error}[error] Не удалось получить JSON.{color_reset}")
        return '', 400

    # Сохраняем данные для пайпа
    global latest_data
    with pipe_lock:
        latest_data = json.dumps(data, ensure_ascii=False)

    clear_console()
    print(f"{color_loading}New GSI packet received{color_reset}")

    # Provider
    provider = data.get('provider', {})
    print(f"\n{color_header}Provider:{color_reset}")
    print(f"{color_info}  name: {provider.get('name', 'N/A')}")
    print(f"  appid: {provider.get('appid', 'N/A')}")
    print(f"  version: {provider.get('version', 'N/A')}{color_reset}")

    # Map
    map_info = data.get('map', {})
    round_info = data.get('round', {})
    print(f"\n{color_header}Map:{color_reset}")
    print(f"{color_info}  name: {map_info.get('name', 'N/A')}")
    print(f"  mode: {map_info.get('mode', 'N/A')}")
    print(f"  round: {map_info.get('round', 'N/A')}")
    print(f"  team scores: CT={map_info.get('team_ct', {}).get('score', 'N/A')} | T={map_info.get('team_t', {}).get('score', 'N/A')}{color_reset}")

    # Bomb Status
    bomb_status = round_info.get('bomb', None)
    print(f"\n{color_header}Bomb Status:{color_reset}")
    
    if bomb_status == 'planted':
        print(f"{color_active}  Bomb planted!{color_reset}")
    elif bomb_status == 'defusing':
        print(f"{color_warning}  Bomb defusing!{color_reset}")
    elif bomb_status == 'exploded':
        print(f"{color_error}  Bomb exploded!{color_reset}")
    elif bomb_status == 'defused':
        print(f"{color_active}  Bomb successfully defused.{color_reset}")
    elif bomb_status:
        print(f"{color_info}  Bomb state: {bomb_status}{color_reset}")
    else:
        print(f"{color_error}  Bomb not active.{color_reset}")

    # Player
    player = data.get('player', {})
    state = player.get('state', {})
    print(f"\n{color_header}Player:{color_reset}")
    print(f"{color_info}  name: {player.get('name', 'N/A')}")
    print(f"  team: {player.get('team', 'N/A')}")
    print(f"  steamid: {player.get('steamid', 'N/A')}")
    print(f"  health: {state.get('health', 'N/A')} | armor: {state.get('armor', 'N/A')} | helmet: {state.get('helmet', False)}{color_reset}")

    # Weapons
    weapons = player.get('weapons', {})
    active_weapon = None

    print(f"\n{color_header}Weapons:{color_reset}")
    if weapons:
        for weapon_info in weapons.values():
            weapon_name = weapon_info.get('name', 'unknown')
            state_str = weapon_info.get('state', 'holstered')

            if state_str == 'active':
                active_weapon = weapon_name
                print(f"{color_active}  > {weapon_name:<25} [state: {state_str}]{color_reset}")
            else:
                print(f"{color_error}  > {weapon_name:<25} [state: {state_str}]{color_reset}")
    else:
        print(f"{color_warning}  [warn] No weapon information.{color_reset}")

    if active_weapon:
        print(f"{color_info}\n[info] Active weapon: {active_weapon}{color_reset}")
    else:
        print(f"{color_warning}\n[warn] Could not determine active weapon.{color_reset}")

    return '', 200

PIPE_NAME = r'\\.\pipe\gsi_pipe'
latest_data = None
pipe_lock = threading.Lock()

def pipe_server():
    global latest_data
    while True:
        try:
            # Создаем именованный пайп
            pipe = win32pipe.CreateNamedPipe(
                PIPE_NAME,
                win32pipe.PIPE_ACCESS_DUPLEX,
                win32pipe.PIPE_TYPE_MESSAGE | win32pipe.PIPE_READMODE_MESSAGE | win32pipe.PIPE_WAIT,
                1, 65536, 65536, 0, None)
            
            # print(f"{color_info}[pipe] Waiting for client connection...{color_reset}")
            
            win32pipe.ConnectNamedPipe(pipe, None)
            # print(f"{color_active}[pipe] Client connected{color_reset}")
            
            with pipe_lock:
                if latest_data:
                    try:
                        win32file.WriteFile(pipe, latest_data.encode('utf-8'))
                        # print(f"{color_info}[pipe] Data sent to client{color_reset}")
                    except Exception as e:
                        print(f"{color_error}[pipe] Error sending data: {e}{color_reset}")
                else:
                    # print(f"{color_warning}[pipe] No data to send{color_reset}")
                    pass
            
            win32file.CloseHandle(pipe)
            # print(f"{color_info}[pipe] Client disconnected{color_reset}")
            
        except pywintypes.error as e:
            if e.winerror == 232:  # ERROR_BROKEN_PIPE
                print(f"{color_warning}[pipe] Client disconnected unexpectedly{color_reset}")
            elif e.winerror == 535:  # ERROR_PIPE_CONNECTED
                print(f"{color_info}[pipe] Client already connected{color_reset}")
            else:
                print(f"{color_error}[pipe] Pipe error: {e}{color_reset}")
            time.sleep(0.1)
        except Exception as e:
            print(f"{color_error}[pipe] Unexpected error: {e}{color_reset}")
            time.sleep(1)

# Запускаем сервер пайпа в отдельном потоке
threading.Thread(target=pipe_server, daemon=True).start()

if __name__ == '__main__':
    print(f"{color_loading}GSI server started: http://localhost:3000/{color_reset}")
    app.run(host='0.0.0.0', port=3000)
