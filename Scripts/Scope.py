import keyboard
from pynput import mouse
import pygetwindow as gw
import threading
import time

import sys
from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtCore import Qt, QTimer, QPoint
from PySide6.QtGui import QPainter, QColor, QPen, QPainterPath
import ctypes

zoomed_in = False
magnifier_minimized = False
overlay = None  # Глобальная переменная для оверлея

class SniperScopeOverlay(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint |
            Qt.FramelessWindowHint |
            Qt.Tool |
            Qt.WindowTransparentForInput |
            Qt.BypassWindowManagerHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.showFullScreen()
        self.visible = False
        self.zoomed = False

        self.repaint_timer = QTimer()
        self.repaint_timer.timeout.connect(self.update)
        self.repaint_timer.start(16)

    def show_scope(self):
        self.visible = True
        self.zoomed = True
        self.show()
        self.update()

    def hide_scope(self):
        self.visible = False
        self.zoomed = False
        self.hide()
        self.update()

    def paintEvent(self, event):
        if not self.visible:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        width = self.width()
        height = self.height()
        center = QPoint(width // 2, height // 2)
        base_radius = int(min(width, height) // 2.5)
        radius = base_radius // 2 if self.zoomed else base_radius

        path = QPainterPath()
        path.addRect(0, 0, width, height)
        path.addEllipse(center, radius, radius)
        painter.setBrush(QColor(0, 0, 0, 200))
        painter.setPen(Qt.NoPen)
        painter.drawPath(path)

        pen = QPen(QColor(0, 0, 0), 1.5)
        painter.setPen(pen)
        painter.drawLine(center.x() - radius, center.y(), center.x() + radius, center.y())
        painter.drawLine(center.x(), center.y() - radius, center.x(), center.y() + radius)

def start_overlay():
    global overlay
    app = QApplication.instance() or QApplication(sys.argv)
    if sys.platform == "win32":
        ctypes.windll.user32.SetProcessDPIAware()
    overlay = SniperScopeOverlay()
    overlay.hide_scope()
    app.exec()

overlay_thread = threading.Thread(target=start_overlay, daemon=True)
overlay_thread.start()
time.sleep(1)

def is_cs2_active():
    win = gw.getActiveWindow()
    if win is None:
        return False
    return 'cs2' in win.title.lower() or 'counter-strike' in win.title.lower()

def minimize_magnifier():
    global magnifier_minimized
    if magnifier_minimized:
        return
    time.sleep(0.7)
    for w in gw.getAllWindows():
        if 'magnifier' in w.title.lower() or 'лупа' in w.title.lower():
            w.minimize()
            magnifier_minimized = True
            break

def toggle_zoom():
    global zoomed_in, overlay
    shift_pressed = keyboard.is_pressed('shift')
    if not zoomed_in:
        keyboard.press_and_release('windows + plus')
        minimize_magnifier()
        zoomed_in = True
        if overlay:
            overlay.show_scope()
    else:
        keyboard.press_and_release('ctrl + alt + num -')
        zoomed_in = False
        if overlay:
            if shift_pressed:
                overlay.visible = True
                overlay.zoomed = True
                overlay.show()
                overlay.update()
            else:
                overlay.hide_scope()

def on_click(x, y, button, pressed):
    if button == mouse.Button.right and pressed and is_cs2_active():
        shift_pressed = keyboard.is_pressed('shift')
        if shift_pressed:
            if overlay:
                overlay.visible = True
                overlay.zoomed = True
                overlay.show()
                overlay.update()
        else:
            toggle_zoom()

def window_monitor():
    global zoomed_in, overlay
    while True:
        if zoomed_in and not is_cs2_active():
            keyboard.press_and_release('ctrl + alt + num -')
            zoomed_in = False
            if overlay:
                overlay.hide_scope()
        time.sleep(0.2)

monitor_thread = threading.Thread(target=window_monitor, daemon=True)
monitor_thread.start()

listener = mouse.Listener(on_click=on_click)
listener.start()
try:
    listener.join()
except KeyboardInterrupt:
    pass
finally:
    keyboard.press_and_release('windows + esc')