import os

def find_csgo_cfg_path():
    """
    Ищет путь к папке cfg для CS:GO/CS2 во всех возможных Steam-директориях.
    Возвращает путь к папке cfg или None, если не найдено.
    """
    CFG_RELATIVE_PATH = os.path.join('steamapps', 'common', 'Counter-Strike Global Offensive', 'game', 'csgo', 'cfg')
    username = os.environ.get('USERNAME', '')
    localappdata = os.environ.get('LOCALAPPDATA', f'C:\\Users\\{username}\\AppData\\Local')
    possible_roots = [
        os.environ.get('PROGRAMFILES(X86)', 'C:\\Program Files (x86)'),
        os.environ.get('PROGRAMFILES', 'C:\\Program Files'),
        localappdata,
        'C:\\', 'D:\\', 'E:\\', 'F:\\'
    ]
    steam_dirs = []
    for root in possible_roots:
        steam_path = os.path.join(root, 'Steam')
        if os.path.isdir(steam_path):
            steam_dirs.append(steam_path)
    for steam_dir in steam_dirs:
        cfg_path = os.path.join(steam_dir, CFG_RELATIVE_PATH)
        if os.path.isdir(cfg_path):
            return cfg_path
    return None

def find_csgo_log_path():
    """
    Ищет путь к console.log для CS:GO/CS2 во всех возможных Steam-директориях.
    Возвращает путь к console.log или None, если не найдено.
    """
    LOG_RELATIVE_PATH = os.path.join('steamapps', 'common', 'Counter-Strike Global Offensive', 'game', 'csgo', 'console.log')
    username = os.environ.get('USERNAME', '')
    localappdata = os.environ.get('LOCALAPPDATA', f'C:\\Users\\{username}\\AppData\\Local')
    possible_roots = [
        os.environ.get('PROGRAMFILES(X86)', 'C:\\Program Files (x86)'),
        os.environ.get('PROGRAMFILES', 'C:\\Program Files'),
        localappdata,
        'C:\\', 'D:\\', 'E:\\', 'F:\\'
    ]
    steam_dirs = []
    for root in possible_roots:
        steam_path = os.path.join(root, 'Steam')
        if os.path.isdir(steam_path):
            steam_dirs.append(steam_path)
    for steam_dir in steam_dirs:
        log_path = os.path.join(steam_dir, LOG_RELATIVE_PATH)
        if os.path.isfile(log_path):
            return log_path
    return None 