import os
import re
import sys
import time
import win32api
import win32con
import win32gui
import win32process
import psutil
import mss
import numpy as np
import colorsys
import string
import win32file
import json
from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtGui import QPainter, QColor
from PySide6.QtCore import Qt, QTimer
from rgb_utils import synced_rgb
from steam_path_utils import find_csgo_cfg_path, find_csgo_log_path

# Отключаем High DPI Scaling
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"
QApplication.setAttribute(Qt.ApplicationAttribute.AA_DisableHighDpiScaling)

cfg_dir = find_csgo_cfg_path()
if not cfg_dir:
    print('[ОШИБКА]: Папка cfg не найдена. Проверьте путь установки Steam и CS:GO.')
    exit(1)
log_path = find_csgo_log_path()
if not log_path:
    print('[ОШИБКА]: Файл console.log не найден. Проверьте путь установки Steam и CS:GO.')
    exit(1)
CONFIG_PATH = os.path.join(cfg_dir, 'pyscripts8.cfg')
VK_F20 = 0x83  # Virtual key code for F20
TARGET_FILENAME = "cs2_user_convars_0_slot0.vcfg"
CROSSHAIR_PATTERN = re.compile(r'"(cl_crosshair[\w_]*)"\s+"([^"]+)"')
PIPE_NAME = r'\\.\pipe\gsi_pipe'
SNIPER_WEAPONS = {"weapon_awp", "weapon_ssg08", "weapon_scar20", "weapon_g3sg1"}

def is_rgb_enabled():
    try:
        with open("rgb_enabled.flag", "r") as f:
            return f.read().strip() == "1"
    except FileNotFoundError:
        return False

def get_rgb_color():
    if is_rgb_enabled():
        return synced_rgb()
    else:
        config = get_crosshair_config()
        if config:
            return config['color_r'], config['color_g'], config['color_b']
        else:
            return (0, 0, 0)  # fallback цвет, если конфиг не найден

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
    except Exception as e:
        # Можно раскомментировать для отладки:
        # print(f"Pipe read error: {e}")
        return None
    return None

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

def read_crosshair_settings(path):
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    return dict(CROSSHAIR_PATTERN.findall(content))

def str_to_bool(s):
    return s.lower() in ['true', '1', 'yes']

def get_crosshair_config():
    latest_file = find_latest_convars_file()
    if not latest_file:
        print("❌ Файл настроек прицела не найден.")
        return None
    settings = read_crosshair_settings(latest_file)
    if not settings:
        print("❌ Настройки прицела не найдены в файле.")
        return None

    use_alpha = int(str_to_bool(settings.get('cl_crosshairusealpha', '0')))
    raw_alpha = int(settings.get('cl_crosshairalpha', 255))
    alpha = raw_alpha if use_alpha else 255

    config = {
        'size': float(settings.get('cl_crosshairsize', 5)),
        'thickness': float(settings.get('cl_crosshairthickness', 1)),
        'gap': float(settings.get('cl_crosshairgap', 1)),
        'dot': int(str_to_bool(settings.get('cl_crosshairdot', '0'))),
        't_style': int(str_to_bool(settings.get('cl_crosshair_t', '0'))),
        'color_r': int(settings.get('cl_crosshaircolor_r', 255)),
        'color_g': int(settings.get('cl_crosshaircolor_g', 255)),
        'color_b': int(settings.get('cl_crosshaircolor_b', 255)),
        'alpha': alpha,
        'scale': int(settings.get('cl_crosshairscale', 1)),
        'drawoutline': int(str_to_bool(settings.get('cl_crosshair_drawoutline', '0'))),
        'outlinethickness': float(settings.get('cl_crosshair_outlinethickness', 1)),
    }

    return config

def press_f20():
    win32api.keybd_event(VK_F20, 0, 0, 0)
    win32api.keybd_event(VK_F20, 0, win32con.KEYEVENTF_KEYUP, 0)

def write_config(commands):
    try:
        with open(CONFIG_PATH, 'w') as f:
            f.write('\n'.join(commands))
        press_f20()  # Отправляем F20 после каждой записи
    except Exception as e:
        print(f"Error writing config: {e}")

def is_cs2_window_active():
    try:
        hwnd = win32gui.GetForegroundWindow()
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        p = psutil.Process(pid)
        return p.name().lower() == "cs2.exe"
    except Exception:
        return False

def is_cursor_active():
    try:
        pt = win32gui.GetCursorPos()
        hwnd = win32gui.GetForegroundWindow()
        rect = win32gui.GetWindowRect(hwnd)
        width = rect[2] - rect[0]
        height = rect[3] - rect[1]
        center_x = rect[0] + width // 2
        center_y = rect[1] + height // 2
        return abs(pt[0] - center_x) > 5 or abs(pt[1] - center_y) > 5
    except Exception:
        return False

class RecoilCrosshairOverlay(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool |
            Qt.WindowType.WindowTransparentForInput |
            Qt.WindowType.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setStyleSheet("background: transparent;")
        self.showFullScreen()

        # Таймеры
        self.repaint_timer = QTimer()
        self.repaint_timer.timeout.connect(self.update)
        self.repaint_timer.start(16)  # ~60 FPS для более стабильной отрисовки

        self.visibility_timer = QTimer()
        self.visibility_timer.timeout.connect(self.update_visibility)
        self.visibility_timer.start(16)  # Синхронизируем с частотой отрисовки

        self.config_timer = QTimer()
        self.config_timer.timeout.connect(self.update_config)
        self.config_timer.start(100)  # Обновление конфига каждые 100мс

        self.weapon_check_timer = QTimer()
        self.weapon_check_timer.timeout.connect(self.check_weapon)
        self.weapon_check_timer.start(30)  # Проверка оружия каждые 30мс

        self.last_visibility_state = False
        self.is_shooting = False
        self.config = get_crosshair_config()
        self.sniper_active = False

    def check_weapon(self):
        active_weapon = get_active_weapon_from_pipe()
        self.sniper_active = active_weapon in SNIPER_WEAPONS if active_weapon else False

    def update_config(self):
        try:
            new_config = get_crosshair_config()
            if new_config:
                self.config = new_config
                self.update()
        except Exception as e:
            print(f"Error in update_config: {e}")

    def update_visibility(self):
        try:
            should_be_visible = is_cs2_window_active()
            if should_be_visible:
                if not self.isVisible():
                    self.showFullScreen()
            else:
                if self.isVisible():
                    self.hide()
            self.last_visibility_state = should_be_visible
        except Exception as e:
            print(f"Error in update_visibility: {e}")

    def paintEvent(self, event):
        try:
            if not is_cs2_window_active() or not self.config or is_cursor_active():
                return

            # Проверяем состояние стрельбы
            is_shooting = win32api.GetAsyncKeyState(win32con.VK_LBUTTON) & 0x8000
            if is_shooting != self.is_shooting:
                self.is_shooting = is_shooting
                if is_shooting:
                    # При начале стрельбы включаем прицел с отдачей
                    write_config(["cl_crosshair_recoil 1"])
                else:
                    # При окончании стрельбы выключаем прицел с отдачей
                    write_config(["cl_crosshair_recoil 0"])

            # Сначала проверяем снайперку, потом стрельбу
            if self.sniper_active:
                return
            if not is_shooting:
                return

            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
            width = self.width()
            height = self.height()
            center_x = width // 2
            center_y = height // 2

            # Отрисовка прицела
            y_scale = height / 480
            size = self.config['size'] * y_scale
            thickness = max(1, round(self.config['thickness'] * y_scale))
            gap = 4.0 + self.config['gap']
            outline = self.config.get('drawoutline', 0)
            outline_thickness = self.config.get('outlinethickness', 1)

            # Получаем RGB цвет из rgb_utils
            r, g, b = get_rgb_color()
            color = QColor(r, g, b, self.config['alpha'])
            outline_color = QColor(0, 0, 0, self.config['alpha'])

            iBarSize = int(round(size))
            iBarThickness = thickness
            iInnerCrossDistance = int(gap)
            iInnerLeft = center_x - iInnerCrossDistance - iBarThickness // 2
            iInnerRight = iInnerLeft + 2 * iInnerCrossDistance + iBarThickness
            iOuterLeft = iInnerLeft - iBarSize
            iOuterRight = iInnerRight + iBarSize
            y0 = center_y - iBarThickness // 2
            y1 = y0 + iBarThickness

            iInnerTop = center_y - iInnerCrossDistance - iBarThickness // 2
            iInnerBottom = iInnerTop + 2 * iInnerCrossDistance + iBarThickness
            iOuterTop = iInnerTop - iBarSize
            iOuterBottom = iInnerBottom + iBarSize
            x0 = center_x - iBarThickness // 2
            x1 = x0 + iBarThickness

            # Отрисовка линий прицела
            if outline and outline_thickness:
                painter.fillRect(
                    int(iInnerRight - outline_thickness), 
                    int(y0 - outline_thickness), 
                    int(iOuterRight - iInnerRight + 2 * outline_thickness), 
                    int(y1 - y0 + 2 * outline_thickness), 
                    outline_color
                )
            painter.fillRect(iInnerRight, y0, iOuterRight - iInnerRight, y1 - y0, color)

            if outline and outline_thickness:
                painter.fillRect(
                    int(iOuterLeft - outline_thickness), 
                    int(y0 - outline_thickness),
                    int(iInnerLeft - iOuterLeft + 2 * outline_thickness),
                    int(y1 - y0 + 2 * outline_thickness), 
                    outline_color
                )
            painter.fillRect(iOuterLeft, y0, iInnerLeft - iOuterLeft, y1 - y0, color)

            if not self.config['t_style']:
                if outline and outline_thickness:
                    painter.fillRect(
                        int(x0 - outline_thickness), 
                        int(iOuterTop - outline_thickness),
                        int(x1 - x0 + 2 * outline_thickness),
                        int(iInnerTop - iOuterTop + 2 * outline_thickness), 
                        outline_color
                    )
                painter.fillRect(x0, iOuterTop, x1 - x0, iInnerTop - iOuterTop, color)

            if outline and outline_thickness:
                painter.fillRect(
                    int(x0 - outline_thickness), 
                    int(iInnerBottom - outline_thickness),
                    int(x1 - x0 + 2 * outline_thickness),
                    int(iOuterBottom - iInnerBottom + 2 * outline_thickness), 
                    outline_color
                )
            painter.fillRect(x0, iInnerBottom, x1 - x0, iOuterBottom - iInnerBottom, color)

            # Отрисовка точки в центре
            if self.config['dot']:
                dot_x0 = center_x - iBarThickness // 2
                dot_y0 = center_y - iBarThickness // 2
                if outline and outline_thickness:
                    painter.fillRect(
                        int(dot_x0 - outline_thickness), 
                        int(dot_y0 - outline_thickness),
                        int(iBarThickness + 2 * outline_thickness),
                        int(iBarThickness + 2 * outline_thickness), 
                        outline_color
                    )
                painter.fillRect(dot_x0, dot_y0, iBarThickness, iBarThickness, color)

        except Exception as e:
            print(f"Error in paintEvent: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    overlay = RecoilCrosshairOverlay()
    overlay.show()
    sys.exit(app.exec())
