import os

# Имя файла и относительный путь к папке cfg
CFG_RELATIVE_PATH = os.path.join('steamapps', 'common', 'Counter-Strike Global Offensive', 'game', 'csgo', 'cfg')

# Получаем переменные окружения
username = os.environ.get('USERNAME', '')
localappdata = os.environ.get('LOCALAPPDATA', f'C:\\Users\\{username}\\AppData\\Local')

# Возможные корни для Steam
possible_roots = [
    os.environ.get('PROGRAMFILES(X86)', 'C:\\Program Files (x86)'),
    os.environ.get('PROGRAMFILES', 'C:\\Program Files'),
    localappdata,
    'C:\\', 'D:\\', 'E:\\', 'F:\\'
]

pyscripts0_content = '''bind scancode104 exec pyscripts1
bind scancode105 exec pyscripts2
bind scancode106 exec pyscripts3
bind scancode107 exec pyscripts4
bind scancode108 exec pyscripts5
bind scancode109 exec pyscripts6
bind scancode110 exec pyscripts7
bind scancode111 exec pyscripts8
bind scancode112 exec pyscripts9
bind scancode113 exec pyscripts10
bind scancode114 exec pyscripts11
bind scancode115 exec pyscripts12
echoln [*] PyScripts Bind Initalization

// post-patch movement config by ruby rain (steamcommunity.com/id/r_by)
// should last about 12 hours, make sure to re-exec while in lobby once it stops working!!

//LOGIC (DON'T TOUCH)==============================
alias reset_t_2 "alias t_2"
alias reset_t "alias t t_2"
reset_t_2
reset_t
alias +jt "alias t_2 +jt_t"
alias -jt "alias t_2 -jt_t"
alias +wjt "alias t_2 +wjt_t"
alias -wjt "alias t_2 -wjt_t"
alias +jt_t "reset_t_2;+jump;-jump; alias t_2 attcks"	
alias attcks "reset_t_2; -attack; -attack2"
alias -jt_t "reset_t_2;"
alias +wjt_t "reset_t_2; +forward;+jump;-jump; alias t_2 attcks"
alias attcks "reset_t_2; -attack; -attack2"
alias -wjt_t "reset_t_2; -forward"
sv_cheats 1
exec_async bypass/setup_async

// DONT TOUCH THIS PLEASE, WITHOUT THIS OR THIS BEING IN THE WRONG LINE MEANS EVERYTHING BREAKS
exec movement/setup
'''

pyscripts3_content = 'bind scancode106 +attack\n'
pyscripts4_content = 'alias "+auto_pistol" "attack 1 1 0"\nalias "-auto_pistol" "attack -999 1 0"\n\nbind "scancode107" "+auto_pistol"\n'
pyscripts5_content = 'alias "+xcarry" "slot1; slot1"\nalias "-xcarry" "slot1; drop"\n\nbind "scancode108" "+xcarry"\n'
pyscripts9_content = 'sys_info\n'

gsi_cfg_content = '''"Example Integration Configuration"
{
    "uri"          "http://localhost:3000/"
    "timeout"      "5.0"
    "buffer"       "0.0"
    "throttle"     "0.1"
    "heartbeat"    "10.0"
    "data"
    {
        "provider"                  "1"
        "tournamentdraft"           "1"
        "map"                       "1"
        "map_round_wins"            "1"
        "round"                     "1"
        "player_id"                 "1"
        "player_state"              "1"
        "player_weapons"            "1"
        "player_match_stats"        "1"
        "player_position"           "1"
        "phase_countdowns"          "1"
        "allplayers_id"             "1"
        "allplayers_state"          "1"
        "allplayers_match_stats"    "1"
        "allplayers_weapons"        "1"
        "allplayers_position"       "1"
        "allgrenades"               "1"
        "bomb"                      "1"
    }
}
'''

steam_dirs = []
for root in possible_roots:
    steam_path = os.path.join(root, 'Steam')
    if os.path.isdir(steam_path):
        steam_dirs.append(steam_path)

found = False
for steam_dir in steam_dirs:
    cfg_path = os.path.join(steam_dir, CFG_RELATIVE_PATH)
    if os.path.isdir(cfg_path):
        for i in range(13):
            file_name = f'pyscripts{i}.cfg'
            file_path = os.path.join(cfg_path, file_name)
            if i == 0:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(pyscripts0_content)
            elif i == 3:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(pyscripts3_content)
            elif i == 4:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(pyscripts4_content)
            elif i == 5:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(pyscripts5_content)
            elif i == 9:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(pyscripts9_content)
            else:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(f'// {file_name} created automatically\n')
        # Создаем gamestate_integration_gsi.cfg
        gsi_file_path = os.path.join(cfg_path, 'gamestate_integration_gsi.cfg')
        with open(gsi_file_path, 'w', encoding='utf-8') as f:
            f.write(gsi_cfg_content)
        found = True
        break

if not found:
    print('Папка cfg не найдена. Проверьте путь установки Steam и CS:GO.')
