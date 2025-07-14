import sys
import time
import threading
from PySide6 import QtWidgets, QtCore, QtGui
import win32api
from rgb_utils import synced_rgb

VK_MAP = {
    'W': 0x57,
    'A': 0x41,
    'S': 0x53,
    'D': 0x44,
    'LMB': 0x01,
    'RMB': 0x02,
}

BTN_SIZE = 50
BTN_SPACING = 5
BTN_CORNER = 13
BTN_ALPHA = 210
BTN_DARKEN = 68
LMB_RMB_WIDTH = 79

class KeyButton(QtWidgets.QWidget):
    def __init__(self, label, vk_code, wide=False, parent=None):
        super().__init__(parent)
        self.label = label
        self.vk_code = vk_code
        self.anim = 0.0
        self.setFixedSize(LMB_RMB_WIDTH if wide else BTN_SIZE, BTN_SIZE)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_anim)
        self.timer.start(16)
        self.font = QtGui.QFont("Arial Greek", 16, QtGui.QFont.Weight.Normal)
        self.font.setCapitalization(QtGui.QFont.Capitalization.AllUppercase)

    def update_anim(self):
        state = win32api.GetAsyncKeyState(self.vk_code) & 0x8000
        target = 1.0 if state else 0.0
        speed = 0.18
        if abs(self.anim - target) > 0.01:
            self.anim += (target - self.anim) * speed
            self.update()
        else:
            self.anim = target
            self.update()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        base = 38
        darken = int(BTN_DARKEN * self.anim)
        value = max(0, base - darken)
        color = QtGui.QColor(value, value, value, BTN_ALPHA)
        # Adjust rectangle position for W button
        if self.label == 'W':
            rect = self.rect().adjusted(0, 2, -4, -2)  # Shift left by making right margin larger
        else:
            rect = self.rect().adjusted(2, 2, -2, -2)
        painter.setBrush(QtGui.QBrush(color))
        painter.setPen(QtCore.Qt.PenStyle.NoPen)
        painter.drawRoundedRect(rect, BTN_CORNER, BTN_CORNER)
        r, g, b = synced_rgb()
        painter.setFont(self.font)
        painter.setPen(QtGui.QColor(r, g, b))
        # Adjust text position for W and A buttons
        if self.label == 'W':
            text_rect = rect.adjusted(2, 0, 0, 0)  # Move text 2 pixels to the right
            painter.drawText(text_rect, QtCore.Qt.AlignmentFlag.AlignCenter, self.label)
        elif self.label == 'A':
            text_rect = rect.adjusted(2, 0, 0, 0)  # Move text 2 pixels to the right
            painter.drawText(text_rect, QtCore.Qt.AlignmentFlag.AlignCenter, self.label)
        else:
            painter.drawText(rect, QtCore.Qt.AlignmentFlag.AlignCenter, self.label)

class KeystrokesOverlay(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            QtCore.Qt.WindowType.FramelessWindowHint |
            QtCore.Qt.WindowType.WindowStaysOnTopHint |
            QtCore.Qt.WindowType.Tool
        )
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_NoSystemBackground)
        self.setWindowOpacity(1.0)
        self.drag_pos = None
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(BTN_SPACING)
        layout.setContentsMargins(9, 9, 9, 9)
        row1 = QtWidgets.QHBoxLayout()
        row1.addStretch(1)
        self.btn_w = KeyButton('W', VK_MAP['W'])
        row1.addWidget(self.btn_w)
        row1.addStretch(1)
        layout.addLayout(row1)
        row2 = QtWidgets.QHBoxLayout()
        self.btn_a = KeyButton('A', VK_MAP['A'])
        self.btn_s = KeyButton('S', VK_MAP['S'])
        self.btn_d = KeyButton('D', VK_MAP['D'])
        row2.addWidget(self.btn_a)
        row2.addWidget(self.btn_s)
        row2.addWidget(self.btn_d)
        layout.addLayout(row2)
        row3 = QtWidgets.QHBoxLayout()
        self.btn_lmb = KeyButton('LMB', VK_MAP['LMB'], wide=True)
        self.btn_rmb = KeyButton('RMB', VK_MAP['RMB'], wide=True)
        row3.addWidget(self.btn_lmb)
        row3.addWidget(self.btn_rmb)
        layout.addLayout(row3)
        width = max(2*LMB_RMB_WIDTH + BTN_SPACING, 3*BTN_SIZE + 2*BTN_SPACING) + 18
        height = BTN_SIZE*3 + BTN_SPACING*2 + 18
        self.setFixedSize(width, height)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self.drag_pos and event.buttons() & QtCore.Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self.drag_pos = None

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)  
    overlay = KeystrokesOverlay()
    # Получаем размер экрана
    screen = app.primaryScreen()
    screen_geometry = screen.geometry()
    screen_width = screen_geometry.width()
    screen_height = screen_geometry.height()
    # Получаем размер оверлея
    overlay_width = overlay.width()
    overlay_height = overlay.height()
    # Центрируем по горизонтали, по вертикали - ниже центра (например, +1/3 высоты экрана)
    x = (screen_width - overlay_width) // 2
    y = (screen_height - overlay_height) // 2 + screen_height * 8 // 24.6 # буквально чуть-чуть пониже
    overlay.move(x, y)
    overlay.show()
    sys.exit(app.exec())
