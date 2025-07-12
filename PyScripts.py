import subprocess
import sys
import os

# --- BEAUTIFUL CONSOLE OUTPUT ---
def print_welcome():
    PURPLE = "\033[38;2;202;101;255m"
    CYAN = "\033[38;2;113;255;219m"
    RESET = "\033[0m"
    print(PURPLE + r"""
 ██▓███  ▓██   ██▓  ██████  ▄████▄   ██▀███   ██▓ ██▓███  ▄▄▄█████▓  ██████ 
▓██░  ██▒ ▒██  ██▒▒██    ▒ ▒██▀ ▀█  ▓██ ▒ ██▒▓██▒▓██░  ██▒▓  ██▒ ▓▒▒██    ▒ 
▓██░ ██▓▒  ▒██ ██░░ ▓██▄   ▒▓█    ▄ ▓██ ░▄█ ▒▒██▒▓██░ ██▓▒▒ ▓██░ ▒░░ ▓██▄   
▒██▄█▓▒ ▒  ░ ▐██▓░  ▒   ██▒▒▓▓▄ ▄██▒▒██▀▀█▄  ░██░▒██▄█▓▒ ▒░ ▓██▓ ░   ▒   ██▒
▒██▒ ░  ░  ░ ██▒▓░▒██████▒▒▒ ▓███▀ ░░██▓ ▒██▒░██░▒██▒ ░  ░  ▒██▒ ░ ▒██████▒▒
▒▓▒░ ░  ░   ██▒▒▒ ▒ ▒▓▒ ▒ ░░ ░▒ ▒  ░░ ▒▓ ░▒▓░░▓  ▒▓▒░ ░  ░  ▒ ░░   ▒ ▒▓▒ ▒ ░
░▒ ░      ▓██ ░▒░ ░ ░▒  ░ ░  ░  ▒     ░▒ ░ ▒░ ▒ ░░▒ ░         ░    ░ ░▒  ░ ░
░░        ▒ ▒ ░░  ░  ░  ░  ░          ░░   ░  ▒ ░░░         ░      ░  ░  ░  
          ░ ░           ░  ░ ░         ░      ░                          ░  
          ░ ░              ░                                                

✦ PyScripts Tweaks for CS2 〜（ゝ。∂）

- Quality of life scripts for CS2
- Custom binds, visuals, automation, and more!
- Free, open, and friendly for everyone
""" + RESET)
    print(CYAN + r"""
✦ Support development with a skin donation 〜（ゝ。∂）
✦ Trade link: https://steamcommunity.com/tradeoffer/new/?partner=1570577878&token=1WuPKdBZ
""" + RESET)
    print(CYAN + r"""
✦ Поддержите разработку скином 〜（ゝ。∂）
✦ Ссылка для обмена: https://steamcommunity.com/tradeoffer/new/?partner=1570577878&token=1WuPKdBZ
""" + RESET)

if __name__ == "__main__":
    print_welcome()
    scripts_dir = os.path.join(os.path.dirname(__file__), "Scripts")
    script_path = os.path.join(scripts_dir, "Menu.py")
    old_cwd = os.getcwd()
    try:
        os.chdir(scripts_dir)
        creationflags = 0
        if sys.platform == "win32":
            creationflags = subprocess.CREATE_NO_WINDOW
        subprocess.run([sys.executable, script_path], creationflags=creationflags)
    finally:
        os.chdir(old_cwd)
