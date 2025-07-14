import time
import win32api
import win32con
import win32gui
import win32process
import psutil
import win32file
import json
import os
import re
import string

VK_F18 = 0x81  # Виртуальный код клавиши F18

PIPE_NAME = r'\\.\pipe\gsi_pipe'
KNIFE_WEAPONS = {
    "weapon_knife",
    "weapon_knife_t",
    "weapon_bayonet",
    "weapon_knife_css",
    "weapon_knife_ursus",
    "weapon_knife_gypsy_jackknife",   # Navaja
    "weapon_knife_outdoor",           # Survival
    "weapon_knife_canis",
    "weapon_knife_cord",
    "weapon_knife_skeleton",
    "weapon_knife_stiletto",
    "weapon_knife_widowmaker",        # Talon
    "weapon_knife_falchion",
    "weapon_knife_push",              # Shadow Daggers
    "weapon_knife_butterfly",
    "weapon_knife_flip",
    "weapon_knife_gut",
    "weapon_knife_karambit",
    "weapon_knife_m9_bayonet",
    "weapon_knife_tactical",          # Huntsman
    "weapon_knife_survival_bowie",    # Bowie
    "weapon_knife_karambit_gold",     # Gold Karambit (CS2)
    "weapon_knife_bayonet_gold",      # Gold Bayonet (CS2)
    "weapon_knife_kukri",             # Kukri (CS2)
    "weapon_knife_paracord",
    "weapon_knife_nomad",
    "weapon_knife_skeleton",
    "weapon_knife_outdoor",
    "weapon_knife_canis",
    "weapon_knife_cord",
    "weapon_knife_ursus",
    "weapon_knife_stiletto",
    "weapon_knife_widowmaker",
    "weapon_knife_falchion",
    "weapon_knife_push",
    "weapon_knife_butterfly",
    "weapon_knife_flip",
    "weapon_knife_gut",
    "weapon_knife_m9_bayonet",
    "weapon_knife_tactical",
    "weapon_knife_survival_bowie"
}

TARGET_FILENAME = "cs2_user_convars_0_slot0.vcfg"
PREF_LEFT_PATTERN = re.compile(r'"cl_prefer_lefthanded"\s+"([^"]+)"')

def get_steam_userdata_path():
    # Получаем переменные окружения
    username = os.environ.get('USERNAME', '')
    localappdata = os.environ.get('LOCALAPPDATA', f'C:\\Users\\{username}\\AppData\\Local')

    # Возможные корни для Steam (как в Create.py)
    possible_roots = [
        os.environ.get('PROGRAMFILES(X86)', 'C:\\Program Files (x86)'),
        os.environ.get('PROGRAMFILES', 'C:\\Program Files'),
        localappdata,
        'C:\\', 'D:\\', 'E:\\', 'F:\\'
    ]

    for root in possible_roots:
        steam_path = os.path.join(root, 'Steam', 'userdata')
        if os.path.exists(steam_path):
            return steam_path
    return None

def find_latest_convars_file():
    steam_userdata = get_steam_userdata_path()
    if not steam_userdata:
        print("❌ Папка Steam\\userdata не найдена ни на одном диске.")
        return None
    newest_time = None
    newest_path = None
    for root, dirs, files in os.walk(steam_userdata):
        for file in files:
            if file == TARGET_FILENAME:
                full_path = os.path.join(root, file)
                modified_time = os.path.getmtime(full_path)
                if newest_time is None or modified_time > newest_time:
                    newest_time = modified_time
                    newest_path = full_path
    return newest_path

def get_prefer_lefthanded():
    path = find_latest_convars_file()
    if not path:
        print("❌ Файл настроек не найден, используем правую руку по умолчанию.")
        return False
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    match = PREF_LEFT_PATTERN.search(content)
    if match:
        return match.group(1).strip().lower() == "true"
    return False

def press_key(vk_code):
    win32api.keybd_event(vk_code, 0, 0, 0)
    time.sleep(0.01)
    win32api.keybd_event(vk_code, 0, win32con.KEYEVENTF_KEYUP, 0)

def is_cs2_in_foreground():
    try:
        hwnd = win32gui.GetForegroundWindow()
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        p = psutil.Process(pid)
        return p.name().lower() == "cs2.exe"
    except Exception:
        return False

def get_active_weapon_from_pipe():
    try:
        handle = win32file.CreateFile(
            PIPE_NAME,
            win32file.GENERIC_READ,
            0, None,
            win32file.OPEN_EXISTING,
            0, None)
        result, data = win32file.ReadFile(handle.handle, 65536)
        handle.Close()
        # data уже является bytes, не нужно decode
        gsi_data = json.loads(data.decode('utf-8'))
        weapons = gsi_data.get("player", {}).get("weapons", {})
        for weapon in weapons.values():
            if weapon.get("state") == "active":
                return weapon.get("name")
    except Exception:
        return None
    return None

def write_knifeswitch_cfg(prefer_left):
    # Используем тот же подход поиска Steam как в Create.py
    username = os.environ.get('USERNAME', '')
    localappdata = os.environ.get('LOCALAPPDATA', f'C:\\Users\\{username}\\AppData\\Local')
    
    possible_roots = [
        os.environ.get('PROGRAMFILES(X86)', 'C:\\Program Files (x86)'),
        os.environ.get('PROGRAMFILES', 'C:\\Program Files'),
        localappdata,
        'C:\\', 'D:\\', 'E:\\', 'F:\\'
    ]
    
    cfg_path = None
    for root in possible_roots:
        steam_path = os.path.join(root, 'Steam')
        if os.path.isdir(steam_path):
            temp_cfg_path = os.path.join(steam_path, 'steamapps', 'common', 'Counter-Strike Global Offensive', 'game', 'csgo', 'cfg', 'pyscripts6.cfg')
            if os.path.exists(os.path.dirname(temp_cfg_path)):
                cfg_path = temp_cfg_path
                break
    
    if not cfg_path:
        print("❌ Не удалось найти папку cfg CS:GO")
        return
        
    command = "switchhandsright" if prefer_left else "switchhandsleft"
    try:
        with open(cfg_path, 'w', encoding='utf-8') as f:
            f.write(command + "\n")
    except Exception as e:
        print(f"Ошибка записи в knifeswitch.cfg: {e}")

print("Скрипт switchhands активен. Ожидание ножа...")

last_weapon = None
knife_active = False
prefer_left = get_prefer_lefthanded()

try:
    while True:
        if is_cs2_in_foreground():
            active_weapon = get_active_weapon_from_pipe()
            # Обновляем настройку руки при каждом цикле (на случай изменения в игре)
            prefer_left = get_prefer_lefthanded()
            # Если выбрали нож
            if active_weapon in KNIFE_WEAPONS and (last_weapon is None or last_weapon not in KNIFE_WEAPONS):
                write_knifeswitch_cfg(prefer_left)
                print(f"{active_weapon} выбран (левая рука: {prefer_left}) — нажимаю F18")
                press_key(VK_F18)
                knife_active = True
            # Если после ножа выбрали другое оружие
            elif (knife_active and active_weapon and active_weapon not in KNIFE_WEAPONS) or (active_weapon and active_weapon not in KNIFE_WEAPONS and (last_weapon is None or last_weapon in KNIFE_WEAPONS)):
                # Теперь всегда обновляем файл при смене на не-нож
                if prefer_left:
                    write_knifeswitch_cfg(False)  # switchhandsleft
                    print(f"{active_weapon} выбран после ножа или не нож (левая рука) — пишу switchhandsleft и нажимаю F18")
                    press_key(VK_F18)
                else:
                    write_knifeswitch_cfg(True)  # switchhandsright
                    print(f"{active_weapon} выбран после ножа или не нож (правая рука) — пишу switchhandsright и нажимаю F18")
                    press_key(VK_F18)
                knife_active = False
            last_weapon = active_weapon
        time.sleep(0.01)
except KeyboardInterrupt:
    print("Выход...")