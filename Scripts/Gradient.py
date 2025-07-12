import sys
import time
import numpy as np
from PySide6 import QtWidgets, QtGui, QtCore
import mss
from PIL import Image
import importlib.util

# Импортируем get_rgb_color из rgb_utils.py
spec = importlib.util.spec_from_file_location("rgb_utils", "Scripts/rgb_utils.py")
if spec and spec.loader:
    rgb_utils = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rgb_utils)
else:
    raise ImportError("Cannot import rgb_utils.py")

# Цвет для замены (chroma key)
TARGET_RGB = (202, 102, 255)  # #ca66ff
TOLERANCE = 80  # Допуск по цвету (увеличен)

# Размер захвата (по умолчанию - весь экран)
with mss.mss() as sct:
    monitor = sct.monitors[1]
    WIDTH = monitor['width']
    HEIGHT = monitor['height']

def make_color(r, g, b, a=180):
    c = QtGui.QColor(r, g, b)
    c.setAlpha(a)
    return c

class OverlayWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            QtCore.Qt.WindowType.WindowStaysOnTopHint |
            QtCore.Qt.WindowType.FramelessWindowHint |
            QtCore.Qt.WindowType.Tool
        )
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setGeometry(0, 0, WIDTH, HEIGHT)
        self._mask = np.zeros((HEIGHT, WIDTH), dtype=bool)
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_overlay)
        self.timer.start(30)  # ~33 FPS
        # --- история масок для сглаживания ---
        self.mask_history = []
        self.mask_history_len = 3  # усреднять по 3 кадрам

    def update_overlay(self):
        # Захват экрана
        with mss.mss() as sct:
            img = sct.grab(sct.monitors[1])
            frame = Image.frombytes('RGB', img.size, img.rgb)
            arr = np.array(frame)

        # Поиск пикселей, близких к TARGET_RGB
        diff = np.abs(arr - TARGET_RGB)
        mask = np.all(diff < TOLERANCE, axis=2)
        # --- усреднение маски ---
        self.mask_history.append(mask)
        if len(self.mask_history) > self.mask_history_len:
            self.mask_history.pop(0)
        avg_mask = np.mean(self.mask_history, axis=0)
        self._mask = avg_mask > 0.5  # пиксель считается подходящим, если чаще True
        self.update()

    def paintEvent(self, event):
        if self._mask is None:
            return
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        # Создаём QImage для маски
        overlay_img = QtGui.QImage(self.width(), self.height(), QtGui.QImage.Format.Format_ARGB32)
        overlay_img.fill(QtCore.Qt.GlobalColor.transparent)
        # Создаём радужный градиент по ширине окна с одинаковым alpha
        grad = QtGui.QLinearGradient(0, 0, self.width(), 0)
        grad.setColorAt(0.0, make_color(255, 0, 0))     # Red
        grad.setColorAt(0.16, make_color(255, 127, 0))  # Orange
        grad.setColorAt(0.33, make_color(255, 255, 0))  # Yellow
        grad.setColorAt(0.5, make_color(0, 255, 0))     # Green
        grad.setColorAt(0.66, make_color(0, 0, 255))    # Blue
        grad.setColorAt(0.83, make_color(75, 0, 130))   # Indigo
        grad.setColorAt(1.0, make_color(148, 0, 211))   # Violet
        grad_brush = QtGui.QBrush(grad)
        # Рисуем градиент на отдельном изображении
        grad_img = QtGui.QImage(self.width(), self.height(), QtGui.QImage.Format.Format_ARGB32)
        grad_img.fill(QtCore.Qt.GlobalColor.transparent)
        grad_painter = QtGui.QPainter(grad_img)
        grad_painter.fillRect(0, 0, self.width(), self.height(), grad_brush)
        grad_painter.end()
        # Применяем маску: только к найденным пикселям
        img_ptr = overlay_img.bits()
        arr = np.ndarray((self.height(), self.width(), 4), dtype=np.uint8, buffer=memoryview(img_ptr))
        grad_ptr = grad_img.bits()
        grad_arr = np.ndarray((self.height(), self.width(), 4), dtype=np.uint8, buffer=memoryview(grad_ptr))
        arr[:, :, :] = 0  # прозрачный фон
        y_idx, x_idx = np.where(self._mask)
        arr[y_idx, x_idx, :] = grad_arr[y_idx, x_idx, :]
        # Нарисовать QImage
        painter.drawImage(0, 0, overlay_img)
        painter.end()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    overlay = OverlayWidget()
    overlay.show()
    sys.exit(app.exec())
