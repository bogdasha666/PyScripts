import sys
import json
import threading
from pathlib import Path
from PySide6.QtCore import Qt, QTimer, QRectF, Property, QPoint
from PySide6.QtGui import QPainter, QColor, QPixmap, QPainterPath
from PySide6.QtWidgets import QApplication, QWidget
from datetime import datetime
import win32file
from multiprocessing.connection import Client

PIPE_NAME = r'\\.\pipe\gsi_pipe'
MENU_PIPE_NAME = r'\\.\pipe\menu_visibility_pipe'

class BombTimerOverlay(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.bomb_planted = False
        self.bomb_planted_time = None
        self.total_time = 40  # Bomb timer is 40 seconds
        self.menu_visible = True  # Default to visible
        self.is_bomb_timer_started = False  # Статическая переменная как в C++
        self.timer_auto_reset = False  # Флаг для предотвращения многократного сброса

        # Set up the timer for UI updates
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update)
        self.update_timer.start(16)  # ~64 FPS (как в C++: 15625 микросекунд)

        # Set up menu visibility check timer
        self.menu_check_timer = QTimer()
        self.menu_check_timer.timeout.connect(self.check_menu_visibility)
        self.menu_check_timer.start(16)  # Check every 16ms for instant updates

        # Load C4 image
        try:
            self.c4_image = QPixmap("c4.png")
            self.c4_image = self.c4_image.scaledToHeight(45, Qt.SmoothTransformation)  # Reduced from 49 to 45
        except Exception as e:
            print(f"Error loading c4.png: {e}")
            self.c4_image = QPixmap(32, 32)
            self.c4_image.fill(QColor(255, 0, 0))

        self.cs_font_family = "Arial Greek"  # Используем Arial Greek для шрифта
        print("BombTimer initialized!")

        # Start pipe reading in a separate thread
        threading.Thread(target=self.read_pipe_loop, daemon=True).start()

    def initUI(self):
        self.setWindowTitle('Bomb Timer')
        self.setGeometry(100, 100, 147, 68)  # Reduced size by 1.09x
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.show()

    def check_menu_visibility(self):
        try:
            with Client(MENU_PIPE_NAME, 'AF_PIPE') as conn:
                state = conn.recv()
                self.menu_visible = (state == "VISIBLE")
                self.update_visibility()
        except Exception as e:
            print(f"Error checking menu visibility: {e}")

    def update_visibility(self):
        # Show overlay if menu is visible or bomb is planted
        should_show = self.menu_visible or self.bomb_planted
        if should_show and not self.isVisible():
            self.show()
        elif not should_show and self.isVisible():
            self.hide()

    def reset_timer(self):
        """Принудительный сброс таймера бомбы"""
        if self.bomb_planted or self.bomb_planted_time is not None:
            print(f"[BombTimer] Принудительный сброс таймера")
        self.bomb_planted = False
        self.bomb_planted_time = None
        self.is_bomb_timer_started = False
        self.timer_auto_reset = False  # Сбросить флаг при ручном сбросе
        self.update_visibility()

    def read_pipe_loop(self):
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
                msg = data.decode('utf-8')
                self.handle_pipe_message(msg)
            except Exception as e:
                # Pipe might not be ready yet, just retry
                import time
                time.sleep(1)

    def handle_pipe_message(self, msg):
        try:
            data = json.loads(msg)
            bomb_status = data.get('round', {}).get('bomb', None)
            
            # Логика из BombTime.cpp
            if bomb_status == 'planted':  # globals::bombState
                if not self.is_bomb_timer_started:
                    self.bomb_planted_time = datetime.now()
                    self.is_bomb_timer_started = True
                    self.bomb_planted = True
                self.update_visibility()
            else:
                # Проверяем, не была ли бомба установлена недавно
                if self.is_bomb_timer_started and self.bomb_planted_time:
                    elapsed = (datetime.now() - self.bomb_planted_time).total_seconds()
                    # Если прошло меньше 45 секунд, продолжаем показывать таймер
                    if elapsed < 45:
                        self.bomb_planted = True
                        self.update_visibility()
                        return
                
                # Сбрасываем только если прошло достаточно времени или явный статус
                if bomb_status in ('defused', 'exploded'):
                    self.bomb_planted = False
                    self.is_bomb_timer_started = False
                    self.bomb_planted_time = None
                    self.update_visibility()
        except Exception as e:
            print(f"Error parsing pipe message: {e}")
            self.bomb_planted = False
            self.is_bomb_timer_started = False
            self.bomb_planted_time = None
            self.update_visibility()

    def paintEvent(self, event):
        try:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            path = QPainterPath()
            rect = self.rect()
            radius = 10.0
            path.addRoundedRect(rect, radius, radius)
            painter.setClipPath(path)
            painter.fillRect(rect, QColor(0, 0, 0))
            border_pen = painter.pen()
            border_pen.setWidth(3)
            border_pen.setColor(QColor(60, 60, 60))
            painter.setPen(border_pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawPath(path)
            painter.drawPixmap(16, (self.height() - self.c4_image.height()) // 2, self.c4_image)
            
            # Логика времени из BombTime.cpp
            if self.is_bomb_timer_started and self.bomb_planted_time:
                elapsed_ms = (datetime.now() - self.bomb_planted_time).total_seconds() * 1000
                remaining_ms = 40000 - elapsed_ms  # Как в C++: 40000 - elapsed_ms
                if remaining_ms <= 0:
                    remaining_ms = 0.0  # Как в C++: globals::bombTime = 0.0l
                    if not self.timer_auto_reset:
                        self.timer_auto_reset = True
                        self.reset_timer()
                else:
                    self.timer_auto_reset = False
                remaining = remaining_ms / 1000  # Конвертируем в секунды для отображения
            else:
                remaining = self.total_time
                self.timer_auto_reset = False
            
            timer_size = min(self.height() - 8, 44)
            timer_x = self.width() - timer_size - 16
            timer_y = (self.height() - timer_size) // 2
            # Цвета и кольцо — оставить как было
            if remaining > 30:
                ring_color = QColor(0, 255, 0)
            elif remaining > 20:
                t = (30 - remaining) / 10.0
                r = round(0 + (255 - 0) * t)
                g = 255
                b = 0
                ring_color = QColor(r, g, b)
            elif remaining > 10:
                t = (20 - remaining) / 10.0
                r = 255
                g = round(255 + (77 - 255) * t)
                b = 0
                ring_color = QColor(r, g, b)
            else:
                ring_color = QColor(255, 77, 0)
            pen = painter.pen()
            pen.setWidth(3)
            pen.setColor(QColor(29, 29, 29))
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(timer_x, timer_y, timer_size, timer_size)
            pen.setColor(ring_color)
            pen.setWidth(4)
            painter.setPen(pen)
            progress = max(0, min(1, remaining / self.total_time))
            span = int(360 * progress * 16)
            painter.drawArc(timer_x, timer_y, timer_size, timer_size, 90 * 16, span)
            painter.setPen(ring_color)
            font = painter.font()
            font.setFamily(self.cs_font_family)
            font.setPointSize(8)
            font.setBold(True)
            painter.setFont(font)
            text = f"{remaining:.1f}"
            text_rect = QRectF(timer_x, timer_y, timer_size, timer_size)
            painter.drawText(text_rect, Qt.AlignCenter, text)
        except Exception as e:
            print(f"Error in paintEvent: {e}")

    def mousePressEvent(self, event):
        self.old_pos = event.globalPos()

    def mouseMoveEvent(self, event):
        delta = QPoint(event.globalPos() - self.old_pos)
        self.move(self.x() + delta.x(), self.y() + delta.y())
        self.old_pos = event.globalPos()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = BombTimerOverlay()
    sys.exit(app.exec())