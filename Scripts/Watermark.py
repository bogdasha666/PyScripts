import sys
import json
import time
import threading
import win32file
import win32pipe
import pywintypes
import re
import win32api
import win32con
from datetime import datetime, timezone, timedelta
from PySide6.QtWidgets import QApplication, QWidget, QLabel
from PySide6.QtCore import Qt, QTimer, QPoint
from PySide6.QtGui import QPainter, QColor, QFont, QPen, QFontDatabase, QFontInfo
from rgb_utils import get_rgb_color, synced_rgb
import os
from steam_path_utils import find_csgo_log_path  # type: ignore

PIPE_NAME = r'\\.\pipe\gsi_pipe'
SYS_INFO_KEY = win32con.VK_F21  # F21 key for sys_info command

# --- Font loader for Arial Greek ---
def get_arial_greek_font(point_size=11, weight=QFont.Weight.Normal, italic=False):
    font = QFont("Arial Greek", point_size, weight, italic)
    if QFontInfo(font).family() == "Arial Greek":
        return font
    font_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Arial Greek Regular.ttf")
    if os.path.exists(font_path):
        font_id = QFontDatabase.addApplicationFont(font_path)
        families = QFontDatabase.applicationFontFamilies(font_id)
        if families:
            return QFont(families[0], point_size, weight, italic)
    return QFont("Arial", point_size, weight, italic)

class OverlayWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(363, 32)  # Новый размер окна
        self.move_to_top_right()
        self.drag_pos = None
        self.data = {'player': {'name': 'N/A', 'state': {'ping': 'N/A'}}}
        self.gmt_offset = self.get_gmt_offset()
        self.text = ''
        self.ping_value = 0  # Значение пинга из лога
        self.log_path = find_csgo_log_path()
        if not self.log_path:
            print('[ОШИБКА]: Файл console.log не найден. Проверьте путь установки Steam и CS:GO.')
            exit(1)
        self.update_text()
        self.start_pipe_thread()
        self.start_ping_log_thread()
        self.start_timer()
        self.start_sys_info_thread()

    def move_to_top_right(self):
        screen = QApplication.primaryScreen().geometry()
        self.move(screen.width() - self.width() - 5, 5)

    def get_gmt_offset(self):
        offset_sec = time.localtime().tm_gmtoff if hasattr(time, 'tm_gmtoff') else -time.timezone
        hours = int(offset_sec // 3600)
        return hours

    def start_sys_info_thread(self):
        def sys_info_sender():
            # Initial delay of 10 seconds
            time.sleep(10)
            
            last_update = time.time()
            update_interval = 1.0  # Update every second
            
            while True:
                current_time = time.time()
                if current_time - last_update >= update_interval:
                    # Send sys_info command
                    win32api.keybd_event(SYS_INFO_KEY, 0, 0, 0)  # Key down
                    time.sleep(0.01)  # Small delay
                    win32api.keybd_event(SYS_INFO_KEY, 0, win32con.KEYEVENTF_KEYUP, 0)  # Key up
                    last_update = current_time
                time.sleep(0.015625)  # Same interval as other threads
                
        threading.Thread(target=sys_info_sender, daemon=True).start()

    def start_pipe_thread(self):
        def pipe_reader():
            while True:
                try:
                    handle = win32file.CreateFile(
                        PIPE_NAME,
                        win32file.GENERIC_READ,
                        0, None,
                        win32file.OPEN_EXISTING,
                        0, None)
                    result, data = win32file.ReadFile(handle, 65536)
                    handle.Close()
                    try:
                        if isinstance(data, bytes):
                            self.data = json.loads(data.decode('utf-8'))
                        else:
                            self.data = json.loads(data)
                    except Exception:
                        self.data = {'player': {'name': 'N/A', 'state': {'ping': 'N/A'}}}
                except pywintypes.error:
                    time.sleep(1)
                except Exception:
                    time.sleep(1)
        threading.Thread(target=pipe_reader, daemon=True).start()

    def start_ping_log_thread(self):
        def ping_log_reader():
            last_size = 0
            regex = re.compile(r'latency (\d+) msec')
            while True:
                try:
                    with open(self.log_path, 'r', encoding='utf-8', errors='ignore') as f:
                        f.seek(last_size)
                        lines = f.readlines()
                        last_size = f.tell()
                        for line in lines:
                            if 'latency' in line:
                                match = regex.search(line)
                                if match:
                                    self.ping_value = int(match.group(1))
                except Exception:
                    pass
                time.sleep(0.015625)  # Same interval as in C++ code (15625 microseconds)
        threading.Thread(target=ping_log_reader, daemon=True).start()

    def start_timer(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.on_timer)
        self.timer.start(1000 // 30)  # 30 FPS

    def on_timer(self):
        self.update_text()
        self.update()

    def update_text(self):
        player = self.data.get('player', {})
        name = player.get('name')
        if not name:
            name = player.get('steamid') or player.get('id') or 'N/A'
        ping_str = f'{self.ping_value}ms'
        now = datetime.now(timezone(timedelta(hours=self.gmt_offset)))
        time_str = now.strftime('%H:%M:%S')
        tz_str = f'GMT{self.gmt_offset:+d}'
        self.text = f'〜（ゝ。∂） | {name} | Ping {ping_str} | {time_str} {tz_str}'

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(0, 0, -1, -1)
        border_color = QColor(40, 40, 40)
        bg_color = QColor(0, 0, 0, 220)
        painter.setBrush(bg_color)
        painter.setPen(QPen(border_color, 2))
        painter.drawRoundedRect(rect, 12, 12)
        # Используем один RGB-цвет для всего текста, как в Keystrokes.py
        font = get_arial_greek_font(11, QFont.Weight.Normal)
        painter.setFont(font)
        r, g, b = synced_rgb()
        text_color = QColor(r, g, b)
        painter.setPen(text_color)
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self.text)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self.drag_pos and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self.drag_pos = None

if __name__ == '__main__':
    app = QApplication(sys.argv)
    overlay = OverlayWidget()
    overlay.show()
    sys.exit(app.exec())
