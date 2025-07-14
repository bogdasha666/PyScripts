from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QRectF, QPropertyAnimation, pyqtProperty
from PyQt6.QtGui import QPainter
from PyQt6.QtSvg import QSvgRenderer
import os

class GearIcon(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(18, 18)
        self.hover = False
        self.svg_path = os.path.join(os.path.dirname(__file__), 'gear.svg')
        self.renderer = None
        self.setMouseTracking(True)
        self._load_svg_with_color('#ffffff')  # Белая по умолчанию
        self._hover_anim = 0.0
        self.anim = QPropertyAnimation(self, b"hover_anim")
        self.anim.setDuration(180)

    def get_hover_anim(self):
        return self._hover_anim

    def set_hover_anim(self, value):
        self._hover_anim = value
        # Цвет между белым и светло-серым
        def blend(c1, c2, t):
            return '#{:02x}{:02x}{:02x}'.format(
                int(c1[0]*(1-t)+c2[0]*t),
                int(c1[1]*(1-t)+c2[1]*t),
                int(c1[2]*(1-t)+c2[2]*t))
        white = (255,255,255)
        gray = (230,230,230)
        color = blend(white, gray, self._hover_anim)
        self._load_svg_with_color(color)
        self.update()

    hover_anim = pyqtProperty(float, get_hover_anim, set_hover_anim)

    def _load_svg(self):
        if os.path.exists(self.svg_path):
            try:
                with open(self.svg_path, 'rb') as f:
                    svg_bytes = f.read()
                self.renderer = QSvgRenderer(svg_bytes)
            except Exception:
                self.renderer = None
        else:
            self.renderer = None

    def enterEvent(self, event):
        self.hover = True
        self.anim.stop()
        self.anim.setStartValue(self._hover_anim)
        self.anim.setEndValue(1.0)
        self.anim.start()
        self.update()

    def leaveEvent(self, event):
        self.hover = False
        self.anim.stop()
        self.anim.setStartValue(self._hover_anim)
        self.anim.setEndValue(0.0)
        self.anim.start()
        self.update()

    def _load_svg_with_color(self, color_hex):
        if os.path.exists(self.svg_path):
            try:
                with open(self.svg_path, 'r', encoding='utf-8') as f:
                    svg_data = f.read()
                import re
                svg_data = re.sub(r'fill="#?[A-Fa-f0-9]{3,6}"', f'fill="{color_hex}"', svg_data)
                if 'fill=' not in svg_data:
                    svg_data = svg_data.replace('<path ', f'<path fill="{color_hex}" ', 1)
                self.renderer = QSvgRenderer(bytearray(svg_data, encoding='utf-8'))
            except Exception:
                self.renderer = None
        else:
            self.renderer = None

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self.hover:
            painter.setOpacity(0.85)  # Лёгкий эффект наведения
        if self.renderer and self.renderer.isValid():
            self.renderer.render(painter, QRectF(self.rect()))