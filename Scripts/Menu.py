import os
import sys
import time
import subprocess
import signal
import ctypes
from ctypes import windll
# Import wintypes separately to avoid AttributeError
try:
    from ctypes import wintypes
except ImportError:
    # Fallback for systems where wintypes is not available
    wintypes = None

# Устанавливаем кодировку UTF-8 для консоли Windows
if sys.platform == "win32":
    try:
        # Устанавливаем кодировку консоли в UTF-8
        os.system("chcp 65001 > nul")
        # Также устанавливаем переменную окружения
        os.environ["PYTHONIOENCODING"] = "utf-8"
    except:
        pass

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QFrame, QLineEdit, QScrollArea
)
from PyQt6.QtGui import QIcon, QFont, QPainter, QColor, QPen, QLinearGradient, QFontInfo
from PyQt6.QtCore import Qt, QSize, QTimer, QRect, QPropertyAnimation, QEasingCurve, QPoint, pyqtSignal, QVariantAnimation
from gear import GearIcon
from rgb_utils import synced_rgb, load_rgb_settings
import threading
import multiprocessing.connection
from multiprocessing.connection import Client
import colorsys
import Create  # Автоматическое создание скриптов и конфигов при запуске GUI
from steam_path_utils import find_csgo_cfg_path
# --- Font loader for Arial Greek ---
from PyQt6.QtGui import QFontDatabase

# --- High-DPI support ---
# Для Windows: включить DPI Awareness (чтобы Qt знал о масштабе системы)
if hasattr(ctypes, 'windll'):   
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)  # Per Monitor v2
    except Exception:
        pass

# Для PyQt6: включить High DPI scaling
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
os.environ["QT_SCALE_FACTOR_ROUNDING_POLICY"] = "RoundPreferFloor"
# --- End High-DPI support ---

# Win32 API constants
HWND_TOPMOST = -1
SWP_NOMOVE = 0x0002
SWP_NOSIZE = 0x0001
HWND_NOTOPMOST = -2

# Global hotkey ID
HOTKEY_ID = 1
EXIT_HOTKEY_ID = 2  # New hotkey ID for exit bind

# Процессы скриптов
r8_proc = None
sniper_proc = None
rgb_proc = None
rainbowhud_proc = None
gsi_proc = None
xcarry_proc = None
scope_anywhere_proc = None
knifeswitch_proc = None
autopistol_proc = None
bombtimer_proc = None
anglebind_proc = None
keystrokes_proc = None  # Add this near other script process globals
killsay_proc = None  # Add this line
chatspammer_proc = None  # Add this line
watermark_proc = None  # Add watermark process variable
recoilcrosshair_proc = None  # Add recoil crosshair process variable
killsound_proc = None  # Add killsound process variable
autoaccept_proc = None  # Add autoaccept process variable
anti_afk_proc = None  # Add anti afk process variable
trigger_proc = None  # Add trigger process variable
r8double_proc = None  # Add r8double process variable
autostop_proc = None  # Add autostop process variable
jumpshoot_proc = None  # Add jumpshoot process variable

rgb_enabled = False

# Global RGB color
global_rgb_color = (255, 0, 0)  # Default red color

# Menu visibility state for pipe
menu_visibility_state = "VISIBLE"

def update_global_rgb_color():
    global global_rgb_color
    global_rgb_color = synced_rgb()

def start_script(path):
    try:
        abs_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), path)
        print(f"[start_script] Запускаю: {abs_path}")
        
        # Создаем копию переменных окружения и устанавливаем UTF-8
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUTF8"] = "1"
        
        # Убираем stderr=subprocess.DEVNULL чтобы видеть ошибки
        return subprocess.Popen([sys.executable, abs_path], stdout=subprocess.DEVNULL, env=env)
    except Exception as e:
        print(f"[start_script] Ошибка запуска: {e}")
        return None

def stop_script(proc):
    if proc and proc.poll() is None:
        os.kill(proc.pid, signal.SIGTERM)

def get_vk_code(key_name):
    """Convert key name to VK code"""
    key_mapping = {
        'A': 0x41, 'B': 0x42, 'C': 0x43, 'D': 0x44, 'E': 0x45,
        'F': 0x46, 'G': 0x47, 'H': 0x48, 'I': 0x49, 'J': 0x4A,
        'K': 0x4B, 'L': 0x4C, 'M': 0x4D, 'N': 0x4E, 'O': 0x4F,
        'P': 0x50, 'Q': 0x51, 'R': 0x52, 'S': 0x53, 'T': 0x54,
        'U': 0x55, 'V': 0x56, 'W': 0x57, 'X': 0x58, 'Y': 0x59,
        'Z': 0x5A,
        'F1': 0x70, 'F2': 0x71, 'F3': 0x72, 'F4': 0x73,
        'F5': 0x74, 'F6': 0x75, 'F7': 0x76, 'F8': 0x77,
        'F9': 0x78, 'F10': 0x79, 'F11': 0x7A, 'F12': 0x7B,
        'ESCAPE': 0x1B, 'TAB': 0x09, 'SPACE': 0x20,
        'SHIFT': 0x10, 'CTRL': 0x11, 'ALT': 0x12,
        'INSERT': 0x2D, 'DELETE': 0x2E,
        'HOME': 0x24, 'END': 0x23,
        'PAGEUP': 0x21, 'PAGEDOWN': 0x22,
        'LEFT': 0x25, 'UP': 0x26, 'RIGHT': 0x27, 'DOWN': 0x28,
    }
    return key_mapping.get(key_name.upper(), 0)

def register_hotkey(hwnd, id, modifiers, vk):
    """Register a global hotkey"""
    return windll.user32.RegisterHotKey(hwnd, id, modifiers, vk)

def unregister_hotkey(hwnd, id):
    """Unregister a global hotkey"""
    return windll.user32.UnregisterHotKey(hwnd, id)

global_rgb_hue = getattr(sys.modules["__main__"], "global_rgb_hue", 0)

def update_global_rgb_hue():
    global global_rgb_hue
    global_rgb_hue = (global_rgb_hue + 2) % 360

def get_arial_greek_font(point_size=11, weight=QFont.Weight.Normal, italic=False):
    # Try to load from system first
    font = QFont("Arial Greek", point_size, weight, italic)
    if QFontInfo(font).family() == "Arial Greek":
        return font
    # Try to load from file
    font_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Arial Greek Regular.ttf")
    if os.path.exists(font_path):
        font_id = QFontDatabase.addApplicationFont(font_path)
        families = QFontDatabase.applicationFontFamilies(font_id)
        if families:
            return QFont(families[0], point_size, weight, italic)
    # Fallback
    return QFont("Arial", point_size, weight, italic)

class RGBSlider(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedHeight(40)
        self.setMouseTracking(True)
        self.checked = False
        self.hovered = False
        self._slider_pos = 0.0
        self.target_slider_pos = 0.0
        self.hover_animation = 0.0  # Переменная для анимации наведения
        self.check_opacity = 0.0
        self.rgb_opacity = 0.0  # Для плавной анимации RGB

        # Анимация слайдера
        self.slider_animation = QPropertyAnimation(self, b"slider_pos")
        self.slider_animation.setDuration(300)
        self.slider_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.slider_animation.valueChanged.connect(self._on_slider_value_changed)

        # Таймер для анимации RGB
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(40)

        self.setStyleSheet("""
            QWidget {
                color: #FFFFFF;
                font-family: Tahoma;
                font-size: 10pt;
            }
        """)

    def _on_slider_value_changed(self, value):
        self._slider_pos = value
        self.update()

    def enterEvent(self, event):
        self.hovered = True
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.hovered = False
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.toggle()
            event.accept()

    def toggle(self):
        self.checked = not self.checked
        self.target_slider_pos = 1.0 if self.checked else 0.0
        self.slider_animation.setStartValue(self._slider_pos)
        self.slider_animation.setEndValue(self.target_slider_pos)
        self.slider_animation.start()
        self.stateChanged.emit(self.checked)

    def update_animation(self):
        # Анимация наведения с плавным затуханием
        target_hover = 1.0 if self.hovered else 0.0
        if self.hover_animation < target_hover:
            self.hover_animation = min(self.hover_animation + 0.1, 1.0)
        elif self.hover_animation > target_hover:
            self.hover_animation = max(self.hover_animation - 0.1, 0.0)

        # Анимация состояния
        target_check = 1.0 if self.checked else 0.0
        if self.check_opacity < target_check:
            self.check_opacity = min(self.check_opacity + 0.5, 1.0)
        elif self.check_opacity > target_check:
            self.check_opacity = max(self.check_opacity - 0.5, 0.0)

        # Плавная анимация RGB эффекта (теперь насыщенность)
        target_rgb = 1.0 if self.checked else 0.0
        speed = 0.08
        if self.rgb_opacity < target_rgb:
            self.rgb_opacity = min(self.rgb_opacity + speed, 1.0)
        elif self.rgb_opacity > target_rgb:
            self.rgb_opacity = max(self.rgb_opacity - speed, 0.0)

        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        slider_rect = QRect(0, (self.height() - 24) // 2, 40, 24)
        base_bg = QColor("#1a1a1a")  # Made darker
        
        # Get RGB color and settings from rgb_utils
        r, g, b = global_rgb_color
        rgb_settings = load_rgb_settings()
        saturation = rgb_settings.get('saturation', 1.0)
        brightness = rgb_settings.get('brightness', 1.0)
        rgb_bg = QColor(r, g, b)
        h, s, v, _ = rgb_bg.getHsv()
        rgb_bg.setHsv(h if h is not None else 0, int(saturation * 255), int(brightness * 255 * 0.25))
        
        # Усиливаем RGB только если rgb_opacity > 0 (включено)
        rgb_alpha = 0.3 + (0.2 * self.hover_animation if self.rgb_opacity > 0 else 0)
        rgb_bg.setAlphaF(rgb_alpha)
        bg_color = self.blend_colors(base_bg, rgb_bg, self.rgb_opacity)
        
        # Добавляем эффект осветления при наведении для выключенного состояния
        if not self.checked:
            lighter_bg = QColor("#252525")  # Более светлая версия базового цвета
            bg_color = self.blend_colors(bg_color, lighter_bg, self.hover_animation * 0.5)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(bg_color)
        painter.drawRoundedRect(slider_rect, 12, 12)

        knob_pos = int(slider_rect.x() + self._slider_pos * (slider_rect.width() - 20))
        knob_rect = QRect(knob_pos, slider_rect.y() + 2, 20, 20)

        base_knob = QColor("#303030")  # Made darker
        rgb_knob = QColor(r, g, b)
        h, s, v, _ = rgb_knob.getHsv()
        if self.rgb_opacity > 0:
            rgb_knob.setHsv(h if h is not None else 0, int(saturation * 255), int(brightness * 255))
        else:
            rgb_knob.setHsv(h if h is not None else 0, int(saturation * 255), int(brightness * 200))
        knob_color = self.blend_colors(base_knob, rgb_knob, self.rgb_opacity)

        # Добавляем эффект осветления при наведении для ползунка
        if not self.checked:
            lighter_knob = QColor("#404040")  # Более светлая версия цвета ползунка
            knob_color = self.blend_colors(knob_color, lighter_knob, self.hover_animation * 0.5)

        # Фон ползунка с RGB (только если rgb_opacity > 0)
        if self.rgb_opacity > 0:
            bg_knob_color = QColor(r, g, b)
            h, s, v, _ = bg_knob_color.getHsv()
            bg_knob_color.setHsv(h if h is not None else 0, int(saturation * 200), int(brightness * 100))
            bg_knob_color.setAlphaF(0.4 + (0.3 * self.hover_animation))  # Увеличили базовую прозрачность
            painter.setBrush(bg_knob_color)
            painter.drawRoundedRect(knob_rect, 10, 10)

        painter.setBrush(knob_color)
        painter.drawRoundedRect(knob_rect, 10, 10)

    def blend_colors(self, color1, color2, t=0.5):
        # t=0: color1, t=1: color2
        return QColor(
            int(color1.red() * (1 - t) + color2.red() * t),
            int(color1.green() * (1 - t) + color2.green() * t),
            int(color1.blue() * (1 - t) + color2.blue() * t)
        )

    def isChecked(self):
        return self.checked

    def setChecked(self, checked):
        if self.checked != checked:
            self.toggle()

    # Сигнал для обработки изменений состояния
    stateChanged = pyqtSignal(bool)

class DecorativeRGBSquare(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedSize(48, 24)  # Same size as slider
        self.rgb_opacity = 0.0
        self.hover_animation = 0.0
        
        # Timer for animations
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(40)

    def update_animation(self):
        # Hover animation
        target_hover = 1.0 if self.underMouse() else 0.0
        if self.hover_animation < target_hover:
            self.hover_animation = min(self.hover_animation + 0.1, 1.0)
        elif self.hover_animation > target_hover:
            self.hover_animation = max(self.hover_animation - 0.1, 0.0)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Get current RGB color and settings from rgb_utils
        r, g, b = global_rgb_color
        rgb_settings = load_rgb_settings()
        saturation = rgb_settings.get('saturation', 1.0)
        brightness = rgb_settings.get('brightness', 1.0)
        rgb_color = QColor(r, g, b)
        h, s, v, _ = rgb_color.getHsv()
        rgb_color.setHsv(h if h is not None else 0, int(saturation * 255), int(brightness * 255))
        
        # Base color
        base_color = QColor("#252525")  # Made darker
        
        # Blend colors based on hover
        final_color = QColor(
            int(base_color.red() * (1 - self.hover_animation) + rgb_color.red() * self.hover_animation),
            int(base_color.green() * (1 - self.hover_animation) + rgb_color.green() * self.hover_animation),
            int(base_color.blue() * (1 - self.hover_animation) + rgb_color.blue() * self.hover_animation)
        )

        # Draw rounded rectangle
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(final_color)
        painter.drawRoundedRect(0, 0, self.width(), self.height(), 12, 12)

class FunctionRow(QWidget):
    def __init__(self, text, slot, show_gear=False, gear_callback=None, use_decorative_square=False):
        super().__init__()
        self.text = text
        self.setMinimumHeight(40)
        self.setMaximumHeight(40)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        if use_decorative_square:
            self.slider = DecorativeRGBSquare()
        else:
            self.slider = RGBSlider()
            self.slider.setFixedWidth(48)
            self.slider.stateChanged.connect(slot)
            
        self.slider.setParent(self)
        self.show_gear = show_gear
        self.gear_callback = gear_callback
        if self.show_gear:
            self.gear_icon = GearIcon(self)
            self.gear_icon.setParent(self)
            self.gear_icon.mousePressEvent = self.on_gear_clicked
        self.update_positions()

    def resizeEvent(self, event):
        self.update_positions()
        super().resizeEvent(event)

    def update_positions(self):
        slider_x = self.width() - 48
        self.slider.move(slider_x, (self.height() - self.slider.height()) // 2)
        if self.show_gear:
            gear_x = self.width() - 48 - 26  # 26px справа от слайдера
            self.gear_icon.move(gear_x, (self.height() - self.gear_icon.height()) // 2)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QColor("#ffffff"))
        font = get_arial_greek_font(11, QFont.Weight.Normal)
        painter.setFont(font)
        left = 10
        right = 48 + (26 if self.show_gear else 0) + 10  # место под слайдер и шестерёнку
        text_rect = QRect(left, 0, self.width() - right - left, self.height())
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, self.text)

    def on_gear_clicked(self, event):
        if self.gear_callback:
            self.gear_callback()
        event.accept()

class AnimatedButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setFixedSize(26, 26)
        self.hover_animation = 0.0
        self.setMouseTracking(True)
        
        # Таймер для анимации
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(40)

    def update_animation(self):
        target_hover = 1.0 if self.underMouse() else 0.0
        if self.hover_animation < target_hover:
            self.hover_animation = min(self.hover_animation + 0.1, 1.0)
        elif self.hover_animation > target_hover:
            self.hover_animation = max(self.hover_animation - 0.1, 0.0)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Рисуем фон с анимацией
        if self.hover_animation > 0:
            bg_color = QColor(255, 255, 255, int(40 * self.hover_animation))
            painter.setBrush(bg_color)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(self.rect(), 6, 6)

        # Рисуем текст
        painter.setPen(QColor("#FFFFFF"))
        font = get_arial_greek_font()
        font.setPointSize(14 if self.text() == "×" else 12)
        font.setBold(True)
        painter.setFont(font)
        
        # Центрируем текст с учетом символа
        text_rect = self.rect()
        if self.text() == "×":
            text_rect.setTop(text_rect.top() - 6)  # Поднимаем крестик
        elif self.text() == "—":
            text_rect.setTop(text_rect.top() - 6)  # Опускаем минус
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, self.text())

class GearPopup(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(220, 50)  # Уменьшили высоту с 90 до 70
        
        # Создаем контейнер для содержимого
        container = QWidget(self)
        container.setStyleSheet("""
            background-color: rgba(13, 13, 13, 100);
            border: 2px solid rgba(35, 34, 40, 150);
            border-radius: 10px;
        """)
        container.setFixedSize(self.size())
        
        # Основной layout для контейнера
        layout = QVBoxLayout(container)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # Создаем горизонтальный layout для заголовка и кнопки
        hlayout = QHBoxLayout()
        hlayout.setSpacing(8)
        
        # Добавляем заголовок
        title = QLabel("XCarry Bind")
        title.setFont(get_arial_greek_font(11, QFont.Weight.Normal))
        title.setStyleSheet("color: #FFFFFF; background: transparent; padding-left: 8px;")
        hlayout.addWidget(title)
        hlayout.addStretch()

        close_container = QWidget()
        close_layout = QHBoxLayout(close_container)
        close_layout.setContentsMargins(0, 0, 4, 0)
        close_layout.setSpacing(4)

        self.minimize_button = AnimatedButton("—")
        self.minimize_button.clicked.connect(self.showMinimized)
        close_layout.addWidget(self.minimize_button)

        self.close_button = AnimatedButton("×")
        self.close_button.clicked.connect(self.close)
        close_layout.addWidget(self.close_button)
        hlayout.addWidget(close_container)

        layout.addLayout(hlayout)
        
        # Create layout for main widget
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(container)

        self.listening = False
        self.update_bind_button()

    def update_bind_button(self):
        try:
            if os.path.exists("xcarry_bind.flag"):
                with open("xcarry_bind.flag", "r", encoding="utf-8") as f:
                    key = f.read().strip()
                text = key if key else "None"
            else:
                text = "None"
        except Exception:
            text = "None"
        self.bind_button.setText(text if not self.listening else "Press any key...")

    def start_listen_key(self):
        self.listening = True
        self.update_bind_button()
        self.grabKeyboard()

    def keyPressEvent(self, event):
        if self.listening:
            key = event.text().upper() if event.text() else ""
            # --- Маппинг русских букв на английские ---
            ru_to_en = {
                'Ф': 'A', 'И': 'B', 'С': 'C', 'В': 'D', 'У': 'E', 'А': 'F', 'П': 'G', 'Р': 'H', 'Ш': 'I', 'О': 'J',
                'Л': 'K', 'Д': 'L', 'Ь': 'M', 'Т': 'N', 'Щ': 'O', 'З': 'P', 'Й': 'Q', 'К': 'R', 'Ы': 'S', 'Е': 'T',
                'Г': 'U', 'М': 'V', 'Ц': 'W', 'Ч': 'X', 'Н': 'Y', 'Я': 'Z',
                # строчные
                'ф': 'A', 'и': 'B', 'с': 'C', 'в': 'D', 'у': 'E', 'а': 'F', 'п': 'G', 'р': 'H', 'ш': 'I', 'о': 'J',
                'л': 'K', 'д': 'L', 'ь': 'M', 'т': 'N', 'щ': 'O', 'з': 'P', 'й': 'Q', 'к': 'R', 'ы': 'S', 'е': 'T',
                'г': 'U', 'м': 'V', 'ц': 'W', 'ч': 'X', 'н': 'Y', 'я': 'Z',
            }
            if key in ru_to_en:
                key = ru_to_en[key]
            # --- END Маппинг ---
            if not key:  # спец. клавиши
                qt_key = event.key()
                key_name = Qt.Key(qt_key).name if hasattr(Qt.Key(qt_key), "name") else str(qt_key)
            else:
                key_name = key
            try:
                with open("xcarry_bind.flag", "w", encoding="utf-8") as f:
                    f.write(str(key_name))
            except Exception:
                pass
            self.releaseKeyboard()
            self.listening = False
            self.update_bind_button()
        else:
            super().keyPressEvent(event)

class BindPopup(QWidget):
    def __init__(self, parent=None, title="Bind", bind_file=None):
        super().__init__(parent)
        self.bind_file = bind_file
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(220, 90 if "Angle Bind" in title else 50)  # Higher height for Angle Bind popup
        
        # Create container for content
        container = QWidget(self)
        container.setStyleSheet("""
            background-color: rgba(13, 13, 13, 100);
            border: 2px solid rgba(35, 34, 40, 150);
            border-radius: 10px;
        """)
        container.setFixedSize(self.size())
        
        # Main layout for container
        layout = QVBoxLayout(container)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # Create horizontal layout for title and button
        hlayout = QHBoxLayout()
        hlayout.setSpacing(8)
        
        # Add title
        title_label = QLabel(title)
        title_label.setFont(get_arial_greek_font(11, QFont.Weight.Normal))
        title_label.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                background: transparent;
                border: none;
                margin: 0;
                padding: 0;
                spacing: 0;
            }
        """)
        hlayout.addWidget(title_label)

        # Add bind button
        self.bind_button = QPushButton()
        self.bind_button.setFixedSize(100, 26)
        self.bind_button.setFont(get_arial_greek_font(11, QFont.Weight.Normal))
        self.bind_button.setStyleSheet("""
            QPushButton {
                background-color: #252525;
                color: #ffffff;
                border-radius: 6px;
                padding: 0 12px;
                text-align: center;
            }
            QPushButton:hover {
                background-color: #303030;
                border: 1px solid #232228;
            }
            QPushButton:pressed {
                background-color: #202020;
            }
        """)
        self.bind_button.clicked.connect(self.start_listen_key)
        hlayout.addWidget(self.bind_button)
        hlayout.addStretch()
        
        layout.addLayout(hlayout)
        
        # Add angle slider section if this is an Angle Bind popup
        if "Angle Bind" in title:
            # Add separator
            separator = QFrame()
            separator.setFrameShape(QFrame.Shape.HLine)
            separator.setStyleSheet("background-color: #232228; margin: 4px 0px; border: none;")
            separator.setFixedHeight(1)
            layout.addWidget(separator)
            
            # Create horizontal layout for degree label and slider
            degree_layout = QHBoxLayout()
            degree_layout.setSpacing(8)
            degree_layout.setContentsMargins(0, 0, 0, 0)
            
            # Add degree label
            degree_label = QLabel("Degree")
            degree_label.setFont(get_arial_greek_font(11, QFont.Weight.Normal))
            degree_label.setStyleSheet("""
                QLabel {
                    color: #FFFFFF;
                    background: transparent;
                    padding: 0;
                    margin: 0;
                    border: none;
                    spacing: 0;
                }
            """)
            degree_layout.addWidget(degree_label)
            degree_layout.setAlignment(degree_label, Qt.AlignmentFlag.AlignVCenter)
            
            # Add angle slider
            self.angle_slider = AngleSlider()
            degree_layout.addWidget(self.angle_slider, 1)  # Added stretch factor of 1
            degree_layout.setAlignment(self.angle_slider, Qt.AlignmentFlag.AlignVCenter)
            
            # Add the degree layout to the main layout
            layout.addLayout(degree_layout)
            
        # Create layout for main widget
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(container)

        self.listening = False
        self.update_bind_button()

    def update_bind_button(self):
        try:
            if self.bind_file and os.path.exists(self.bind_file):
                with open(self.bind_file, "r", encoding="utf-8") as f:
                    key = f.read().strip()
                text = key if key else "None"
            else:
                text = "None"
        except Exception:
            text = "None"
        self.bind_button.setText(text if not self.listening else "Press any key...")

    def start_listen_key(self):
        self.listening = True
        self.update_bind_button()
        self.grabKeyboard()

    def keyPressEvent(self, event):
        if self.listening:
            if event.key() == Qt.Key.Key_Escape:
                # Clear the bind when ESC is pressed
                try:
                    if self.bind_file:
                        with open(self.bind_file, "w", encoding="utf-8") as f:
                            f.write("")
                except Exception:
                    pass
                self.listening = False
                self.update_bind_button()
                self.releaseKeyboard()
                return

            key = event.text().upper() if event.text() else ""
            # Russian to English mapping
            ru_to_en = {
                'Ф': 'A', 'И': 'B', 'С': 'C', 'В': 'D', 'У': 'E', 'А': 'F', 'П': 'G', 'Р': 'H', 'Ш': 'I', 'О': 'J',
                'Л': 'K', 'Д': 'L', 'Ь': 'M', 'Т': 'N', 'Щ': 'O', 'З': 'P', 'Й': 'Q', 'К': 'R', 'Ы': 'S', 'Е': 'T',
                'Г': 'U', 'М': 'V', 'Ц': 'W', 'Ч': 'X', 'Н': 'Y', 'Я': 'Z',
                'ф': 'A', 'и': 'B', 'с': 'C', 'в': 'D', 'у': 'E', 'а': 'F', 'п': 'G', 'р': 'H', 'ш': 'I', 'о': 'J',
                'л': 'K', 'д': 'L', 'ь': 'M', 'т': 'N', 'щ': 'O', 'з': 'P', 'й': 'Q', 'к': 'R', 'ы': 'S', 'е': 'T',
                'г': 'U', 'м': 'V', 'ц': 'W', 'ч': 'X', 'н': 'Y', 'я': 'Z',
            }
            if key in ru_to_en:
                key = ru_to_en[key]
            if not key:  # Special keys
                qt_key = event.key()
                key_name = Qt.Key(qt_key).name if hasattr(Qt.Key(qt_key), "name") else str(qt_key)
                # Convert Qt key names to our format
                key_name = key_name.replace("Key_", "").upper()
                # Special cases
                if event.key() == Qt.Key.Key_Space:
                    key_name = "SPACE"
                key_mapping = {
                    # Navigation keys
                    "PRIOR": "PAGEUP",
                    "NEXT": "PAGEDOWN",
                    "HOME": "HOME",
                    "END": "END",
                    "LEFT": "LEFT",
                    "RIGHT": "RIGHT",
                    "UP": "UP",
                    "DOWN": "DOWN",
                    "INSERT": "INSERT",
                    "DELETE": "DELETE",
                    # Modifier keys
                    "SHIFT": "SHIFT",
                    "CONTROL": "CTRL",
                    "ALT": "ALT",
                    "META": "WIN",
                    "CAPS": "CAPS",
                    "NUM": "NUMLOCK",
                    "SCROLL": "SCROLLLOCK",
                    # Function keys
                    "F1": "F1",
                    "F2": "F2",
                    "F3": "F3",
                    "F4": "F4",
                    "F5": "F5",
                    "F6": "F6",
                    "F7": "F7",
                    "F8": "F8",
                    "F9": "F9",
                    "F10": "F10",
                    "F11": "F11",
                    "F12": "F12",
                    "F13": "F13",
                    "F14": "F14",
                    "F15": "F15",
                    "F16": "F16",
                    "F17": "F17",
                    "F18": "F18",
                    "F19": "F19",
                    "F20": "F20",
                    "F21": "F21",
                    "F22": "F22",
                    "F23": "F23",
                    "F24": "F24",
                    "F25": "F25",
                    "F26": "F26",
                    # Other special keys
                    "ESCAPE": "ESCAPE",
                    "TAB": "TAB",
                    "BACKSPACE": "BACKSPACE",
                    "RETURN": "ENTER",
                    "ENTER": "ENTER",
                    "SPACE": "SPACE",
                    "PRINT": "PRINTSCREEN",
                    "PAUSE": "PAUSE",
                    "SNAPSHOT": "PRINTSCREEN",
                    # Media keys
                    "MEDIANEXT": "MEDIANEXT",
                    "MEDIAPREVIOUS": "MEDIAPREVIOUS",
                    "MEDIAPLAY": "MEDIAPLAY",
                    "MEDIASTOP": "MEDIASTOP",
                    "VOLUMEUP": "VOLUMEUP",
                    "VOLUMEDOWN": "VOLUMEDOWN",
                    "VOLUMEMUTE": "VOLUMEMUTE",
                    # Numpad keys
                    "NUMPAD0": "NUMPAD0",
                    "NUMPAD1": "NUMPAD1",
                    "NUMPAD2": "NUMPAD2",
                    "NUMPAD3": "NUMPAD3",
                    "NUMPAD4": "NUMPAD4",
                    "NUMPAD5": "NUMPAD5",
                    "NUMPAD6": "NUMPAD6",
                    "NUMPAD7": "NUMPAD7",
                    "NUMPAD8": "NUMPAD8",
                    "NUMPAD9": "NUMPAD9",
                    "NUMPADMULTIPLY": "NUMPADMULTIPLY",
                    "NUMPADPLUS": "NUMPADPLUS",
                    "NUMPADMINUS": "NUMPADMINUS",
                    "NUMPADDOT": "NUMPADDOT",
                    "NUMPADDIVIDE": "NUMPADDIVIDE",
                    "NUMPADENTER": "NUMPADENTER"
                }
                key_name = key_mapping.get(key_name, key_name)
            else:
                key_name = key
            try:
                if self.bind_file:
                    with open(self.bind_file, "w", encoding="utf-8") as f:
                        f.write(str(key_name))
            except Exception:
                pass
            self.listening = False
            self.update_bind_button()
            self.releaseKeyboard()
        else:
            super().keyPressEvent(event)

class ScriptGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent;")  # Добавляем прозрачный фон для основного виджета
        self.resize(260, 380)
        
        # Initialize menu bind monitoring
        self.current_menu_bind = None
        self.current_exit_bind = None
        self.menu_bind_timer = QTimer(self)
        self.menu_bind_timer.timeout.connect(self.check_menu_bind)
        self.menu_bind_timer.start(1000)  # Check every second
        
        # Initialize exit bind monitoring
        self.exit_bind_timer = QTimer(self)
        self.exit_bind_timer.timeout.connect(self.check_exit_bind)
        self.exit_bind_timer.start(1000)  # Check every second
        
        # Register initial hotkeys
        self.register_toggle_hotkey()
        self.register_exit_hotkey()
        
        outer_frame = QFrame(self)
        outer_frame.setObjectName("outer")
        outer_frame.setStyleSheet("""
            QFrame#outer {
                background-color: rgba(13, 13, 13, 100);  /* Уменьшаем непрозрачность еще больше */
                border: 2px solid rgba(35, 34, 40, 150);  /* Делаем границу тоже полупрозрачной */
                border-radius: 12px;
            }
        """)
        outer_layout = QVBoxLayout(outer_frame)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(outer_frame)

        self.header = QWidget()
        self.header.setFixedHeight(32)
        self.header.setStyleSheet("""
            background-color: rgba(0, 0, 0, 255);  /* Максимальная непрозрачность заголовка */
            border-top-left-radius: 12px;
            border-top-right-radius: 12px;
        """)
        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(0)

        title = QLabel("〜（ゝ。∂）")
        title.setFont(get_arial_greek_font(13, QFont.Weight.Normal))
        title.setStyleSheet("color: #FFFFFF; background: transparent; padding-left: 8px;")
        header_layout.addWidget(title)
        header_layout.addStretch()

        close_container = QWidget()
        close_layout = QHBoxLayout(close_container)
        close_layout.setContentsMargins(0, 0, 4, 0)
        close_layout.setSpacing(4)

        # Удаляем кнопку сворачивания
        self.close_button = AnimatedButton("×")
        self.close_button.clicked.connect(self.close)
        close_layout.addWidget(self.close_button)
        header_layout.addWidget(close_container)

        # Make header draggable
        self.header.setMouseTracking(True)
        self.header.mousePressEvent = self.header_mousePressEvent
        self.header.mouseMoveEvent = self.header_mouseMoveEvent
        self.header.mouseReleaseEvent = self.header_mouseReleaseEvent

        outer_layout.addWidget(self.header)

        # Создаем QScrollArea
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                border: none;
                background: rgba(26, 26, 26, 100);
                width: 8px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 50);
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(255, 255, 255, 80);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(8, 8, 8, 8)
        content_layout.setSpacing(12)

        def create_category(title, rows):
            frame = QFrame()
            frame.setObjectName("category")
            frame.setStyleSheet("""
                QFrame#category {
                    border: 1px solid #232228;
                    border-radius: 8px;
                    background-color: rgba(26, 26, 26, 100);
                }
            """)
            vbox = QVBoxLayout(frame)
            vbox.setContentsMargins(10, 10, 10, 10)
            vbox.setSpacing(0)
            label = QLabel(title)
            label.setFont(get_arial_greek_font(11, QFont.Weight.Normal))
            label.setStyleSheet("color: #ffffff; margin-bottom: 6px;")
            vbox.addWidget(label)
            for i, (row_text, row_slot, slider_attr, *extra) in enumerate(rows):
                show_gear = extra[0] if extra else False
                gear_callback = extra[1] if len(extra) > 1 else None
                use_decorative_square = extra[2] if len(extra) > 2 else False
                row_widget = FunctionRow(row_text, row_slot, show_gear, gear_callback, use_decorative_square)
                setattr(self, slider_attr, row_widget.slider)
                vbox.addWidget(row_widget)
                if i < len(rows) - 1:
                    sep = QFrame()
                    sep.setFrameShape(QFrame.Shape.HLine)
                    sep.setStyleSheet("background-color: #232228; border: none;")
                    sep.setFixedHeight(1)
                    vbox.addWidget(sep)
            return frame

        # Категория Movement
        movement_rows = [
            ("Angle Bind", self.toggle_anglebind, "anglebind_slider", True, self.show_anglebind_gear_popup),
            ("Auto Stop", self.toggle_autostop, "autostop_slider", True, self.show_autostop_gear_popup),
        ]
        movement_frame = create_category("Movement", movement_rows)
        content_layout.addWidget(movement_frame)

        # Категория Visuals
        visuals_rows = [
            ("Bomb Timer", self.toggle_bombtimer, "bombtimer_slider"),
            ("Sniper Crosshair", self.toggle_sniper, "sniper_slider"),
            ("Recoil Crosshair", self.toggle_recoilcrosshair, "recoilcrosshair_slider"),
            ("RGB Crosshair", self.toggle_rgbcrosshair, "rgb_slider"),
            ("Rainbow HUD", self.toggle_rainbowhud, "rainbowhud_slider"),
            ("Scope Anywhere", self.toggle_scope_anywhere, "scope_anywhere_slider"),
            ("Keystrokes", self.toggle_keystrokes, "keystrokes_slider"),
            ("Watermark", self.toggle_watermark, "watermark_slider"),
        ]
        visuals_frame = create_category("Visuals", visuals_rows)
        content_layout.addWidget(visuals_frame)

        # Категория Chat
        chat_rows = [
            ("Kill Say", self.toggle_killsay, "killsay_slider", True, self.show_killsay_gear_popup),
            ("Chat Spammer", self.toggle_chatspammer, "chatspammer_slider", True, self.show_chatspammer_gear_popup),
        ]
        chat_frame = create_category("Chat", chat_rows)
        content_layout.addWidget(chat_frame)
        self.chat_frame = chat_frame

        # Категория Weapon
        weapon_rows = [
            ("Auto Pistol", self.toggle_autopistol, "autopistol_slider"),
            ("R8 Revolver", self.toggle_r8, "r8_slider"),
            ("R8 Double", self.toggle_r8double, "r8double_slider", True, self.show_r8double_gear_popup),
            ("Knife Switch", self.toggle_knifeswitch, "knifeswitch_slider"),
            ("XCarry", self.toggle_xcarry, "xcarry_slider", True, self.show_xcarry_gear_popup),
            ("Trigger", self.toggle_trigger, "trigger_slider", True, self.show_trigger_gear_popup),
            # ("Jump Shoot", self.toggle_jumpshoot, "jumpshoot_slider", True, self.show_jumpshoot_gear_popup),  // Убрано из меню по просьбе пользователя
        ]
        weapon_frame = create_category("Weapon", weapon_rows)
        content_layout.addWidget(weapon_frame)
        self.weapon_frame = weapon_frame

        # Категория Audio
        audio_rows = [
            ("Kill Sound", self.toggle_killsound, "killsound_slider", True, self.show_killsound_gear_popup),
        ]
        audio_frame = create_category("Audio", audio_rows)
        content_layout.addWidget(audio_frame)
        self.audio_frame = audio_frame

        # Категория Automation
        automation_rows = [
            ("Auto Accept", self.toggle_autoaccept, "autoaccept_slider"),
            ("Anti AFK", self.toggle_antiafk, "antiafk_slider"),
            # ("Auto Report", self.toggle_autoreport, "autoreport_slider", True, self.show_autoreport_gear_popup),  # Убрано из меню по просьбе пользователя
        ]
        automation_frame = create_category("Automation", automation_rows)
        content_layout.addWidget(automation_frame)
        self.automation_frame = automation_frame

        # Категория Misc
        misc_rows = [
            ("Custom Binds", None, "custombinds_slider", True, self.show_custombinds_gear_popup, True),
            ("Gradient Manager", None, "gradient_manager_slider", True, self.show_gradient_manager_gear_popup, True),
            ("Font Changer", None, "font_changer_slider", True, self.show_font_changer_popup, True),
        ]
        misc_frame = create_category("Misc", misc_rows)
        content_layout.addWidget(misc_frame)
        self.misc_frame = misc_frame

        # Устанавливаем контент в QScrollArea
        scroll_area.setWidget(content)
        outer_layout.addWidget(scroll_area)

        # Create a transparent overlay for the background
        self.overlay = QWidget(self)
        self.overlay.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.overlay.setStyleSheet("background: transparent;")
        self.overlay.raise_()  # Put it behind other widgets

        self.xcarry_gear_popup = None
        self.autostop_gear_popup = None
        self.anglebind_gear_popup = None
        self.custombinds_gear_popup = None
        self.killsay_gear_popup = None
        self.chatspammer_gear_popup = None
        self.gradient_manager_gear_popup = None
        self.trigger_gear_popup = None
        self.r8double_gear_popup = None
        self.autoreport_gear_popup = None
        self.jumpshoot_gear_popup = None
        self.font_changer_gear_popup = None

        # Start custombinds.py automatically
        global gsi_proc
        if not gsi_proc or gsi_proc.poll() is not None:
            gsi_proc = start_script("GSI.py")
            if not gsi_proc:
                print("[error] Не удалось запустить GSI сервер для CustomBinds")
            else:
                print("[info] GSI сервер для CustomBinds запущен")

        self.custombinds_proc = start_script("CustomBinds.py")  # Исправлено: CustomBinds.py
        if self.custombinds_proc:
            print("[info] Custom Binds скрипт запущен")
        else:
            print("[error] Не удалось запустить Custom Binds скрипт")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Update overlay size to match window
        self.overlay.resize(self.size())

    def check_menu_bind(self):
        """Check if menu bind has changed and update if necessary"""
        try:
            if os.path.exists("menu_bind.flag"):
                with open("menu_bind.flag", "r", encoding="utf-8") as f:
                    new_bind = f.read().strip()
                
                # If bind has changed
                if new_bind != self.current_menu_bind:
                    # Unregister old hotkey if exists
                    if self.current_menu_bind:
                        unregister_hotkey(int(self.winId()), HOTKEY_ID)
                    
                    # Register new hotkey
                    if new_bind:
                        vk = get_vk_code(new_bind)
                        if vk:
                            if register_hotkey(int(self.winId()), HOTKEY_ID, 0, vk):
                                print(f"[info] Updated toggle hotkey: {new_bind}")
                                self.current_menu_bind = new_bind
                            else:
                                print(f"[error] Failed to register new hotkey: {new_bind}")
                    else:
                        self.current_menu_bind = None
        except Exception as e:
            print(f"[error] Failed to check menu bind: {e}")

    def register_toggle_hotkey(self):
        """Register the toggle hotkey from menu_bind.flag"""
        try:
            if os.path.exists("menu_bind.flag"):
                with open("menu_bind.flag", "r", encoding="utf-8") as f:
                    key = f.read().strip()
                if key:
                    vk = get_vk_code(key)
                    if vk:
                        # Register hotkey with no modifiers
                        if register_hotkey(int(self.winId()), HOTKEY_ID, 0, vk):
                            print(f"[info] Registered toggle hotkey: {key}")
                            self.current_menu_bind = key
                        else:
                            print(f"[error] Failed to register hotkey: {key}")
        except Exception as e:
            print(f"[error] Failed to register hotkey: {e}")

    def register_exit_hotkey(self):
        """Register the exit hotkey from exit_bind.flag"""
        try:
            if os.path.exists("exit_bind.flag"):
                with open("exit_bind.flag", "r", encoding="utf-8") as f:
                    key = f.read().strip()
                if key:
                    vk = get_vk_code(key)
                    if vk:
                        # Register hotkey with no modifiers
                        if register_hotkey(int(self.winId()), EXIT_HOTKEY_ID, 0, vk):
                            print(f"[info] Registered exit hotkey: {key}")
                            self.current_exit_bind = key
                        else:
                            print(f"[error] Failed to register exit hotkey: {key}")
        except Exception as e:
            print(f"[error] Failed to register exit hotkey: {e}")

    def nativeEvent(self, eventType, message):
        """Handle native Windows events"""
        try:
            if wintypes is None:
                return False, 0
                
            # Handle the case where message might be None
            if message is None:
                return False, 0
                
            msg = wintypes.MSG.from_address(int(message))
            if msg.message == 0x0312:  # WM_HOTKEY
                if msg.wParam == HOTKEY_ID:
                    self.toggle_visibility()
                    return True, 0
                elif msg.wParam == EXIT_HOTKEY_ID:
                    self.close()  # Close the application
                    return True, 0
        except Exception as e:
            print(f"[error] Native event handling failed: {e}")
        return False, 0

    def toggle_visibility(self):
        global menu_visibility_state
        if self.isVisible():
            # Close all popups before hiding main window
            if self.xcarry_gear_popup and self.xcarry_gear_popup.isVisible():
                self.xcarry_gear_popup.close()
            if self.autostop_gear_popup and self.autostop_gear_popup.isVisible():
                self.autostop_gear_popup.close()
            if self.anglebind_gear_popup and self.anglebind_gear_popup.isVisible():
                self.anglebind_gear_popup.close()
            if self.custombinds_gear_popup and self.custombinds_gear_popup.isVisible():
                self.custombinds_gear_popup.close()
            if self.killsay_gear_popup and self.killsay_gear_popup.isVisible():
                self.killsay_gear_popup.close()
            if self.chatspammer_gear_popup and self.chatspammer_gear_popup.isVisible():
                self.chatspammer_gear_popup.close()
            if self.gradient_manager_gear_popup and self.gradient_manager_gear_popup.isVisible():
                self.gradient_manager_gear_popup.close()
            # --- KillSoundPopup ---
            if hasattr(self, 'killsound_gear_popup') and self.killsound_gear_popup and self.killsound_gear_popup.isVisible():
                self.killsound_gear_popup.close()
            if self.trigger_gear_popup and self.trigger_gear_popup.isVisible():
                self.trigger_gear_popup.close()
            if self.r8double_gear_popup and self.r8double_gear_popup.isVisible():
                self.r8double_gear_popup.close()
            # --- AutoReportPopup ---
            if self.autoreport_gear_popup and self.autoreport_gear_popup.isVisible():
                self.autoreport_gear_popup.close()
            # --- JumpShootPopup ---
            if self.jumpshoot_gear_popup and self.jumpshoot_gear_popup.isVisible():
                self.jumpshoot_gear_popup.close()
            # --- FontChangerPopup ---
            if self.font_changer_gear_popup and self.font_changer_gear_popup.isVisible():
                self.font_changer_gear_popup.close()
            self.hide()
            menu_visibility_state = "HIDDEN"
        else:
            self.show()
            # Make sure window stays on top
            hwnd = int(self.winId())
            windll.user32.SetWindowPos(hwnd, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE)
            menu_visibility_state = "VISIBLE"

    def toggle_r8(self, state):
        global r8_proc, gsi_proc
        if state:
            # Start GSI server if not already running
            if not gsi_proc or gsi_proc.poll() is not None:
                gsi_proc = start_script("GSI.py")  # Исправлено: GSI.py
                if gsi_proc:
                    print("[info] GSI сервер запущен")
                else:
                    print("[error] Не удалось запустить GSI сервер")
                    self.r8_slider.setChecked(False)
                    return

            # Start R8 script
            r8_proc = start_script("R8.py")  # Исправлено: R8.py вместо r8.py
            if r8_proc:
                print("[info] R8 скрипт запущен")
            else:
                print("[error] Не удалось запустить R8 скрипт")
                self.r8_slider.setChecked(False)
        else:
            if r8_proc:
                stop_script(r8_proc)
                r8_proc = None
                print("[info] R8 скрипт остановлен")

    def toggle_sniper(self, state):
        global sniper_proc, gsi_proc
        if state:
            # Start GSI server if not already running
            if not gsi_proc or gsi_proc.poll() is not None:
                gsi_proc = start_script("GSI.py")  # Исправлено: GSI.py
                if gsi_proc:
                    print("[info] GSI сервер запущен")
                else:
                    print("[error] Не удалось запустить GSI сервер")
                    self.sniper_slider.setChecked(False)
                    return

            # Start sniper crosshair
            sniper_proc = start_script("Crosshair.py")  # Исправлено: Crosshair.py
            if sniper_proc:
                print("[info] Sniper Crosshair запущен")
            else:
                print("[error] Не удалось запустить Sniper Crosshair")
                self.sniper_slider.setChecked(False)
        else:
            if sniper_proc:
                stop_script(sniper_proc)
                sniper_proc = None
                print("[info] Sniper Crosshair остановлен")

    def toggle_rgbcrosshair(self, state):
        global rgb_proc
        if state:
            with open("rgb_enabled.flag", "w") as f:
                f.write("1")
            rgb_proc = start_script("RGBCrosshair.py")  # Исправлено: RGBCrosshair.py
        else:
            with open("rgb_enabled.flag", "w") as f:
                f.write("0")
            stop_script(rgb_proc)

    def toggle_rainbowhud(self, state):
        global rainbowhud_proc
        if state:
            rainbowhud_proc = start_script("RainbowHUD.py")  # Исправлено: RainbowHUD.py
        else:
            stop_script(rainbowhud_proc)

    def toggle_autostop(self, state):
        global autostop_proc
        if state:
            autostop_proc = start_script("AutoStop.py")  # Исправлено: AutoStop.py
        else:
            stop_script(autostop_proc)
            autostop_proc = None

    def toggle_xcarry(self, state):
        global xcarry_proc, gsi_proc
        if state:
            # Запускаем GSI если не запущен
            if not gsi_proc or gsi_proc.poll() is not None:
                gsi_proc = start_script("GSI.py")  # Исправлено: GSI.py
                if not gsi_proc:
                    print("[error] Не удалось запустить GSI сервер")
                    self.xcarry_slider.setChecked(False)
                    return
                print("[info] GSI сервер готов")

            # Запускаем xcarry
            xcarry_proc = start_script("XCarry.py")  # Исправлено: XCarry.py
            if xcarry_proc:
                print("[info] Xcarry скрипт запущен")
            else:
                print("[error] Не удалось запустить Xcarry")
                self.xcarry_slider.setChecked(False)
        else:
            if xcarry_proc:
                stop_script(xcarry_proc)
                xcarry_proc = None
                print("[info] Xcarry скрипт остановлен")

    def toggle_scope_anywhere(self, state):
        global scope_anywhere_proc
        if state:
            scope_anywhere_proc = start_script("Scope.py")  # Исправлено: Scope.py
            if scope_anywhere_proc:
                print("[info] Scope Anywhere запущен")
            else:
                print("[error] Не удалось запустить Scope Anywhere")
                self.scope_anywhere_slider.setChecked(False)
        else:
            if scope_anywhere_proc:
                stop_script(scope_anywhere_proc)
                scope_anywhere_proc = None
                print("[info] Scope Anywhere остановлен")

    def toggle_knifeswitch(self, state):
        global knifeswitch_proc, gsi_proc
        if state:
            # Запускаем GSI если не запущен
            if not gsi_proc or gsi_proc.poll() is not None:
                gsi_proc = start_script("GSI.py")  # Исправлено: GSI.py
                if not gsi_proc:
                    print("[error] Не удалось запустить GSI сервер")
                    self.knifeswitch_slider.setChecked(False)
                    return
                print("[info] GSI сервер готов")

            # Запускаем knifeswitch
            knifeswitch_proc = start_script("KnifeSwitch.py")  # Исправлено: KnifeSwitch.py
            if knifeswitch_proc:
                print("[info] Knife Switch скрипт запущен")
            else:
                print("[error] Не удалось запустить Knife Switch")
                self.knifeswitch_slider.setChecked(False)
        else:
            if knifeswitch_proc:
                stop_script(knifeswitch_proc)
                knifeswitch_proc = None
                print("[info] Knife Switch скрипт остановлен")

    def toggle_autopistol(self, state):
        global autopistol_proc, gsi_proc
        if state:
            # Запускаем GSI если не запущен
            if not gsi_proc or gsi_proc.poll() is not None:
                gsi_proc = start_script("GSI.py")  # Исправлено: GSI.py
                if not gsi_proc:
                    print("[error] Не удалось запустить GSI сервер")
                    self.autopistol_slider.setChecked(False)
                    return
                print("[info] GSI сервер готов")
            # Запускаем autopistol
            autopistol_proc = start_script("AutoPistol.py")  # Исправлено: AutoPistol.py
            if autopistol_proc:
                print("[info] Auto Pistol скрипт запущен")
            else:
                print("[error] Не удалось запустить Auto Pistol")
                self.autopistol_slider.setChecked(False)
        else:
            if autopistol_proc:
                stop_script(autopistol_proc)
                autopistol_proc = None
                print("[info] Auto Pistol скрипт остановлен")

    def toggle_bombtimer(self, state):
        global bombtimer_proc, gsi_proc
        if state:
            # Запускаем GSI если не запущен
            if not gsi_proc or gsi_proc.poll() is not None:
                gsi_proc = start_script("GSI.py")  # Исправлено: GSI.py
                if not gsi_proc:
                    print("[error] Не удалось запустить GSI сервер")
                    self.bombtimer_slider.setChecked(False)
                    return
                print("[info] GSI сервер готов")
            # Запускаем bombtimer
            bombtimer_proc = start_script("BombTimer.py")  # Исправлено: BombTimer.py
            if bombtimer_proc:
                print("[info] Bomb Timer скрипт запущен")
            else:
                print("[error] Не удалось запустить Bomb Timer")
                self.bombtimer_slider.setChecked(False)
        else:
            if bombtimer_proc:
                stop_script(bombtimer_proc)
                bombtimer_proc = None
                print("[info] Bomb Timer скрипт остановлен")

    def toggle_anglebind(self, state):
        global anglebind_proc
        if state:
            anglebind_proc = start_script("AngleBind.py")  # Исправлено: AngleBind.py
            if anglebind_proc:
                print("[info] Angle Bind скрипт запущен")
            else:
                print("[error] Не удалось запустить Angle Bind")
                self.anglebind_slider.setChecked(False)
        else:
            if anglebind_proc:
                stop_script(anglebind_proc)
                anglebind_proc = None
                print("[info] Angle Bind скрипт остановлен")

    def toggle_keystrokes(self, state):
        global keystrokes_proc
        if state:
            keystrokes_proc = start_script("Keystrokes.py")  # Исправлено: Keystrokes.py
        else:
            stop_script(keystrokes_proc)

    def toggle_watermark(self, state):
        global watermark_proc, gsi_proc
        if state:
            # Запускать GSI если не запущен
            if not gsi_proc or gsi_proc.poll() is not None:
                gsi_proc = start_script("GSI.py")  # Исправлено: GSI.py
                if not gsi_proc:
                    print("[error] Не удалось запустить GSI сервер")
                    self.watermark_slider.setChecked(False)
                    return
                print("[info] GSI сервер готов")
            watermark_proc = start_script("Watermark.py")  # Исправлено: Watermark.py
        else:
            stop_script(watermark_proc)

    def toggle_killsay(self, state):
        global killsay_proc, gsi_proc
        if state:
            # Start GSI server if not already running
            if not gsi_proc or gsi_proc.poll() is not None:
                gsi_proc = start_script("GSI.py")  # Исправлено: GSI.py
                if not gsi_proc:
                    print("[error] Не удалось запустить GSI сервер")
                    self.killsay_slider.setChecked(False)
                    return
                print("[info] GSI сервер готов")

            # Start KillSay script
            killsay_proc = start_script("KillSay.py")  # Исправлено: KillSay.py
            if killsay_proc:
                print("[info] KillSay скрипт запущен")
            else:
                print("[error] Не удалось запустить KillSay")
                self.killsay_slider.setChecked(False)
        else:
            if killsay_proc:
                stop_script(killsay_proc)
                killsay_proc = None
                print("[info] KillSay скрипт остановлен")

    def toggle_chatspammer(self, state):
        global chatspammer_proc
        if state:
            chatspammer_proc = start_script("ChatSpammer.py")  # Исправлено: ChatSpammer.py
            if chatspammer_proc:
                print("[info] Chat Spammer скрипт запущен")
            else:
                print("[error] Не удалось запустить Chat Spammer")
                self.chatspammer_slider.setChecked(False)
        else:
            if chatspammer_proc:
                stop_script(chatspammer_proc)
                chatspammer_proc = None
                print("[info] Chat Spammer скрипт остановлен")

    def toggle_recoilcrosshair(self, state):
        global recoilcrosshair_proc
        if state:
            if recoilcrosshair_proc is None:
                recoilcrosshair_proc = start_script("RecoilCrosshair.py")  # Исправлено: RecoilCrosshair.py
        else:
            if recoilcrosshair_proc is not None:
                stop_script(recoilcrosshair_proc)
                recoilcrosshair_proc = None

    def toggle_killsound(self, state):
        global killsound_proc, gsi_proc
        if state:
            # Запускать GSI если не запущен
            if not gsi_proc or gsi_proc.poll() is not None:
                gsi_proc = start_script("GSI.py")  # Исправлено: GSI.py
                if not gsi_proc:
                    print("[error] Не удалось запустить GSI сервер")
                    self.killsound_slider.setChecked(False)
                    return
                print("[info] GSI сервер готов")
            killsound_proc = start_script("KillSound.py")  # Исправлено: KillSound.py
            if killsound_proc:
                print("[info] Kill Sound скрипт запущен")
            else:
                print("[error] Не удалось запустить Kill Sound")
                self.killsound_slider.setChecked(False)
        else:
            if killsound_proc:
                stop_script(killsound_proc)
                killsound_proc = None
                print("[info] Kill Sound скрипт остановлен")

    def toggle_autoaccept(self, state):
        global autoaccept_proc
        if state:
            autoaccept_proc = start_script("AutoAccept.py")  # Исправлено: AutoAccept.py
            if autoaccept_proc:
                print("[info] Auto Accept скрипт запущен")
            else:
                print("[error] Не удалось запустить Auto Accept")
                self.autoaccept_slider.setChecked(False)
        else:
            if autoaccept_proc:
                stop_script(autoaccept_proc)
                autoaccept_proc = None
                print("[info] Auto Accept скрипт остановлен")

    def toggle_antiafk(self, state):
        global anti_afk_proc, gsi_proc
        if state:
            # Запускать GSI если не запущен
            if not gsi_proc or gsi_proc.poll() is not None:
                gsi_proc = start_script("GSI.py")  # Исправлено: GSI.py
                if not gsi_proc:
                    print("[error] Не удалось запустить GSI сервер")
                    self.antiafk_slider.setChecked(False)
                    return
                print("[info] GSI сервер готов")
            anti_afk_proc = start_script("AntiAFK.py")  # Исправлено: AntiAFK.py
            if anti_afk_proc:
                print("[info] Anti AFK скрипт запущен")
            else:
                print("[error] Не удалось запустить Anti AFK")
                self.antiafk_slider.setChecked(False)
        else:
            if anti_afk_proc:
                stop_script(anti_afk_proc)
                anti_afk_proc = None
                print("[info] Anti AFK скрипт остановлен")

    def toggle_trigger(self, state):
        global trigger_proc
        if state:
            trigger_proc = start_script("Trigger.py")  # Исправлено: Trigger.py
            if trigger_proc:
                print("[info] Trigger скрипт запущен")
            else:
                print("[error] Не удалось запустить Trigger")
                self.trigger_slider.setChecked(False)
        else:
            if trigger_proc:
                stop_script(trigger_proc)
                trigger_proc = None
                print("[info] Trigger скрипт остановлен")

    def toggle_r8double(self, state):
        global r8double_proc
        if state:
            r8double_proc = start_script("R8Double.py")  # Исправлено: R8Double.py
            if r8double_proc:
                print("[info] R8 Double скрипт запущен")
            else:
                print("[error] Не удалось запустить R8 Double скрипт")
                self.r8double_slider.setChecked(False)
        else:
            if r8double_proc:
                stop_script(r8double_proc)
                r8double_proc = None
                print("[info] R8 Double скрипт остановлен")

    def toggle_autoreport(self, state):
        global autoreport_proc
        if state:
            autoreport_proc = start_script("AutoReport.py")
        else:
            if autoreport_proc:
                stop_script(autoreport_proc)
                autoreport_proc = None

    def toggle_jumpshoot(self, state):
        global jumpshoot_proc
        if state:
            jumpshoot_proc = start_script("JumpShoot.py")
            if jumpshoot_proc:
                print("[info] JumpShoot скрипт запущен")
            else:
                print("[error] Не удалось запустить JumpShoot")
                self.jumpshoot_slider.setChecked(False)
        else:
            if jumpshoot_proc:
                stop_script(jumpshoot_proc)
                jumpshoot_proc = None
                print("[info] JumpShoot скрипт остановлен")

    def show_xcarry_gear_popup(self):
        if self.xcarry_gear_popup and self.xcarry_gear_popup.isVisible():
            self.xcarry_gear_popup.close()
            return
            
        # Создаем попап с указанием заголовка и файла для бинда
        self.xcarry_gear_popup = BindPopup(self, "XCarry Bind", "xcarry_bind.flag")
        
        # Получаем глобальные координаты функции XCarry
        xcarry_slider_parent = self.xcarry_slider.parent()
        xcarry_global_pos = xcarry_slider_parent.mapToGlobal(xcarry_slider_parent.rect().topLeft())
        
        # Позиционируем попап справа от функции XCarry с дополнительным смещением
        x = xcarry_global_pos.x() + xcarry_slider_parent.width() + 35
        y = xcarry_global_pos.y() - 5
        
        self.xcarry_gear_popup.move(x, y)
        self.xcarry_gear_popup.show()

    def show_autostop_gear_popup(self):
        if self.autostop_gear_popup and self.autostop_gear_popup.isVisible():
            self.autostop_gear_popup.close()
            return
            
        self.autostop_gear_popup = BindPopup(self, "Hotkey Bind", "autostop_bind.flag")
        autostop_slider_parent = self.autostop_slider.parent()
        autostop_global_pos = autostop_slider_parent.mapToGlobal(autostop_slider_parent.rect().topLeft())
        x = autostop_global_pos.x() + autostop_slider_parent.width() + 35
        y = autostop_global_pos.y() - 5
        self.autostop_gear_popup.move(x, y)
        self.autostop_gear_popup.show()

    def show_anglebind_gear_popup(self):
        if self.anglebind_gear_popup and self.anglebind_gear_popup.isVisible():
            self.anglebind_gear_popup.close()
            return
        
        self.anglebind_gear_popup = BindPopup(self, "Angle Bind", "angle_bind.flag")
        anglebind_slider_parent = self.anglebind_slider.parent()
        anglebind_global_pos = anglebind_slider_parent.mapToGlobal(anglebind_slider_parent.rect().topLeft())
        x = anglebind_global_pos.x() + anglebind_slider_parent.width() + 35
        y = anglebind_global_pos.y() - 55
        self.anglebind_gear_popup.move(x, y)
        self.anglebind_gear_popup.show()

    def show_custombinds_gear_popup(self):
        if self.custombinds_gear_popup and self.custombinds_gear_popup.isVisible():
            self.custombinds_gear_popup.close()
            return
            
        self.custombinds_gear_popup = CustomBindsPopup(self)
        custombinds_slider_parent = self.custombinds_slider.parent()
        custombinds_global_pos = custombinds_slider_parent.mapToGlobal(custombinds_slider_parent.rect().topLeft())
        x = custombinds_global_pos.x() + custombinds_slider_parent.width() + 35
        y = custombinds_global_pos.y() - 45
        self.custombinds_gear_popup.move(x, y)
        self.custombinds_gear_popup.show()

    def show_killsay_gear_popup(self):
        if self.killsay_gear_popup and self.killsay_gear_popup.isVisible():
            self.killsay_gear_popup.close()
            return
            
        self.killsay_gear_popup = KillSayPopup(self)
        killsay_slider_parent = self.killsay_slider.parent()
        killsay_global_pos = killsay_slider_parent.mapToGlobal(killsay_slider_parent.rect().topLeft())
        x = killsay_global_pos.x() + killsay_slider_parent.width() + 35
        y = killsay_global_pos.y() - 50
        self.killsay_gear_popup.move(x, y)
        self.killsay_gear_popup.show()

    def show_chatspammer_gear_popup(self):
        if self.chatspammer_gear_popup and self.chatspammer_gear_popup.isVisible():
            self.chatspammer_gear_popup.close()
            return
            
        self.chatspammer_gear_popup = ChatSpammerPopup(self)
        chatspammer_slider_parent = self.chatspammer_slider.parent()
        chatspammer_global_pos = chatspammer_slider_parent.mapToGlobal(chatspammer_slider_parent.rect().topLeft())
        x = chatspammer_global_pos.x() + chatspammer_slider_parent.width() + 35
        y = chatspammer_global_pos.y() + 5
        self.chatspammer_gear_popup.move(x, y)
        self.chatspammer_gear_popup.show()

    def show_gradient_manager_gear_popup(self):
        if self.gradient_manager_gear_popup and self.gradient_manager_gear_popup.isVisible():
            self.gradient_manager_gear_popup.close()
            return
        self.gradient_manager_gear_popup = GradientManagerPopup(self)
        self.gradient_manager_gear_popup.show()
        self.reposition_gradient_manager_popup()

    def reposition_gradient_manager_popup(self):
        if self.gradient_manager_gear_popup and self.gradient_manager_gear_popup.isVisible():
            gradient_manager_slider_parent = self.gradient_manager_slider.parent()
            gradient_manager_global_pos = gradient_manager_slider_parent.mapToGlobal(gradient_manager_slider_parent.rect().topLeft())
            x = gradient_manager_global_pos.x() + gradient_manager_slider_parent.width() + 35
            y = gradient_manager_global_pos.y() - 5
            self.gradient_manager_gear_popup.move(x, y)

    def header_mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def header_mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            # Перемещаем окно
            self.move(event.globalPosition().toPoint() - self.drag_position)
            # Обновляем позиции всех открытых попапов
            if self.xcarry_gear_popup and self.xcarry_gear_popup.isVisible():
                xcarry_slider_parent = self.xcarry_slider.parent()
                xcarry_global_pos = xcarry_slider_parent.mapToGlobal(xcarry_slider_parent.rect().topLeft())
                self.xcarry_gear_popup.move(xcarry_global_pos.x() + xcarry_slider_parent.width() + 35, xcarry_global_pos.y() - 5)
            if self.autostop_gear_popup and self.autostop_gear_popup.isVisible():
                autostop_slider_parent = self.autostop_slider.parent()
                autostop_global_pos = autostop_slider_parent.mapToGlobal(autostop_slider_parent.rect().topLeft())
                self.autostop_gear_popup.move(autostop_global_pos.x() + autostop_slider_parent.width() + 35, autostop_global_pos.y() - 5)
            if self.anglebind_gear_popup and self.anglebind_gear_popup.isVisible():
                anglebind_slider_parent = self.anglebind_slider.parent()
                anglebind_global_pos = anglebind_slider_parent.mapToGlobal(anglebind_slider_parent.rect().topLeft())
                self.anglebind_gear_popup.move(anglebind_global_pos.x() + anglebind_slider_parent.width() + 35, anglebind_global_pos.y() - 55)
            if self.custombinds_gear_popup and self.custombinds_gear_popup.isVisible():
                custombinds_slider_parent = self.custombinds_slider.parent()
                custombinds_global_pos = custombinds_slider_parent.mapToGlobal(custombinds_slider_parent.rect().topLeft())
                self.custombinds_gear_popup.move(custombinds_global_pos.x() + custombinds_slider_parent.width() + 35, custombinds_global_pos.y() - 45)
            if self.killsay_gear_popup and self.killsay_gear_popup.isVisible():
                killsay_slider_parent = self.killsay_slider.parent()
                killsay_global_pos = killsay_slider_parent.mapToGlobal(killsay_slider_parent.rect().topLeft())
                self.killsay_gear_popup.move(killsay_global_pos.x() + killsay_slider_parent.width() + 35, killsay_global_pos.y() - 50)
            if self.chatspammer_gear_popup and self.chatspammer_gear_popup.isVisible():
                chatspammer_slider_parent = self.chatspammer_slider.parent()
                chatspammer_global_pos = chatspammer_slider_parent.mapToGlobal(chatspammer_slider_parent.rect().topLeft())
                self.chatspammer_gear_popup.move(chatspammer_global_pos.x() + chatspammer_slider_parent.width() + 35, chatspammer_global_pos.y() + 5)
            if self.trigger_gear_popup and self.trigger_gear_popup.isVisible():
                trigger_slider_parent = self.trigger_slider.parent()
                trigger_global_pos = trigger_slider_parent.mapToGlobal(trigger_slider_parent.rect().topLeft())
                self.trigger_gear_popup.move(trigger_global_pos.x() + trigger_slider_parent.width() + 35, trigger_global_pos.y() - 5)
            if self.gradient_manager_gear_popup and self.gradient_manager_gear_popup.isVisible():
                self.reposition_gradient_manager_popup()
            self.reposition_killsound_popup()
            if self.r8double_gear_popup and self.r8double_gear_popup.isVisible():
                r8double_slider_parent = self.r8double_slider.parent()
                r8double_global_pos = r8double_slider_parent.mapToGlobal(r8double_slider_parent.rect().topLeft())
                self.r8double_gear_popup.move(r8double_global_pos.x() + r8double_slider_parent.width() + 35, r8double_global_pos.y() - 5)
            # --- AutoReportPopup ---
            if self.autoreport_gear_popup and self.autoreport_gear_popup.isVisible():
                autoreport_slider_parent = self.autoreport_slider.parent()
                autoreport_global_pos = autoreport_slider_parent.mapToGlobal(autoreport_slider_parent.rect().topLeft())
                self.autoreport_gear_popup.move(autoreport_global_pos.x() + autoreport_slider_parent.width() + 35, autoreport_global_pos.y() - 5)
            # --- JumpShootPopup ---
            if self.jumpshoot_gear_popup and self.jumpshoot_gear_popup.isVisible():
                jumpshoot_slider_parent = self.jumpshoot_slider.parent()
                jumpshoot_global_pos = jumpshoot_slider_parent.mapToGlobal(jumpshoot_slider_parent.rect().topLeft())
                self.jumpshoot_gear_popup.move(jumpshoot_global_pos.x() + jumpshoot_slider_parent.width() + 35, jumpshoot_global_pos.y() - 5)
            # --- FontChangerPopup ---
            if self.font_changer_gear_popup and self.font_changer_gear_popup.isVisible():
                font_changer_slider_parent = self.font_changer_slider.parent()
                font_changer_global_pos = font_changer_slider_parent.mapToGlobal(font_changer_slider_parent.rect().topLeft())
                self.font_changer_gear_popup.move(font_changer_global_pos.x() + font_changer_slider_parent.width() + 35, font_changer_global_pos.y() - 5)
            event.accept()

    def header_mouseReleaseEvent(self, event):
        self.drag_position = None

    def check_exit_bind(self):
        """Check if exit bind has changed and update if necessary"""
        try:
            if os.path.exists("exit_bind.flag"):
                with open("exit_bind.flag", "r", encoding="utf-8") as f:
                    new_bind = f.read().strip()
                
                # If bind has changed
                if new_bind != self.current_exit_bind:
                    # Unregister old hotkey if exists
                    if self.current_exit_bind:
                        unregister_hotkey(int(self.winId()), EXIT_HOTKEY_ID)
                    
                    # Register new hotkey
                    if new_bind:
                        vk = get_vk_code(new_bind)
                        if vk:
                            if register_hotkey(int(self.winId()), EXIT_HOTKEY_ID, 0, vk):
                                print(f"[info] Updated exit hotkey: {new_bind}")
                                self.current_exit_bind = new_bind
                            else:
                                print(f"[error] Failed to register new exit hotkey: {new_bind}")
                    else:
                        self.current_exit_bind = None
        except Exception as e:
            print(f"[error] Failed to check exit bind: {e}")

    def closeEvent(self, event):
        """Clean up when closing"""
        # Stop menu bind monitoring
        self.menu_bind_timer.stop()
        self.exit_bind_timer.stop()
        
        # Unregister hotkeys
        if self.current_menu_bind:
            unregister_hotkey(int(self.winId()), HOTKEY_ID)
        if self.current_exit_bind:
            unregister_hotkey(int(self.winId()), EXIT_HOTKEY_ID)
        
        # Stop all scripts
        global r8_proc, sniper_proc, rgb_proc, rainbowhud_proc, gsi_proc
        global autostop_proc, xcarry_proc, scope_anywhere_proc, knifeswitch_proc, autopistol_proc
        global bombtimer_proc, anglebind_proc, keystrokes_proc, killsay_proc, chatspammer_proc, watermark_proc, killsound_proc, autoaccept_proc, anti_afk_proc  # Add anti_afk_proc here
        global r8double_proc
        if r8_proc:
            stop_script(r8_proc)
        if sniper_proc:
            stop_script(sniper_proc)
        if rgb_proc:
            stop_script(rgb_proc)
        if rainbowhud_proc:
            stop_script(rainbowhud_proc)
        if gsi_proc:
            stop_script(gsi_proc)
        if autostop_proc:
            stop_script(autostop_proc)
        if xcarry_proc:
            stop_script(xcarry_proc)
        if scope_anywhere_proc:
            stop_script(scope_anywhere_proc)
        if knifeswitch_proc:
            stop_script(knifeswitch_proc)
        if autopistol_proc:
            stop_script(autopistol_proc)
        if bombtimer_proc:
            stop_script(bombtimer_proc)
        if anglebind_proc:
            stop_script(anglebind_proc)
        if hasattr(self, 'custombinds_proc') and self.custombinds_proc:
            stop_script(self.custombinds_proc)
        if keystrokes_proc:
            stop_script(keystrokes_proc)
        if killsay_proc:  # Add this block
            stop_script(killsay_proc)
        if chatspammer_proc:  # Add this block
            stop_script(chatspammer_proc)
        if watermark_proc:  # Add this block
            stop_script(watermark_proc)
        if killsound_proc:  # Add this block
            stop_script(killsound_proc)
        if autoaccept_proc:  # Add this block
            stop_script(autoaccept_proc)
        if anti_afk_proc:  # Add this block
            stop_script(anti_afk_proc)
        if trigger_proc:  # Add trigger process
            stop_script(trigger_proc)
        if r8double_proc:
            stop_script(r8double_proc)
            r8double_proc = None
        # --- KillSoundPopup ---
        if hasattr(self, 'killsound_gear_popup') and self.killsound_gear_popup and self.killsound_gear_popup.isVisible():
            self.killsound_gear_popup.close()
        event.accept()
        from PyQt6.QtWidgets import QApplication
        QApplication.quit()

    def show_killsound_gear_popup(self):
        if hasattr(self, 'killsound_gear_popup') and self.killsound_gear_popup and self.killsound_gear_popup.isVisible():
            self.killsound_gear_popup.close()
            return
        self.killsound_gear_popup = KillSoundPopup(self)
        killsound_slider_parent = self.killsound_slider.parent()
        killsound_global_pos = killsound_slider_parent.mapToGlobal(killsound_slider_parent.rect().topLeft())
        x = killsound_global_pos.x() + killsound_slider_parent.width() + 35
        y = killsound_global_pos.y() - 5
        self.killsound_gear_popup.move(x, y)
        self.killsound_gear_popup.show()

    def reposition_killsound_popup(self):
        if hasattr(self, 'killsound_gear_popup') and self.killsound_gear_popup and self.killsound_gear_popup.isVisible():
            killsound_slider_parent = self.killsound_slider.parent()
            killsound_global_pos = killsound_slider_parent.mapToGlobal(killsound_slider_parent.rect().topLeft())
            x = killsound_global_pos.x() + killsound_slider_parent.width() + 35
            y = killsound_global_pos.y() - 5
            self.killsound_gear_popup.move(x, y)

    def show_trigger_gear_popup(self):
        if self.trigger_gear_popup and self.trigger_gear_popup.isVisible():
            self.trigger_gear_popup.close()
            return
            
        # Создаем попап с указанием заголовка и файла для бинда
        self.trigger_gear_popup = BindPopup(self, "Trigger Bind", "trigger_bind.flag")
        
        # Получаем глобальные координаты функции Trigger
        trigger_slider_parent = self.trigger_slider.parent()
        trigger_global_pos = trigger_slider_parent.mapToGlobal(trigger_slider_parent.rect().topLeft())
        
        # Позиционируем попап справа от функции Trigger с дополнительным смещением
        x = trigger_global_pos.x() + trigger_slider_parent.width() + 35
        y = trigger_global_pos.y() - 5
        
        self.trigger_gear_popup.move(x, y)
        self.trigger_gear_popup.show()

    def show_r8double_gear_popup(self):
        if hasattr(self, 'r8double_gear_popup') and self.r8double_gear_popup and self.r8double_gear_popup.isVisible():
            self.r8double_gear_popup.close()
            return
        self.r8double_gear_popup = BindPopup(self, "Hotkey Bind", "r8double_bind.flag")
        r8double_slider_parent = self.r8double_slider.parent()
        r8double_global_pos = r8double_slider_parent.mapToGlobal(r8double_slider_parent.rect().topLeft())
        x = r8double_global_pos.x() + r8double_slider_parent.width() + 35
        y = r8double_global_pos.y() - 5
        self.r8double_gear_popup.move(x, y)
        self.r8double_gear_popup.show()

    def show_autoreport_gear_popup(self):
        global autoreport_proc  # Добавлено объявление глобальной переменной
        if self.autoreport_gear_popup and self.autoreport_gear_popup.isVisible():
            self.autoreport_gear_popup.close()
            return
        self.autoreport_gear_popup = AutoReportPopup(self)
        autoreport_slider_parent = self.autoreport_slider.parent()
        autoreport_global_pos = autoreport_slider_parent.mapToGlobal(autoreport_slider_parent.rect().topLeft())
        x = autoreport_global_pos.x() + autoreport_slider_parent.width() + 35
        y = autoreport_global_pos.y() - 5
        self.autoreport_gear_popup.move(x, y)
        self.autoreport_gear_popup.show()

    def show_jumpshoot_gear_popup(self):
        if hasattr(self, 'jumpshoot_gear_popup') and self.jumpshoot_gear_popup and self.jumpshoot_gear_popup.isVisible():
            self.jumpshoot_gear_popup.close()
            return
        self.jumpshoot_gear_popup = BindPopup(self, "Jump Bind", "jumpshoot_bind.flag")
        jumpshoot_slider_parent = self.jumpshoot_slider.parent()
        jumpshoot_global_pos = jumpshoot_slider_parent.mapToGlobal(jumpshoot_slider_parent.rect().topLeft())
        x = jumpshoot_global_pos.x() + jumpshoot_slider_parent.width() + 35
        y = jumpshoot_global_pos.y() - 5
        self.jumpshoot_gear_popup.move(x, y)
        self.jumpshoot_gear_popup.show()

    def show_font_changer_popup(self):
        if self.font_changer_gear_popup and self.font_changer_gear_popup.isVisible():
            self.font_changer_gear_popup.close()
            return
        self.font_changer_gear_popup = FontChangerPopup(self)
        font_changer_slider_parent = self.font_changer_slider.parent()
        font_changer_global_pos = font_changer_slider_parent.mapToGlobal(font_changer_slider_parent.rect().topLeft())
        x = font_changer_global_pos.x() + font_changer_slider_parent.width() + 35
        y = font_changer_global_pos.y() - 5
        self.font_changer_gear_popup.move(x, y)
        self.font_changer_gear_popup.show()

def wait_for_shared_memory(name, timeout=5):
    # Функция больше не нужна, оставлена пустой для совместимости, можно удалить полностью
    pass

class AngleSlider(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedSize(120, 26)
        self.value = 180  # Default value
        self.dragging = False
        self.setMouseTracking(True)
        self.rgb_opacity = 0.0
        self._hover_anim = 0.0  # Для плавного ховера
        
        # Путь до конфигурационного файла anglebind
        self.cfg_path = os.path.join(find_csgo_cfg_path() or '', 'pyscripts7.cfg')

        # Load saved value if exists
        try:
            with open("angle_value.txt", "r") as f:
                self.value = int(f.read().strip())
                self.update_cfg_file()  # Update config when loading saved value
        except:
            self.value = 180

        # --- Таймер для плавной анимации RGB и ховера ---
        from PyQt6.QtCore import QTimer
        self._rgb_timer = QTimer(self)
        self._rgb_timer.timeout.connect(self._animate)
        self._rgb_timer.start(40)

    def angle_to_yaw(self, angle):
        RATIO = 4306.22 / 180  # 23.9234444444
        return angle * RATIO

    def update_cfg_file(self):
        """Обновляет конфиг CS2 с текущим значением yaw"""
        try:
            yaw = self.angle_to_yaw(self.value)
            content = f"yaw {yaw:.4f} 1 0\n"
            with open(self.cfg_path, "w") as f:
                f.write(content)
        except Exception as e:
            print(f"[Ошибка записи файла anglebind.cfg]: {e}")

    def _animate(self):
        # Плавная анимация ховера
        target = 1.0 if self.dragging or self.underMouse() else 0.0
        speed = 0.08  # Уменьшили скорость с 0.13 до 0.08 для более плавной анимации
        if self._hover_anim < target:
            self._hover_anim = min(self._hover_anim + speed, 1.0)
        elif self._hover_anim > target:
            self._hover_anim = max(self._hover_anim - speed, 0.0)
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.update_value(event.pos().x())

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = False

    def mouseMoveEvent(self, event):
        if self.dragging:
            self.update_value(event.pos().x())

    def enterEvent(self, event):
        self.rgb_opacity = 1.0
        self.update()

    def leaveEvent(self, event):
        if not self.dragging:
            self.rgb_opacity = 0.0
            self.update()

    def update_value(self, x):
        x = max(0, min(x, self.width()))
        self.value = int((x / self.width()) * 360 - 180)
        self.value = max(-180, min(180, self.value))
        # Save value to file
        try:
            with open("angle_value.txt", "w") as f:
                f.write(str(self.value))
        except:
            pass
        # Update CS2 config
        self.update_cfg_file()
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw background
        base_bg = QColor("#252525")  # Made darker
        
        # Get RGB color and settings from rgb_utils
        r, g, b = global_rgb_color
        rgb_settings = load_rgb_settings()
        saturation = rgb_settings.get('saturation', 1.0)
        brightness = rgb_settings.get('brightness', 1.0)
        dark_rgb = QColor(r, g, b)
        h, s, v, _ = dark_rgb.getHsv()
        dark_rgb.setHsv(h if h is not None else 0, int(saturation * 180), int(brightness * 60))
        
        t = 0.55 * self._hover_anim
        bg_color = QColor(
            int(base_bg.red() * (1 - t) + dark_rgb.red() * t),
            int(base_bg.green() * (1 - t) + dark_rgb.green() * t),
            int(base_bg.blue() * (1 - t) + dark_rgb.blue() * t)
        )

        # 1. Draw background
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(bg_color)
        painter.drawRoundedRect(1, 1, self.width() - 2, self.height() - 2, 6, 6)

        # 2. Draw border (под слайдером)
        r, g, b = global_rgb_color
        rgb_color = QColor(r, g, b)
        h, s, v, _ = rgb_color.getHsv()
        rgb_color.setHsv(h if h is not None else 0, int(saturation * 200), int(brightness * 120))
        
        # Создаем базовый цвет обводки
        base_color = QColor("#232228")
        
        # Интерполируем между базовым и RGB цветом
        border_color = QColor(
            int(base_color.red() * (1 - self._hover_anim) + rgb_color.red() * self._hover_anim),
            int(base_color.green() * (1 - self._hover_anim) + rgb_color.green() * self._hover_anim),
            int(base_color.blue() * (1 - self._hover_anim) + rgb_color.blue() * self._hover_anim)
        )
        
        pen = QPen(border_color)
        pen.setWidth(2)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(1, 1, self.width() - 2, self.height() - 2, 6, 6)

        # 3. Draw value indicator (RGB прямоугольник) — ограниченная зона!
        margin = 4  # внутренний отступ
        slider_width = self.width() - 2 * margin
        x = int((self.value + 180) * slider_width / 360) + margin
        
        # Базовый серый цвет для индикатора
        base_indicator = QColor("#606060")  # Сделали серый цвет светлее
        
        # RGB цвет для индикатора
        r, g, b = global_rgb_color
        rgb_indicator = QColor(r, g, b)
        h, s, v, _ = rgb_indicator.getHsv()
        rgb_indicator.setHsv(h if h is not None else 0, int(saturation * 255), int(brightness * 255))
        
        # Интерполируем между базовым и RGB цветом
        indicator_color = QColor(
            int(base_indicator.red() * (1 - self._hover_anim) + rgb_indicator.red() * self._hover_anim),
            int(base_indicator.green() * (1 - self._hover_anim) + rgb_indicator.green() * self._hover_anim),
            int(base_indicator.blue() * (1 - self._hover_anim) + rgb_indicator.blue() * self._hover_anim)
        )
        
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(indicator_color)
        painter.drawRoundedRect(x - 2, 2, 4, self.height() - 4, 3, 3)

        # 4. Draw value text (поверх всего)
        painter.setPen(QColor("#FFFFFF"))
        font = get_arial_greek_font(11, QFont.Weight.Normal)
        painter.setFont(font)
        text = str(self.value) + "°"
        text_rect = self.rect()
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, text)

class CustomBindsPopup(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(270, 200)  # Reduced width from 300 to 280
        
        # Create container for content
        container = QWidget(self)
        container.setStyleSheet("""
            background-color: rgba(13, 13, 13, 100);
            border: 2px solid rgba(35, 34, 40, 150);
            border-radius: 10px;
        """)
        container.setFixedSize(self.size())
        
        # Main layout for container
        layout = QVBoxLayout(container)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(4)  # Reduced spacing from 8 to 4

        # Add binds
        self.add_bind_row(layout, "Long Jump Bind", "longjump_bind.flag")
        self.add_bind_row(layout, "Jump Throw Bind", "jumpthrow_bind.flag")
        self.add_bind_row(layout, "Self Kick Bind", "selfkick_bind.flag")

        # Add separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: #232228; margin: 4px 0px; border: none;")
        separator.setFixedHeight(1)
        layout.addWidget(separator)

        # Add menu and exit binds
        self.add_bind_row(layout, "Menu Bind", "menu_bind.flag")
        self.add_bind_row(layout, "Exit Bind", "exit_bind.flag")
        
        # Create layout for main widget
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(container)

    def add_bind_row(self, layout, title, bind_file):
        # Create horizontal layout for title and bind button
        hlayout = QHBoxLayout()
        hlayout.setSpacing(8)
        
        # Add title
        title_label = QLabel(title)
        title_label.setFont(get_arial_greek_font(11, QFont.Weight.Normal))
        title_label.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                background: transparent;
                border: none;
                margin: 0;
                padding: 0;
                spacing: 0;
            }
        """)
        hlayout.addWidget(title_label)

        # Spacer to push button to the right
        hlayout.addStretch()

        # Add bind button
        bind_button = QPushButton()
        bind_button.setFixedSize(120, 26)  # Increased width from 100 to 120
        bind_button.setFont(get_arial_greek_font(11, QFont.Weight.Normal))
        bind_button.setStyleSheet("""
            QPushButton {
                background-color: #252525;
                color: #ffffff;
                border-radius: 6px;
                padding: 0 12px;
                text-align: center;
            }
            QPushButton:hover {
                background-color: #303030;
                border: 1px solid #232228;
            }
            QPushButton:pressed {
                background-color: #202020;
            }
        """)
        bind_button.setProperty("bind_file", bind_file)  # Store bind_file as a property
        bind_button.clicked.connect(lambda: self.start_listen_key(bind_button))
        hlayout.addWidget(bind_button)
        # (удалено) hlayout.addStretch()
        
        layout.addLayout(hlayout)
        self.update_bind_button(bind_button)

    def update_bind_button(self, button):
        try:
            bind_file = button.property("bind_file")
            if bind_file and os.path.exists(bind_file):
                with open(bind_file, "r", encoding="utf-8") as f:
                    key = f.read().strip()
                text = key if key else "None"
            else:
                text = "None"
        except Exception:
            text = "None"
        listening = button.property("listening") or False
        button.setText(text if not listening else "Press any key...")

    def start_listen_key(self, button):
        button.setProperty("listening", True)
        self.update_bind_button(button)
        self.grabKeyboard()

    def keyPressEvent(self, event):
        for child in self.findChildren(QPushButton):
            if child.property("listening"):
                if event.key() == Qt.Key.Key_Escape:
                    try:
                        bind_file = child.property("bind_file")
                        if bind_file:
                            with open(bind_file, "w", encoding="utf-8") as f:
                                f.write("")
                    except Exception:
                        pass
                    child.setProperty("listening", False)
                    self.update_bind_button(child)
                    self.releaseKeyboard()
                    return
                key = event.text().upper() if event.text() else ""
                ru_to_en = {
                    'Ф': 'A', 'И': 'B', 'С': 'C', 'В': 'D', 'У': 'E', 'А': 'F', 'П': 'G', 'Р': 'H', 'Ш': 'I', 'О': 'J',
                    'Л': 'K', 'Д': 'L', 'Ь': 'M', 'Т': 'N', 'Щ': 'O', 'З': 'P', 'Й': 'Q', 'К': 'R', 'Ы': 'S', 'Е': 'T',
                    'Г': 'U', 'М': 'V', 'Ц': 'W', 'Ч': 'X', 'Н': 'Y', 'Я': 'Z',
                    'ф': 'A', 'и': 'B', 'с': 'C', 'в': 'D', 'у': 'E', 'а': 'F', 'п': 'G', 'р': 'H', 'ш': 'I', 'о': 'J',
                    'л': 'K', 'д': 'L', 'ь': 'M', 'т': 'N', 'щ': 'O', 'з': 'P', 'й': 'Q', 'к': 'R', 'ы': 'S', 'е': 'T',
                    'г': 'U', 'м': 'V', 'ц': 'W', 'ч': 'X', 'н': 'Y', 'я': 'Z',
                }
                if key in ru_to_en:
                    key = ru_to_en[key]
                if not key:  # Special keys
                    qt_key = event.key()
                    key_name = Qt.Key(qt_key).name if hasattr(Qt.Key(qt_key), "name") else str(qt_key)
                    key_name = key_name.replace("Key_", "").upper()
                    key_mapping = {
                        "PRIOR": "PAGEUP",
                        "NEXT": "PAGEDOWN",
                        "HOME": "HOME",
                        "END": "END",
                        "LEFT": "LEFT",
                        "RIGHT": "RIGHT",
                        "UP": "UP",
                        "DOWN": "DOWN",
                        "INSERT": "INSERT",
                        "DELETE": "DELETE",
                        "SHIFT": "SHIFT",
                        "CONTROL": "CTRL",
                        "ALT": "ALT",
                        "META": "WIN",
                        "CAPS": "CAPS",
                        "NUM": "NUMLOCK",
                        "SCROLL": "SCROLLLOCK",
                        "F1": "F1",
                        "F2": "F2",
                        "F3": "F3",
                        "F4": "F4",
                        "F5": "F5",
                        "F6": "F6",
                        "F7": "F7",
                        "F8": "F8",
                        "F9": "F9",
                        "F10": "F10",
                        "F11": "F11",
                        "F12": "F12",
                        "F13": "F13",
                        "F14": "F14",
                        "F15": "F15",
                        "F16": "F16",
                        "F17": "F17",
                        "F18": "F18",
                        "F19": "F19",
                        "F20": "F20",
                        "F21": "F21",
                        "F22": "F22",
                        "F23": "F23",
                        "F24": "F24",
                        "F25": "F25",
                        "F26": "F26",
                        "ESCAPE": "ESCAPE",
                        "TAB": "TAB",
                        "BACKSPACE": "BACKSPACE",
                        "RETURN": "ENTER",
                        "ENTER": "ENTER",
                        "SPACE": "SPACE",
                        "PRINT": "PRINTSCREEN",
                        "PAUSE": "PAUSE",
                        "SNAPSHOT": "PRINTSCREEN",
                        "MEDIANEXT": "MEDIANEXT",
                        "MEDIAPREVIOUS": "MEDIAPREVIOUS",
                        "MEDIAPLAY": "MEDIAPLAY",
                        "MEDIASTOP": "MEDIASTOP",
                        "VOLUMEUP": "VOLUMEUP",
                        "VOLUMEDOWN": "VOLUMEDOWN",
                        "VOLUMEMUTE": "VOLUMEMUTE",
                        "NUMPAD0": "NUMPAD0",
                        "NUMPAD1": "NUMPAD1",
                        "NUMPAD2": "NUMPAD2",
                        "NUMPAD3": "NUMPAD3",
                        "NUMPAD4": "NUMPAD4",
                        "NUMPAD5": "NUMPAD5",
                        "NUMPAD6": "NUMPAD6",
                        "NUMPAD7": "NUMPAD7",
                        "NUMPAD8": "NUMPAD8",
                        "NUMPAD9": "NUMPAD9",
                        "NUMPADMULTIPLY": "NUMPADMULTIPLY",
                        "NUMPADPLUS": "NUMPADPLUS",
                        "NUMPADMINUS": "NUMPADMINUS",
                        "NUMPADDOT": "NUMPADDOT",
                        "NUMPADDIVIDE": "NUMPADDIVIDE",
                        "NUMPADENTER": "NUMPADENTER",
                    }
                    key_name = key_mapping.get(key_name, key_name)
                    key = key_name
                try:
                    bind_file = child.property("bind_file")
                    if bind_file:
                        with open(bind_file, "w", encoding="utf-8") as f:
                            f.write(str(key))
                except Exception:
                    pass
                child.setProperty("listening", False)
                self.update_bind_button(child)
                self.releaseKeyboard()
                return
        super().keyPressEvent(event)

class KillSayPopup(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(260, 90)
        
        # Path to CS:GO config file
        self.cfg_path = os.path.join(find_csgo_cfg_path() or '', 'pyscripts11.cfg')
        
        # Create container for content
        container = QWidget(self)
        container.setStyleSheet("""
            background-color: rgba(13, 13, 13, 100);
            border: 2px solid rgba(35, 34, 40, 150);
            border-radius: 10px;
        """)
        container.setFixedSize(self.size())
        
        # Main layout for container
        layout = QVBoxLayout(container)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # Add title
        title_label = QLabel("Chat Message")
        title_label.setFont(get_arial_greek_font(11, QFont.Weight.Normal))
        title_label.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                background: transparent;
                border: none;
                margin: 0;
                padding: 0;
                spacing: 0;
            }
        """)
        layout.addWidget(title_label)

        # Add text input
        self.text_input = QLineEdit()
        self.text_input.setFont(get_arial_greek_font(11))
        self.text_input.setStyleSheet("""
            QLineEdit {
                background-color: #252525;
                color: #ffffff;
                border: 1px solid #232228;
                border-radius: 6px;
                padding: 4px 8px;
            }
            QLineEdit:focus {
                border: 1px solid #303030;
            }
        """)
        self.text_input.setPlaceholderText("Enter kill message...")
        self.text_input.textChanged.connect(self.save_message)
        layout.addWidget(self.text_input)

        # Load saved message if exists
        try:
            if os.path.exists(self.cfg_path):
                with open(self.cfg_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    # Extract message from "say" command
                    if "say" in content:
                        message = content.split("say", 1)[1].strip()
                        self.text_input.setText(message)
        except Exception as e:
            print(f"[error] Failed to load message from config: {e}")

        # Create layout for main widget
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(container)

    def save_message(self):
        try:
            message = self.text_input.text()
            # Write message with "say" command to config file
            with open(self.cfg_path, "w", encoding="utf-8") as f:
                f.write(f"say {message}")
        except Exception as e:
            print(f"[error] Failed to save message to config: {e}")

class ChatSpammerPopup(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(260, 120)  # Increased height
        
        # Path to CS:GO config file
        self.cfg_path = os.path.join(find_csgo_cfg_path() or '', 'pyscripts10.cfg')
        
        # Create container for content
        container = QWidget(self)
        container.setStyleSheet("""
            background-color: rgba(13, 13, 13, 100);
            border: 2px solid rgba(35, 34, 40, 150);
            border-radius: 10px;
        """)
        container.setFixedSize(self.size())
        
        # Main layout for container
        layout = QVBoxLayout(container)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # Add title
        title_label = QLabel("Chat Message")
        title_label.setFont(get_arial_greek_font(11, QFont.Weight.Normal))
        title_label.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                background: transparent;
                border: none;
                margin: 0;
                padding: 0;
                spacing: 0;
            }
        """)
        layout.addWidget(title_label)

        # Add text input
        self.text_input = QLineEdit()
        self.text_input.setFont(get_arial_greek_font(11))
        self.text_input.setStyleSheet("""
            QLineEdit {
                background-color: #252525;
                color: #ffffff;
                border: 1px solid #232228;
                border-radius: 6px;
                padding: 4px 8px;
            }
            QLineEdit:focus {
                border: 1px solid #303030;
            }
        """)
        self.text_input.setPlaceholderText("Enter chat message...")
        self.text_input.textChanged.connect(self.save_message)
        layout.addWidget(self.text_input)

        # Add separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: #232228; margin: 4px 0px; border: none;")
        separator.setFixedHeight(1)
        layout.addWidget(separator)

        # Create horizontal layout for bind button
        bind_layout = QHBoxLayout()
        bind_layout.setSpacing(8)
        
        # Add bind label
        bind_label = QLabel("Hotkey")
        bind_label.setFont(get_arial_greek_font(11, QFont.Weight.Normal))
        bind_label.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                background: transparent;
                border: none;
                margin: 0;
                padding: 0;
                spacing: 0;
            }
        """)
        bind_layout.addWidget(bind_label)

        # Add bind button
        self.bind_button = QPushButton()
        self.bind_button.setFixedSize(100, 26)
        self.bind_button.setFont(get_arial_greek_font(11, QFont.Weight.Normal))
        self.bind_button.setStyleSheet("""
            QPushButton {
                background-color: #252525;
                color: #ffffff;
                border-radius: 6px;
                padding: 0 12px;
                text-align: center;
            }
            QPushButton:hover {
                background-color: #303030;
                border: 1px solid #232228;
            }
            QPushButton:pressed {
                background-color: #202020;
            }
        """)
        self.bind_button.clicked.connect(self.start_listen_key)
        bind_layout.addWidget(self.bind_button)
        bind_layout.addStretch()
        
        layout.addLayout(bind_layout)

        # Load saved message if exists
        try:
            if os.path.exists(self.cfg_path):
                with open(self.cfg_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    # Extract message from "say" command
                    if "say" in content:
                        message = content.split("say", 1)[1].strip()
                        self.text_input.setText(message)
        except Exception as e:
            print(f"[error] Failed to load message from config: {e}")

        # Create layout for main widget
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(container)

        self.listening = False
        self.update_bind_button()

    def save_message(self):
        try:
            message = self.text_input.text()
            # Write message with "say" command to config file
            with open(self.cfg_path, "w", encoding="utf-8") as f:
                f.write(f"say {message}")
        except Exception as e:
            print(f"[error] Failed to save message to config: {e}")

    def update_bind_button(self):
        try:
            if os.path.exists("chatspammer_bind.flag"):
                with open("chatspammer_bind.flag", "r", encoding="utf-8") as f:
                    key = f.read().strip()
                text = key if key else "None"
            else:
                text = "None"
        except Exception:
            text = "None"
        self.bind_button.setText(text if not self.listening else "Press any key...")

    def start_listen_key(self):
        self.listening = True
        self.update_bind_button()
        self.grabKeyboard()

    def keyPressEvent(self, event):
        if self.listening:
            if event.key() == Qt.Key.Key_Escape:
                # Clear the bind when ESC is pressed
                try:
                    with open("chatspammer_bind.flag", "w", encoding="utf-8") as f:
                        f.write("")
                except Exception:
                    pass
                self.listening = False
                self.update_bind_button()
                self.releaseKeyboard()
                return

            key = event.text().upper() if event.text() else ""
            # Russian to English mapping
            ru_to_en = {
                'Ф': 'A', 'И': 'B', 'С': 'C', 'В': 'D', 'У': 'E', 'А': 'F', 'П': 'G', 'Р': 'H', 'Ш': 'I', 'О': 'J',
                'Л': 'K', 'Д': 'L', 'Ь': 'M', 'Т': 'N', 'Щ': 'O', 'З': 'P', 'Й': 'Q', 'К': 'R', 'Ы': 'S', 'Е': 'T',
                'Г': 'U', 'М': 'V', 'Ц': 'W', 'Ч': 'X', 'Н': 'Y', 'Я': 'Z',
                'ф': 'A', 'и': 'B', 'с': 'C', 'в': 'D', 'у': 'E', 'а': 'F', 'п': 'G', 'р': 'H', 'ш': 'I', 'о': 'J',
                'л': 'K', 'д': 'L', 'ь': 'M', 'т': 'N', 'щ': 'O', 'з': 'P', 'й': 'Q', 'к': 'R', 'ы': 'S', 'е': 'T',
                'г': 'U', 'м': 'V', 'ц': 'W', 'ч': 'X', 'н': 'Y', 'я': 'Z',
            }
            if key in ru_to_en:
                key = ru_to_en[key]
            if not key:  # Special keys
                qt_key = event.key()
                key_name = Qt.Key(qt_key).name if hasattr(Qt.Key(qt_key), "name") else str(qt_key)
                # Convert Qt key names to our format
                key_name = key_name.replace("Key_", "").upper()
                # Special cases
                key_mapping = {
                    # Navigation keys
                    "PRIOR": "PAGEUP",
                    "NEXT": "PAGEDOWN",
                    "HOME": "HOME",
                    "END": "END",
                    "LEFT": "LEFT",
                    "RIGHT": "RIGHT",
                    "UP": "UP",
                    "DOWN": "DOWN",
                    "INSERT": "INSERT",
                    "DELETE": "DELETE",
                    
                    # Modifier keys
                    "SHIFT": "SHIFT",
                    "CONTROL": "CTRL",
                    "ALT": "ALT",
                    "META": "WIN",
                    "CAPS": "CAPS",
                    "NUM": "NUMLOCK",
                    "SCROLL": "SCROLLLOCK",
                    
                    # Function keys
                    "F1": "F1",
                    "F2": "F2",
                    "F3": "F3",
                    "F4": "F4",
                    "F5": "F5",
                    "F6": "F6",
                    "F7": "F7",
                    "F8": "F8",
                    "F9": "F9",
                    "F10": "F10",
                    "F11": "F11",
                    "F12": "F12",
                    "F13": "F13",
                    "F14": "F14",
                    "F15": "F15",
                    "F16": "F16",
                    "F17": "F17",
                    "F18": "F18",
                    "F19": "F19",
                    "F20": "F20",
                    "F21": "F21",
                    "F22": "F22",
                    "F23": "F23",
                    "F24": "F24",
                    "F25": "F25",
                    "F26": "F26",
                    
                    # Other special keys
                    "ESCAPE": "ESCAPE",
                    "TAB": "TAB",
                    "BACKSPACE": "BACKSPACE",
                    "RETURN": "ENTER",
                    "ENTER": "ENTER",
                    "SPACE": "SPACE",
                    "PRINT": "PRINTSCREEN",
                    "PAUSE": "PAUSE",
                    "SNAPSHOT": "PRINTSCREEN",
                    
                    # Media keys
                    "MEDIANEXT": "MEDIANEXT",
                    "MEDIAPREVIOUS": "MEDIAPREVIOUS",
                    "MEDIAPLAY": "MEDIAPLAY",
                    "MEDIASTOP": "MEDIASTOP",
                    "VOLUMEUP": "VOLUMEUP",
                    "VOLUMEDOWN": "VOLUMEDOWN",
                    "VOLUMEMUTE": "VOLUMEMUTE",
                    
                    # Numpad keys
                    "NUMPAD0": "NUMPAD0",
                    "NUMPAD1": "NUMPAD1",
                    "NUMPAD2": "NUMPAD2",
                    "NUMPAD3": "NUMPAD3",
                    "NUMPAD4": "NUMPAD4",
                    "NUMPAD5": "NUMPAD5",
                    "NUMPAD6": "NUMPAD6",
                    "NUMPAD7": "NUMPAD7",
                    "NUMPAD8": "NUMPAD8",
                    "NUMPAD9": "NUMPAD9",
                    "NUMPADMULTIPLY": "NUMPADMULTIPLY",
                    "NUMPADPLUS": "NUMPADPLUS",
                    "NUMPADMINUS": "NUMPADMINUS",
                    "NUMPADDOT": "NUMPADDOT",
                    "NUMPADDIVIDE": "NUMPADDIVIDE",
                    "NUMPADENTER": "NUMPADENTER"
                }
                key_name = key_mapping.get(key_name, key_name)
            else:
                key_name = key
            try:
                with open("chatspammer_bind.flag", "w", encoding="utf-8") as f:
                    f.write(str(key_name))
            except Exception:
                pass
            self.listening = False
            self.update_bind_button()
            self.releaseKeyboard()
        else:
            super().keyPressEvent(event)

def menu_pipe_server():
    address = r'\\.\pipe\menu_visibility_pipe'
    while True:
        try:
            with multiprocessing.connection.Listener(address, 'AF_PIPE') as listener:
                while True:
                    with listener.accept() as conn:
                        conn.send(menu_visibility_state)
        except Exception as e:
            print(f"[pipe] Ошибка pipe: {e}")
            time.sleep(1)

class GradientManagerPopup(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(225, 200)
        self.cfg_path = "rgb.cfg"
        self.settings = {
            'speed': 0.5,
            'saturation': 1.0,
            'brightness': 1.0,
            'steps': 0.5
        }
        self.load_settings()
        container = QWidget(self)
        container.setStyleSheet("""
            background-color: rgba(13, 13, 13, 100);
            border: 2px solid rgba(35, 34, 40, 150);
            border-radius: 10px;
        """)
        container.setFixedSize(self.size())
        layout = QVBoxLayout(container)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)
        # --- Preview row ---
        preview_row = QHBoxLayout()
        preview_row.setContentsMargins(0, 0, 0, 0)
        preview_row.setSpacing(8)
        preview_label = QLabel("Preview")
        preview_label.setFont(get_arial_greek_font(11, QFont.Weight.Normal))
        preview_label.setStyleSheet("color: #FFFFFF; background: none; border: none;")
        preview_row.addWidget(preview_label)
        preview_row.addStretch(1)
        self.preview = GradientPreviewWidget(self)
        self.preview.setFixedSize(120, 25)
        preview_row.addWidget(self.preview)
        layout.addLayout(preview_row)
        # --- Separator ---
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: #232228; margin: 4px 0px; border: none;")
        separator.setFixedHeight(1)
        layout.addWidget(separator)
        # --- Speed row ---
        speed_row = QHBoxLayout()
        speed_row.setContentsMargins(0, 0, 0, 0)
        speed_row.setSpacing(8)
        speed_label = QLabel("Speed")
        speed_label.setFont(get_arial_greek_font(11, QFont.Weight.Normal))
        speed_label.setStyleSheet("color: #FFFFFF; background: none; border: none;")
        speed_row.addWidget(speed_label)
        speed_row.addStretch(1)
        self.speed_slider = AngleSliderLike(0.01, 10.00, self.settings['speed'], self.on_speed_changed)
        speed_row.addWidget(self.speed_slider)
        layout.addLayout(speed_row)
        # --- Saturation row ---
        saturation_row = QHBoxLayout()
        saturation_row.setContentsMargins(0, 0, 0, 0)
        saturation_row.setSpacing(8)
        saturation_label = QLabel("Saturation")
        saturation_label.setFont(get_arial_greek_font(11, QFont.Weight.Normal))
        saturation_label.setStyleSheet("color: #FFFFFF; background: none; border: none;")
        saturation_row.addWidget(saturation_label)
        saturation_row.addStretch(1)
        self.saturation_slider = AngleSliderLike(0.00, 1.00, self.settings['saturation'], self.on_saturation_changed)
        saturation_row.addWidget(self.saturation_slider)
        layout.addLayout(saturation_row)
        # --- Brightness row ---
        brightness_row = QHBoxLayout()
        brightness_row.setContentsMargins(0, 0, 0, 0)
        brightness_row.setSpacing(8)
        brightness_label = QLabel("Brightness")
        brightness_label.setFont(get_arial_greek_font(11, QFont.Weight.Normal))
        brightness_label.setStyleSheet("color: #FFFFFF; background: none; border: none;")
        brightness_row.addWidget(brightness_label)
        brightness_row.addStretch(1)
        self.brightness_slider = AngleSliderLike(0.01, 1.00, self.settings['brightness'], self.on_brightness_changed)
        brightness_row.addWidget(self.brightness_slider)
        layout.addLayout(brightness_row)
        # --- Steps row ---
        steps_row = QHBoxLayout()
        steps_row.setContentsMargins(0, 0, 0, 0)
        steps_row.setSpacing(8)
        steps_label = QLabel("Steps")
        steps_label.setFont(get_arial_greek_font(11, QFont.Weight.Normal))
        steps_label.setStyleSheet("color: #FFFFFF; background: none; border: none;")
        steps_row.addWidget(steps_label)
        steps_row.addStretch(1)
        self.steps_slider = AngleSliderLike(0.01, 1.00, self.settings['steps'], self.on_steps_changed)
        steps_row.addWidget(self.steps_slider)
        layout.addLayout(steps_row)
        layout.addStretch(1)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(container)
        self.update_preview()

    def load_settings(self):
        try:
            if os.path.exists(self.cfg_path):
                with open(self.cfg_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        if '=' in line:
                            k, v = line.strip().split('=', 1)
                            if k in self.settings:
                                self.settings[k] = float(v)
        except Exception:
            pass

    def save_settings(self):
        try:
            with open(self.cfg_path, 'w', encoding='utf-8') as f:
                for k, v in self.settings.items():
                    f.write(f"{k}={v}\n")
        except Exception:
            pass

    def on_speed_changed(self, value):
        self.settings['speed'] = value
        self.save_settings()
        self.update_preview()

    def on_saturation_changed(self, value):
        self.settings['saturation'] = value
        self.save_settings()
        self.update_preview()

    def on_brightness_changed(self, value):
        self.settings['brightness'] = value
        self.save_settings()
        self.update_preview()

    def on_steps_changed(self, value):
        self.settings['steps'] = value
        self.save_settings()
        # steps не влияет на preview

    def update_preview(self):
        self.preview.set_params(
            speed=self.settings['speed'],
            saturation=self.settings['saturation'],
            brightness=self.settings['brightness']
        )
        self.preview.update()

class GradientPreviewWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(32)
        self.speed = 0.5
        self.saturation = 1.0
        self.brightness = 1.0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.update)
        self._timer.start(40)
        # self._hue = 0.0  # больше не нужен

    def set_params(self, speed, saturation, brightness):
        self.speed = speed
        self.saturation = saturation
        self.brightness = brightness

    def paintEvent(self, event):
        import time
        import colorsys
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        # Считаем hue по глобальному времени, как в rgb_utils.py
        t = time.time() * self.speed * 50 % 360
        hue = (t % 360) / 360.0
        r, g, b = colorsys.hsv_to_rgb(hue, self.saturation, self.brightness)
        color = QColor(int(r * 255), int(g * 255), int(b * 255))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(color)
        painter.drawRoundedRect(0, 0, self.width(), self.height(), 10, 10)

class GradientParamSlider(QHBoxLayout):
    def __init__(self, label, min_val, max_val, value, on_change):
        super().__init__()
        self.setContentsMargins(0, 0, 0, 0)
        self.setSpacing(8)
        self.label = QLabel(label)
        self.label.setFont(get_arial_greek_font(11, QFont.Weight.Normal))
        self.label.setStyleSheet("color: #FFFFFF;")
        self.addWidget(self.label)
        self.addStretch(1)
        self.slider = AngleSliderLike(min_val, max_val, value, on_change)
        self.addWidget(self.slider)
        # value_label удалён, значение теперь рисуется внутри слайдера
        # self.value_label = QLabel(f"{value:.2f}")
        # self.value_label.setFont(QFont("Arial Greek", 11, QFont.Weight.Normal))
        # self.value_label.setStyleSheet("color: #FFFFFF;")
        # self.value_label.setFixedWidth(44)
        # self.value_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        # self.addWidget(self.value_label)
        # self.slider.valueChanged.connect(self.update_value_label)
    # def update_value_label(self, value):
    #     self.value_label.setText(f"{value:.2f}")

class AngleSliderLike(QWidget):
    valueChanged = pyqtSignal(float)
    def __init__(self, min_val, max_val, value, on_change):
        super().__init__()
        self.setFixedSize(120, 26)
        self.min_val = min_val
        self.max_val = max_val
        self.value = value
        self.on_change = on_change
        self.dragging = False
        self.setMouseTracking(True)
        self._hover_anim = 0.0
        self._rgb_timer = QTimer(self)
        self._rgb_timer.timeout.connect(self._animate)
        self._rgb_timer.start(40)
    def _animate(self):
        target = 1.0 if self.dragging or self.underMouse() else 0.0
        speed = 0.08
        if self._hover_anim < target:
            self._hover_anim = min(self._hover_anim + speed, 1.0)
        elif self._hover_anim > target:
            self._hover_anim = max(self._hover_anim - speed, 0.0)
        self.update()
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.update_value(event.pos().x())
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = False
    def mouseMoveEvent(self, event):
        if self.dragging:
            self.update_value(event.pos().x())
    def enterEvent(self, event):
        self.update()
    def leaveEvent(self, event):
        if not self.dragging:
            self.update()
    def update_value(self, x):
        x = max(0, min(x, self.width()))
        self.value = round((x / self.width()) * (self.max_val - self.min_val) + self.min_val, 2)
        self.value = max(self.min_val, min(self.max_val, self.value))
        self.on_change(self.value)
        self.valueChanged.emit(self.value)
        self.update()
    def paintEvent(self, event):
        from rgb_utils import load_rgb_settings
        global_rgb_color = globals().get('global_rgb_color', (255, 0, 0))
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        base_bg = QColor("#252525")
        rgb_settings = load_rgb_settings()
        saturation = rgb_settings.get('saturation', 1.0)
        brightness = rgb_settings.get('brightness', 1.0)
        r, g, b = global_rgb_color
        # --- RGB hover фон ---
        dark_rgb = QColor(r, g, b)
        h, s, v, _ = dark_rgb.getHsv()
        dark_rgb.setHsv(h if h is not None else 0, int(saturation * 180), int(brightness * 60))
        t = 0.55 * self._hover_anim
        bg_color = QColor(
            int(base_bg.red() * (1 - t) + dark_rgb.red() * t),
            int(base_bg.green() * (1 - t) + dark_rgb.green() * t),
            int(base_bg.blue() * (1 - t) + dark_rgb.blue() * t)
        )
        # --- Рисуем фон ---
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(bg_color)
        painter.drawRoundedRect(1, 1, self.width() - 2, self.height() - 2, 6, 6)
        # --- RGB рамка ---
        rgb_color = QColor(r, g, b)
        h, s, v, _ = rgb_color.getHsv()
        rgb_color.setHsv(h if h is not None else 0, int(saturation * 200), int(brightness * 120))
        base_color = QColor("#232228")
        border_color = QColor(
            int(base_color.red() * (1 - self._hover_anim) + rgb_color.red() * self._hover_anim),
            int(base_color.green() * (1 - self._hover_anim) + rgb_color.green() * self._hover_anim),
            int(base_color.blue() * (1 - self._hover_anim) + rgb_color.blue() * self._hover_anim)
        )
        pen = QPen(border_color)
        pen.setWidth(2)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(1, 1, self.width() - 2, self.height() - 2, 6, 6)
        # --- Индикатор ---
        margin = 4
        slider_width = self.width() - 2 * margin
        x = int((self.value - self.min_val) * slider_width / (self.max_val - self.min_val)) + margin
        base_indicator = QColor("#606060")
        rgb_indicator = QColor(r, g, b)
        h, s, v, _ = rgb_indicator.getHsv()
        rgb_indicator.setHsv(h if h is not None else 0, int(saturation * 255), int(brightness * 255))
        indicator_color = QColor(
            int(base_indicator.red() * (1 - self._hover_anim) + rgb_indicator.red() * self._hover_anim),
            int(base_indicator.green() * (1 - self._hover_anim) + rgb_indicator.green() * self._hover_anim),
            int(base_indicator.blue() * (1 - self._hover_anim) + rgb_indicator.blue() * self._hover_anim)
        )
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(indicator_color)
        painter.drawRoundedRect(x - 2, 2, 4, self.height() - 4, 3, 3)
        # --- Значение (в процентах) ---
        painter.setPen(QColor("#FFFFFF"))
        font = get_arial_greek_font(11, QFont.Weight.Normal)
        painter.setFont(font)
        percent = int(round(self.value * 100))
        value_text = f"{percent}%"
        text_rect = self.rect()
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, value_text)

class KillSoundPopup(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(260, 90)  # увеличили высоту для сепаратора
        container = QWidget(self)
        container.setStyleSheet("""
            background-color: rgba(13, 13, 13, 100);
            border: 2px solid rgba(35, 34, 40, 150);
            border-radius: 10px;
        """)
        container.setFixedSize(self.size())
        layout = QVBoxLayout(container)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)
        # --- Volume row ---
        volume_row = QHBoxLayout()
        volume_row.setContentsMargins(0, 0, 0, 0)
        volume_row.setSpacing(8)
        volume_label = QLabel("Volume")
        volume_label.setFont(get_arial_greek_font(11, QFont.Weight.Normal))
        volume_label.setStyleSheet("color: #FFFFFF; background: none; border: none;")
        volume_row.addWidget(volume_label)
        volume_row.addStretch(1)
        # Load value from file
        try:
            with open("killsound_volume.flag", "r", encoding="utf-8") as f:
                value = float(f.read().strip())
        except Exception:
            value = 1.0
        self.volume_slider = AngleSliderLike(0.00, 1.00, value, self.on_volume_changed)
        volume_row.addWidget(self.volume_slider)
        layout.addLayout(volume_row)
        # --- Separator ---
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: #232228; margin: 4px 0px; border: none;")
        separator.setFixedHeight(1)
        layout.addWidget(separator)
        # --- Sound Path row ---
        path_row = QHBoxLayout()
        path_row.setContentsMargins(0, 0, 0, 0)
        path_row.setSpacing(8)
        path_label = QLabel("Sound Path")
        path_label.setFont(get_arial_greek_font(11, QFont.Weight.Normal))
        path_label.setStyleSheet("color: #FFFFFF; background: none; border: none;")
        path_row.addWidget(path_label)
        path_row.addStretch(1)
        self.path_input = QLineEdit()
        self.path_input.setFont(get_arial_greek_font(11))
        self.path_input.setStyleSheet("""
            QLineEdit {
                background-color: #252525;
                color: #ffffff;
                border: 1px solid #232228;
                border-radius: 6px;
                padding: 4px 8px;
            }
            QLineEdit:focus {
                border: 1px solid #303030;
            }
        """)
        self.path_input.setPlaceholderText("Enter sound path...")
        self.path_input.textChanged.connect(self.save_path)
        # Load value from file
        try:
            with open("killsound_path.flag", "r", encoding="utf-8") as f:
                path_val = f.read().strip()
                self.path_input.setText(path_val)
        except Exception:
            pass
        self.path_input.setFixedWidth(120)
        path_row.addWidget(self.path_input)
        layout.addLayout(path_row)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(container)
    def on_volume_changed(self, value):
        try:
            with open("killsound_volume.flag", "w", encoding="utf-8") as f:
                f.write(f"{value:.2f}")
        except Exception:
            pass
    def save_path(self):
        try:
            path = self.path_input.text().replace('"', '')
            with open("killsound_path.flag", "w", encoding="utf-8") as f:
                f.write(path)
        except Exception:
            pass

# --- AutoReportPopup ---
class AutoReportPopup(QWidget):
    TEAM_OPTIONS = ["T", "CT"]
    COLOR_OPTIONS = [
        ("Orange", "#e6802a"),
        ("Yellow", "#f1e441"),
        ("Purple", "#bd2c96"),
        ("Green", "#009e80"),
        ("Blue", "#88cef5"),
    ]
    def load_weapon_font(self):
        font_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "weapon.ttf")
        if os.path.exists(font_path):
            font_id = QFontDatabase.addApplicationFont(font_path)
            families = QFontDatabase.applicationFontFamilies(font_id)
            if families:
                return QFont(families[0], 13)
        return QFont("Arial", 13)
    def create_team_button(self):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        self.team_label = QLabel(self.team)
        self.team_label.setFont(get_arial_greek_font(11, QFont.Weight.Normal))
        self.team_label.setStyleSheet("color: #ead28b;" if self.team == "T" else "color: #b6d4ee;")
        layout.addWidget(self.team_label)
        self.team_icon = QLabel("$" if self.team == "T" else "!")
        self.team_icon.setFont(self.load_weapon_font())  # Исправлено название метода
        self.team_icon.setStyleSheet("color: #ead28b;" if self.team == "T" else "color: #b6d4ee;")
        layout.addWidget(self.team_icon)
        widget.setFixedSize(60, 26)
        widget.setStyleSheet("""
            background-color: #252525;
            border-radius: 6px;
        """)
        widget.installEventFilter(self)  # Используем eventFilter вместо mousePressEvent
        return widget
    def team_button_click(self, event):
        self.toggle_team()
    def update_team_button(self):
        self.team_label.setText(self.team)
        self.team_label.setStyleSheet("color: #ead28b;" if self.team == "T" else "color: #b6d4ee;")
        self.team_icon.setText("$" if self.team == "T" else "!")
        self.team_icon.setStyleSheet("color: #ead28b;" if self.team == "T" else "color: #b6d4ee;")
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(260, 150)
        self.flag_path = "autoreport.flag"
        self.team = "T"
        self.color = "Orange"
        self.bind = "None"
        self.listening = False
        self._color_anim = None
        self._color_anim_value = self.get_color_rgb(self.color)
        self.load_flag()
        container = QWidget(self)
        container.setStyleSheet("""
            background-color: rgba(13, 13, 13, 100);
            border: 2px solid rgba(35, 34, 40, 150);
            border-radius: 10px;
        """)
        container.setFixedSize(self.size())
        layout = QVBoxLayout(container)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)
        # --- Team row ---
        team_row = QHBoxLayout()
        team_label = QLabel("Player Team")
        team_label.setFont(get_arial_greek_font(11, QFont.Weight.Normal))
        team_label.setStyleSheet("color: #FFFFFF; background: none; border: none;")
        team_row.addWidget(team_label)
        team_row.addStretch(1)
        self.team_button = self.create_team_button()
        team_row.addWidget(self.team_button)
        layout.addLayout(team_row)
        # --- Color row ---
        color_row = QHBoxLayout()
        color_label = QLabel("Player Color")
        color_label.setFont(get_arial_greek_font(11, QFont.Weight.Normal))
        color_label.setStyleSheet("color: #FFFFFF; background: none; border: none;")
        color_row.addWidget(color_label)
        color_row.addStretch(1)
        self.color_button = QPushButton(self.color)
        self.color_button.setFixedSize(90, 26)
        self.color_button.setFont(get_arial_greek_font(11, QFont.Weight.Normal))
        self.color_button.setStyleSheet(self.color_button_style(self.color))
        self.color_button.clicked.connect(self.toggle_color)
        color_row.addWidget(self.color_button)
        layout.addLayout(color_row)
        # --- Separator ---
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: #232228; margin: 4px 0px; border: none;")
        separator.setFixedHeight(1)
        layout.addWidget(separator)
        # --- Hotkey row ---
        bind_row = QHBoxLayout()
        bind_label = QLabel("Hotkey")
        bind_label.setFont(get_arial_greek_font(11, QFont.Weight.Normal))
        bind_label.setStyleSheet("color: #FFFFFF; background: none; border: none;")
        bind_row.addWidget(bind_label)
        bind_row.addStretch(1)
        self.bind_button = QPushButton(self.bind)
        self.bind_button.setFixedSize(100, 26)
        self.bind_button.setFont(get_arial_greek_font(11, QFont.Weight.Normal))
        self.bind_button.setStyleSheet("""
            QPushButton {
                background-color: #252525;
                color: #ffffff;
                border-radius: 6px;
                padding: 0 12px;
                text-align: center;
                font-family: 'Arial Greek', Arial, sans-serif;
            }
            QPushButton:hover {
                background-color: #303030;
                border: 1px solid #232228;
            }
            QPushButton:pressed {
                background-color: #202020;
            }
        """)
        self.bind_button.clicked.connect(self.start_listen_key)
        bind_row.addWidget(self.bind_button)
        layout.addLayout(bind_row)
        # --- Main layout ---
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(container)
        self.update_flag()
    def get_color_rgb(self, color_name):
        color_map = dict(self.COLOR_OPTIONS)
        color = color_map.get(color_name, "#e6802a")
        from PyQt6.QtGui import QColor
        return QColor(color)
    def color_button_style(self, color_name):
        color_map = dict(self.COLOR_OPTIONS)
        color = color_map.get(color_name, "#e6802a")
        return f"""
            QPushButton {{
                background-color: {color};
                color: #232228;
                border-radius: 6px;
                padding: 0 12px;
                text-align: center;
                font-family: 'Arial Greek', Arial, sans-serif;
            }}
            QPushButton:hover {{
                border: 1px solid #232228;
            }}
            QPushButton:pressed {{
                background-color: #202020;
                color: #ffffff;
            }}
        """
    def toggle_team(self):
        idx = self.TEAM_OPTIONS.index(self.team)
        self.team = self.TEAM_OPTIONS[(idx + 1) % len(self.TEAM_OPTIONS)]
        self.update_team_button()
        self.update_flag()
    def toggle_color(self):
        idx = [c[0] for c in self.COLOR_OPTIONS].index(self.color)
        self.color = self.COLOR_OPTIONS[(idx + 1) % len(self.COLOR_OPTIONS)][0]
        self.color_button.setText(self.color)
        self.color_button.setStyleSheet(self.color_button_style(self.color))
        self.update_flag()
    def start_listen_key(self):
        self.listening = True
        self.bind_button.setText("Press any key...")
        self.grabKeyboard()
    def keyPressEvent(self, event):
        if self.listening:
            if event.key() == Qt.Key.Key_Escape:
                self.bind = "None"
            else:
                key = event.text().upper() if event.text() else ""
                ru_to_en = {
                    'Ф': 'A', 'И': 'B', 'С': 'C', 'В': 'D', 'У': 'E', 'А': 'F', 'П': 'G', 'Р': 'H', 'Ш': 'I', 'О': 'J',
                    'Л': 'K', 'Д': 'L', 'Ь': 'M', 'Т': 'N', 'Щ': 'O', 'З': 'P', 'Й': 'Q', 'К': 'R', 'Ы': 'S', 'Е': 'T',
                    'Г': 'U', 'М': 'V', 'Ц': 'W', 'Ч': 'X', 'Н': 'Y', 'Я': 'Z',
                    'ф': 'A', 'и': 'B', 'с': 'C', 'в': 'D', 'у': 'E', 'а': 'F', 'п': 'G', 'р': 'H', 'ш': 'I', 'о': 'J',
                    'л': 'K', 'д': 'L', 'ь': 'M', 'т': 'N', 'щ': 'O', 'з': 'P', 'й': 'Q', 'к': 'R', 'ы': 'S', 'е': 'T',
                    'г': 'U', 'м': 'V', 'ц': 'W', 'ч': 'X', 'н': 'Y', 'я': 'Z',
                }
                if key in ru_to_en:
                    key = ru_to_en[key]
                if not key:
                    qt_key = event.key()
                    key_name = Qt.Key(qt_key).name if hasattr(Qt.Key(qt_key), "name") else str(qt_key)
                    key_name = key_name.replace("Key_", "").upper()
                    key = key_name
                self.bind = key
            self.listening = False
            self.bind_button.setText(self.bind)
            self.releaseKeyboard()
            self.update_flag()
        else:
            super().keyPressEvent(event)
    def load_flag(self):
        try:
            if os.path.exists(self.flag_path):
                with open(self.flag_path, "r", encoding="utf-8") as f:
                    lines = f.read().split("\n")
                    for line in lines:
                        if line.startswith("team:"):
                            self.team = line.split(":", 1)[1].strip()
                        elif line.startswith("color:"):
                            self.color = line.split(":", 1)[1].strip()
                        elif line.startswith("bind:"):
                            self.bind = line.split(":", 1)[1].strip()
        except Exception:
            pass
    def update_flag(self):
        try:
            with open(self.flag_path, "w", encoding="utf-8") as f:
                f.write(f"team: {self.team}\ncolor: {self.color}\nbind: {self.bind}\n")
        except Exception:
            pass
        self.bind_button.setText(self.bind)
        self.update_team_button()
        self.color_button.setText(self.color)
        self.color_button.setStyleSheet(self.color_button_style(self.color))
    def team_button_style(self, team):
        color = "#ead28b" if team == "T" else "#b6d4ee"
        return f"""
            QPushButton {{
                background-color: #252525;
                color: {color};
                border-radius: 6px;
                padding: 0 12px;
                text-align: center;
                font-family: 'Arial Greek', Arial, sans-serif;
            }}
            QPushButton:hover {{
                background-color: #303030;
                border: 1px solid #232228;
            }}
            QPushButton:pressed {{
                background-color: #202020;
            }}
        """
    def eventFilter(self, obj, event):
        # Для кнопки выбора команды в AutoReportPopup
        from PyQt6.QtCore import QEvent
        if hasattr(self, 'team_button') and obj is self.team_button and event.type() == QEvent.Type.MouseButtonPress:
            self.team_button_click(event)
            return True
        # Для GearIcon и других, если нужно, можно добавить аналогично
        return super().eventFilter(obj, event)

class FontChangerPopup(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(260, 130)
        container = QWidget(self)
        container.setStyleSheet("""
            background-color: rgba(13, 13, 13, 100);
            border: 2px solid rgba(35, 34, 40, 150);
            border-radius: 10px;
        """)
        container.setFixedSize(self.size())
        layout = QVBoxLayout(container)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)
        # Choose Font
        choose_btn = QPushButton("Choose Font")
        choose_btn.setFont(get_arial_greek_font(11, QFont.Weight.Normal))
        choose_btn.setStyleSheet("""
            QPushButton { background-color: #252525; color: #ffffff; border-radius: 6px; padding: 0 12px; }
            QPushButton:hover { background-color: #303030; border: 1px solid #232228; }
            QPushButton:pressed { background-color: #202020; }
        """)
        choose_btn.clicked.connect(self.choose_font)
        layout.addWidget(choose_btn)
        # Reset Font
        reset_btn = QPushButton("Reset Font")
        reset_btn.setFont(get_arial_greek_font(11, QFont.Weight.Normal))
        reset_btn.setStyleSheet(choose_btn.styleSheet())
        reset_btn.clicked.connect(self.reset_font)
        layout.addWidget(reset_btn)
        # Restart CS2
        restart_btn = QPushButton("Restart CS2")
        restart_btn.setFont(get_arial_greek_font(11, QFont.Weight.Normal))
        restart_btn.setStyleSheet(choose_btn.styleSheet())
        restart_btn.clicked.connect(self.restart_game)
        layout.addWidget(restart_btn)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(container)
    def choose_font(self):
        import os
        from PyQt6.QtWidgets import QFileDialog, QMessageBox
        file_dialog = QFileDialog(self)
        file_dialog.setNameFilter("Font Files (*.ttf *.otf)")
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        if file_dialog.exec():
            selected = file_dialog.selectedFiles()
            if selected:
                font_path = selected[0]
                import shutil
                dest_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "CustomFont"))
                src_path = os.path.abspath(font_path)
                if src_path == dest_path:
                    QMessageBox.information(self, "Font", "Этот шрифт уже выбран.")
                    return
                try:
                    shutil.copy(src_path, dest_path)
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to copy font: {e}")
                    return
                # --- Работа с папкой Steam/csgo/panorama/fonts ---
                try:
                    from steam_path_utils import find_csgo_cfg_path
                    import shutil
                    from fontconf_utils import generate_fonts_conf
                    # Получаем путь к cfg, поднимаемся до csgo
                    cfg_path = find_csgo_cfg_path()
                    if not cfg_path:
                        QMessageBox.critical(self, "Error", "CS:GO cfg path not found!")
                        return
                    csgo_path = os.path.dirname(cfg_path)
                    panorama_path = os.path.join(csgo_path, "panorama")
                    fonts_path = os.path.join(panorama_path, "fonts")
                    fonts1_path = os.path.join(panorama_path, "fonts1")
                    # Если fonts1 уже есть, удаляем fonts и создаём новую fonts
                    if os.path.exists(fonts1_path):
                        if os.path.exists(fonts_path):
                            shutil.rmtree(fonts_path)
                        os.makedirs(fonts_path, exist_ok=True)
                    else:
                        # Если fonts1 нет, переименовываем fonts -> fonts1, создаём fonts
                        if os.path.exists(fonts_path):
                            os.rename(fonts_path, fonts1_path)
                        os.makedirs(fonts_path, exist_ok=True)
                    # Копируем выбранный шрифт в новую папку fonts
                    font_dst_path = os.path.join(fonts_path, os.path.basename(src_path))
                    shutil.copy(src_path, font_dst_path)
                    # Получаем имя шрифта (без расширения)
                    from PyQt6.QtGui import QFontDatabase
                    font_id = QFontDatabase.addApplicationFont(src_path)
                    families = QFontDatabase.applicationFontFamilies(font_id)
                    font_name = families[0] if families else os.path.splitext(os.path.basename(src_path))[0]
                    # Генерируем fonts.conf
                    fonts_conf_path = os.path.join(fonts_path, "fonts.conf")
                    generate_fonts_conf(fonts_conf_path, font_name, os.path.basename(src_path))
                    # --- Работа с core/panorama/fonts/conf.d ---
                    core_fonts_path = os.path.abspath(os.path.join(csgo_path, "..", "core", "panorama", "fonts"))
                    confd_path = os.path.join(core_fonts_path, "conf.d")
                    confd1_path = os.path.join(core_fonts_path, "conf.d1")
                    import shutil
                    if os.path.exists(confd1_path):
                        if os.path.exists(confd_path):
                            shutil.rmtree(confd_path)
                        os.makedirs(confd_path, exist_ok=True)
                    else:
                        if os.path.exists(confd_path):
                            os.rename(confd_path, confd1_path)
                        os.makedirs(confd_path, exist_ok=True)
                    # Создаём 42-repl-global.conf с нужным FONTNAME
                    from fontconf_utils import generate_42repl_conf
                    repl_conf_path = os.path.join(confd_path, "42-repl-global.conf")
                    generate_42repl_conf(repl_conf_path, font_name)
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to prepare csgo fonts folder: {e}")
                    return
                QMessageBox.information(self, "Font Changed", "Font successfully changed! Restart the game to apply.")
    def reset_font(self):
        from PyQt6.QtWidgets import QMessageBox
        import os
        import shutil
        from steam_path_utils import find_csgo_cfg_path
        try:
            cfg_path = find_csgo_cfg_path()
            if not cfg_path:
                QMessageBox.critical(self, "Error", "CS:GO cfg path not found!")
                return
            csgo_path = os.path.dirname(cfg_path)
            panorama_path = os.path.join(csgo_path, "panorama")
            fonts_path = os.path.join(panorama_path, "fonts")
            fonts1_path = os.path.join(panorama_path, "fonts1")
            # Удаляем fonts
            if os.path.exists(fonts_path):
                shutil.rmtree(fonts_path)
            # Переименовываем fonts1 -> fonts
            if os.path.exists(fonts1_path):
                os.rename(fonts1_path, fonts_path)
            # Работа с core/panorama/fonts/conf.d
            core_fonts_path = os.path.abspath(os.path.join(csgo_path, "..", "core", "panorama", "fonts"))
            confd_path = os.path.join(core_fonts_path, "conf.d")
            confd1_path = os.path.join(core_fonts_path, "conf.d1")
            # Удаляем conf.d
            if os.path.exists(confd_path):
                shutil.rmtree(confd_path)
            # Переименовываем conf.d1 -> conf.d
            if os.path.exists(confd1_path):
                os.rename(confd1_path, confd_path)
            QMessageBox.information(self, "Reset Font", "Font and config reset to original.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to reset font: {e}")
    def restart_game(self):
        from PyQt6.QtWidgets import QMessageBox
        import subprocess
        import time
        import os
        try:
            # Завершаем все процессы cs2.exe
            subprocess.call(["taskkill", "/F", "/IM", "cs2.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(1)
            # Запускаем CS2 через Steam
            # Найти путь к Steam
            steam_path = None
            possible_roots = [
                os.environ.get('PROGRAMFILES(X86)', 'C:\\Program Files (x86)'),
                os.environ.get('PROGRAMFILES', 'C:\\Program Files'),
                os.environ.get('LOCALAPPDATA', ''),
                'C:\\', 'D:\\', 'E:\\', 'F:\\'
            ]
            for root in possible_roots:
                candidate = os.path.join(root, 'Steam', 'steam.exe')
                if os.path.isfile(candidate):
                    steam_path = candidate
                    break
            if not steam_path:
                QMessageBox.critical(self, "Error", "Steam not found! Запустите CS2 вручную.")
                return
            # Запуск CS2 через Steam (app id 730)
            subprocess.Popen([steam_path, "-applaunch", "730"])
            QMessageBox.information(self, "Restart Game", "CS2 Restarted through Steam!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Не удалось перезапустить CS2: {e}")

# --- HIDE CONSOLE ON WINDOWS (if run as script) ---
if sys.platform == "win32":
    try:
        import ctypes
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
    except Exception:
        pass

# --- BEAUTIFUL CONSOLE OUTPUT IF CONSOLE IS VISIBLE ---
def print_welcome():
    # ANSI escape codes for colors
    PURPLE = "\033[38;2;202;101;255m"
    CYAN = "\033[38;2;113;255;219m"
    RESET = "\033[0m"
    print(PURPLE + r"""
   ____        _____           _       _     _     
  |  _ \ _   _| ____|_ __ ___ (_) __ _| |__ | |__  
  | |_) | | | |  _| | '_ ` _ \| |/ _` | '_ \| '_ \ 
  |  __/| |_| | |___| | | | | | | (_| | |_) | | | |
  |_|    \__, |_____|_| |_| |_|_|\__,_|_.__/|_| |_|
         |___/                                     

PyScripts Tweaks for CS2 (⌒▽⌒)

- Quality of life scripts for CS2
- Custom binds, visuals, automation, and more!
- Free, open, and friendly for everyone
""" + RESET)
    print(CYAN + r"""
Support development with a skin donation (⌒▽⌒)
Trade link: https://steamcommunity.com/tradeoffer/new/?partner=1570577878&token=1WuPKdBZ
""" + RESET)

if __name__ == "__main__":
    # Only print welcome if running as main script and console is visible
    if sys.stdout.isatty():
        print_welcome()

    app = QApplication(sys.argv)

    # Глобальный таймер для синхронизации RGB
    rgb_timer = QTimer()
    rgb_timer.timeout.connect(update_global_rgb_color)
    rgb_timer.start(40)
    
    window = ScriptGUI()
    window.show()

    # Запускаем pipe сервер в отдельном потоке
    pipe_server_thread = threading.Thread(target=menu_pipe_server, daemon=True)
    pipe_server_thread.start()

    sys.exit(app.exec())