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
from PySide6.QtGui import QPainter, QColor, QPen
from PySide6.QtCore import Qt, QTimer
from rgb_utils import synced_rgb
from steam_path_utils import find_csgo_cfg_path, find_csgo_log_path  # type: ignore

# Отключаем High DPI Scaling
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"

QApplication.setAttribute(Qt.ApplicationAttribute.AA_DisableHighDpiScaling)

TARGET_FILENAME = "cs2_user_convars_0_slot0.vcfg"
CROSSHAIR_PATTERN = re.compile(r'"(cl_crosshair[\w_]*)"\s+"([^"]+)"')

PIPE_NAME = r'\\.\pipe\gsi_pipe'
SNIPER_WEAPONS = {"weapon_awp", "weapon_ssg08", "weapon_scar20", "weapon_g3sg1"}

cfg_dir = find_csgo_cfg_path()
if not cfg_dir:
    print('[ОШИБКА]: Папка cfg не найдена. Проверьте путь установки Steam и CS:GO.')
    exit(1)

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

def is_cs2_window_active():
    try:
        hwnd = win32gui.GetForegroundWindow()
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        p = psutil.Process(pid)
        return p.name().lower() == "cs2.exe"
    except Exception:
        return False

def is_black_bar_on_sides():
    if not is_cs2_window_active():
        return False
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        width = monitor['width']
        height = monitor['height']
        bar_width = 3
        bar_height = 40  # чуть больше для надёжности
        center_y = height // 2 - bar_height // 2
        # Левая полоса
        left_bbox = {'left': 0, 'top': center_y, 'width': bar_width, 'height': bar_height}
        # Правая полоса
        right_bbox = {'left': width - bar_width, 'top': center_y, 'width': bar_width, 'height': bar_height}
        left_img = np.array(sct.grab(left_bbox))
        right_img = np.array(sct.grab(right_bbox))
        # Проверяем, что обе полосы действительно чёрные
        left_black = np.all(left_img[..., :3] < 16)
        right_black = np.all(right_img[..., :3] < 16)
        return left_black and right_black

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
        
        # Обрабатываем данные в зависимости от типа
        if isinstance(data, bytes):
            gsi_data = json.loads(data.decode('utf-8'))
        else:
            gsi_data = json.loads(data)
            
        weapons = gsi_data.get("player", {}).get("weapons", {})
        for weapon in weapons.values():
            if weapon.get("state") == "active":
                return weapon.get("name")
    except Exception as e:
        # Можно раскомментировать для отладки:
        # print(f"Pipe read error: {e}")
        return None
    return None

def is_cursor_in_cs2_window_and_offcenter():
    # Проверяет, находится ли курсор внутри окна CS2 и не по центру (±3px)
    try:
        hwnd = win32gui.GetForegroundWindow()
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        p = psutil.Process(pid)
        if p.name().lower() != "cs2.exe":
            return False
        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
        cursor_x, cursor_y = win32gui.GetCursorPos()
        if not (left <= cursor_x < right and top <= cursor_y < bottom):
            return False
        center_x = (left + right) // 2
        center_y = (top + bottom) // 2
        # Если курсор смещён от центра больше чем на 3 пикселя — считаем, что он "активен"
        return abs(cursor_x - center_x) > 3 or abs(cursor_y - center_y) > 3
    except Exception:
        return False

class CrosshairOverlay(QWidget):
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
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self.setStyleSheet("background: transparent;")
        self.showFullScreen()
        self.config = get_crosshair_config()
        self.last_visibility_state = False
        self.last_blackbar_state = False
        self.last_sniper_state = False

        # Удаляем подключение к shared_memory
        # self.shm = shared_memory.SharedMemory(name='sniper_weapon_state')
        # self.weapon_state = np.ndarray((1,), dtype=np.bool_, buffer=self.shm.buf)
        self.weapon_state = None  # Больше не используется

        # Reduced timer frequency for better stability
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_config)
        self.timer.start(100)  # Обновление конфига каждые 100мс

        self.repaint_timer = QTimer()
        self.repaint_timer.timeout.connect(self.update)
        self.repaint_timer.start(7)  # ~144 FPS (1000/144 ≈ 6.94мс)

        self.visibility_timer = QTimer()
        self.visibility_timer.timeout.connect(self.update_visibility)
        self.visibility_timer.start(7)  # Синхронизировано с частотой перерисовки

        self.blackbar_timer = QTimer()
        self.blackbar_timer.timeout.connect(self.update_blackbar)
        self.blackbar_timer.start(100)  # Проверка черной полосы каждые 100мс
        self.blackbar_hidden = False

        self.sniper_check_timer = QTimer()
        self.sniper_check_timer.timeout.connect(self.check_sniper_active)
        self.sniper_check_timer.start(7)  # Проверять раз в 30 мс

        self.sniper_active = False

    def update_blackbar(self):
        try:
            prev = self.blackbar_hidden
            if is_cs2_window_active():
                self.blackbar_hidden = is_black_bar_on_sides()
            else:
                self.blackbar_hidden = False
            if self.blackbar_hidden != prev:
                self.update()
        except Exception as e:
            print(f"Error in update_blackbar: {e}")

    def update_visibility(self):
        try:
            should_be_visible = is_cs2_window_active() and self.sniper_active
            if should_be_visible:
                if not self.isVisible():
                    self.showFullScreen()
            else:
                if self.isVisible():
                    self.hide()
                self.last_sniper_state = False
            self.last_visibility_state = should_be_visible
        except Exception as e:
            print(f"Error in update_visibility: {e}")

    def update_config(self):
        try:
            new_config = get_crosshair_config()
            if new_config:
                self.config = new_config
                self.update()
        except Exception as e:
            print(f"Error in update_config: {e}")

    def paintEvent(self, event):
        try:
            if not self.config or self.blackbar_hidden:
                return
            # Не рисуем прицел, если курсор находится внутри окна CS2 и не по центру
            if is_cursor_in_cs2_window_and_offcenter():
                return
                
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
            
            width = self.width()
            height = self.height()
            center_x = width // 2
            center_y = height // 2

            y_scale = height / 480
            size = self.config['size'] * y_scale
            thickness = max(1, round(self.config['thickness'] * y_scale))
            gap = 4.0 + self.config['gap']
            outline = self.config.get('drawoutline', 0)
            outline_thickness = self.config.get('outlinethickness', 1)
            
            # Calculate stroke offset and thickness based on outline_thickness
            if outline and outline_thickness < 1.0:
                stroke_offset_x = -0.5
                stroke_offset_y = -0.5
                flThick = 0.5
            else:
                stroke_offset_x = 0
                stroke_offset_y = 0
                flThick = outline_thickness if outline else 0

            r, g, b = get_rgb_color()
            color = QColor(r, g, b, self.config['alpha'])
            outline_color = QColor(0, 0, 0, self.config['alpha'])  # Черный контур для лучшей видимости

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

            # Рисуем правую часть прицела
            if outline and outline_thickness:
                painter.fillRect(
                    int(iInnerRight - flThick + stroke_offset_x), 
                    int(y0 - flThick + stroke_offset_y), 
                    int(iOuterRight - iInnerRight + 2 * flThick), 
                    int(y1 - y0 + 2 * flThick), 
                    outline_color
                )
            painter.fillRect(iInnerRight, y0, iOuterRight - iInnerRight, y1 - y0, color)

            # Рисуем левую часть прицела
            if outline and outline_thickness:
                painter.fillRect(
                    int(iOuterLeft - flThick + stroke_offset_x), 
                    int(y0 - flThick + stroke_offset_y), 
                    int(iInnerLeft - iOuterLeft + 2 * flThick), 
                    int(y1 - y0 + 2 * flThick), 
                    outline_color
                )
            painter.fillRect(iOuterLeft, y0, iInnerLeft - iOuterLeft, y1 - y0, color)

            # Рисуем верхнюю часть прицела (если не T-style)
            if not self.config['t_style']:
                if outline and outline_thickness:
                    painter.fillRect(
                        int(x0 - flThick + stroke_offset_x), 
                        int(iOuterTop - flThick + stroke_offset_y), 
                        int(x1 - x0 + 2 * flThick), 
                        int(iInnerTop - iOuterTop + 2 * flThick), 
                        outline_color
                    )
                painter.fillRect(x0, iOuterTop, x1 - x0, iInnerTop - iOuterTop, color)

            # Рисуем нижнюю часть прицела
            if outline and outline_thickness:
                painter.fillRect(
                    int(x0 - flThick + stroke_offset_x), 
                    int(iInnerBottom - flThick + stroke_offset_y), 
                    int(x1 - x0 + 2 * flThick), 
                    int(iOuterBottom - iInnerBottom + 2 * flThick), 
                    outline_color
                )
            painter.fillRect(x0, iInnerBottom, x1 - x0, iOuterBottom - iInnerBottom, color)

            # Рисуем точку в центре (если включена)
            if self.config['dot']:
                dot_size = max(1, iBarThickness)  # Размер точки равен толщине линии
                dot_x0 = center_x - dot_size // 2
                dot_y0 = center_y - dot_size // 2
                if outline and outline_thickness:
                    painter.fillRect(
                        int(dot_x0 - flThick + stroke_offset_x), 
                        int(dot_y0 - flThick + stroke_offset_y), 
                        int(dot_size + 2 * flThick), 
                        int(dot_size + 2 * flThick), 
                        outline_color
                    )
                painter.fillRect(dot_x0, dot_y0, dot_size, dot_size, color)
                
        except Exception as e:
            print(f"Error in paintEvent: {e}")

    def closeEvent(self, event):
        # Больше не требуется очистка shared_memory
        super().closeEvent(event)

    def check_sniper_active(self):
        active_weapon = get_active_weapon_from_pipe()
        self.sniper_active = active_weapon in SNIPER_WEAPONS if active_weapon else False

if __name__ == "__main__":
    app = QApplication(sys.argv)
    overlay = CrosshairOverlay()
    overlay.show()
    sys.exit(app.exec())