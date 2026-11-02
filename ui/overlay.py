"""Always-on-top timer overlay window."""
import sys
import ctypes
from PySide6.QtCore import Qt, QTimer, Signal, QSize, QByteArray
from PySide6.QtGui import QColor, QPalette, QIcon, QPixmap, QPainter
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
)

from models import fmt_clock

PHASE_COLORS = {
    "prep": "#FFD54F",
    "work": "#66BB6A",
    "rest": "#EF5350",
    "idle": "#1E1E1E",
}

PHASE_NAMES = {
    "prep": "READY",
    "work": "WORK",
    "rest": "REST",
}

class OverlayWindow(QWidget):
    closed = Signal()

    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.Window
            | Qt.WindowStaysOnTopHint
            | Qt.WindowTitleHint
            | Qt.WindowCloseButtonHint
        )
        # ซ่อนชื่อโปรแกรมบน Title bar
        self.setWindowTitle(" ")
        self.resize(520, 280)
        self.setMinimumSize(320, 180)

        self._bg_color = PHASE_COLORS["idle"]
        self._blinking = False
        self._blink_state = True
        self._is_paused = False

        self._blink_timer = QTimer(self)
        self._blink_timer.setInterval(400)
        self._blink_timer.timeout.connect(self._toggle_blink)

        self._time_px = 80
        self._phase_px = 28
        self._info_px = 15

        self.obj_label = QLabel("—")
        self.obj_label.setAlignment(Qt.AlignCenter)

        self.phase_label = QLabel("—")
        self.phase_label.setAlignment(Qt.AlignCenter)

        self.time_label = QLabel("00:00")
        self.time_label.setAlignment(Qt.AlignCenter)

        self.set_label = QLabel("")
        self.set_label.setAlignment(Qt.AlignCenter)

        self.btn_prev = QPushButton()
        self.btn_pause = QPushButton()
        self.btn_reset = QPushButton()
        self.btn_next = QPushButton()

        for b in (self.btn_prev, self.btn_pause, self.btn_reset, self.btn_next):
            b.setCursor(Qt.PointingHandCursor)
            b.setFocusPolicy(Qt.NoFocus)
            b.setFixedSize(50, 50)
            b.setIconSize(QSize(24, 24))

        ctrl = QHBoxLayout()
        ctrl.setSpacing(16)
        ctrl.addStretch()
        ctrl.addWidget(self.btn_prev)
        ctrl.addWidget(self.btn_pause)
        ctrl.addWidget(self.btn_reset)
        ctrl.addWidget(self.btn_next)
        ctrl.addStretch()

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 10, 16, 16)
        root.setSpacing(6)
        root.addWidget(self.obj_label)
        root.addWidget(self.phase_label)
        root.addWidget(self.time_label, 1)
        root.addWidget(self.set_label)
        root.addLayout(ctrl)

        self._refresh_styles()

    def showEvent(self, event):
        super().showEvent(event)
        # เปิดโหมด Dark Mode ให้กับ Title Bar
        if sys.platform == "win32":
            try:
                hwnd = int(self.winId())
                value = ctypes.c_int(1)
                ctypes.windll.dwmapi.DwmSetWindowAttribute(
                    hwnd, 20, ctypes.byref(value), ctypes.sizeof(value)
                )
            except Exception as e:
                pass # ซ่อน error ไว้ถ้าระบบไม่รองรับ

    def _get_icon(self, name: str, color: str) -> QIcon:
        paths = {
            "prev": f'<polygon points="18 20 8 12 18 4 18 20" fill="{color}" stroke="{color}" stroke-width="1.5" stroke-linejoin="round"/><line x1="5" y1="19" x2="5" y2="5" stroke="{color}" stroke-width="2.5" stroke-linecap="round"/>',
            "next": f'<polygon points="6 4 16 12 6 20 6 4" fill="{color}" stroke="{color}" stroke-width="1.5" stroke-linejoin="round"/><line x1="19" y1="19" x2="19" y2="5" stroke="{color}" stroke-width="2.5" stroke-linecap="round"/>',
            "play": f'<polygon points="7 4 19 12 7 20 7 4" fill="{color}" stroke="{color}" stroke-width="1.5" stroke-linejoin="round"/>',
            "pause": f'<rect x="7" y="4" width="4" height="16" rx="1" fill="{color}"/><rect x="13" y="4" width="4" height="16" rx="1" fill="{color}"/>',
            "reset": f'<path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><path d="M3 3v5h5" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>'
        }
        svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">{paths[name]}</svg>'
        renderer = QSvgRenderer(QByteArray(svg.encode()))
        pixmap = QPixmap(48, 48)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()
        return QIcon(pixmap)

    def set_pause_icon(self, paused: bool):
        self._is_paused = paused
        self._refresh_styles()

    def update_phase(self, phase, name, set_n, set_total):
        self._bg_color = PHASE_COLORS.get(phase, PHASE_COLORS["idle"])
        self.phase_label.setText(PHASE_NAMES.get(phase, ""))
        self.obj_label.setText(name)
        self.set_label.setText(f"Set {set_n} / {set_total}" if set_total > 1 else "")
        if not self._blinking:
            self._refresh_styles()

    def update_time(self, remaining, phase):
        self.time_label.setText(fmt_clock(remaining))

    def start_blinking(self):
        self._blinking = True
        self._blink_state = True
        self._apply_colors(self._bg_color)
        self._blink_timer.start()

    def stop_blinking(self):
        self._blinking = False
        self._blink_timer.stop()
        self._refresh_styles()

    def _toggle_blink(self):
        self._blink_state = not self._blink_state
        color = self._bg_color if self._blink_state else "#FFFFFF"
        self._apply_colors(color)

    def _set_palette_bg(self, color):
        pal = self.palette()
        pal.setColor(QPalette.Window, QColor(color))
        self.setPalette(pal)
        self.setAutoFillBackground(True)

    def _compute_sizes(self):
        h = max(self.height(), 1)
        self._time_px = max(22, int(h * 0.36))
        self._phase_px = max(14, int(h * 0.11))
        self._info_px = max(10, int(h * 0.065))

    @staticmethod
    def _text_color_for(color: str) -> str:
        c = QColor(color)
        lum = 0.299 * c.red() + 0.587 * c.green() + 0.114 * c.blue()
        return "#000000" if lum > 150 else "#FFFFFF"

    def _apply_colors(self, bg):
        self._set_palette_bg(bg)
        text = self._text_color_for(bg)

        self.time_label.setStyleSheet(
            f"font-size: {self._time_px}px; font-weight: 300; "
            f"color: {text}; background: transparent;"
        )
        self.phase_label.setStyleSheet(
            f"font-size: {self._phase_px}px; font-weight: 600; "
            f"color: {text}; background: transparent; letter-spacing: 3px;"
        )
        self.obj_label.setStyleSheet(
            f"font-size: {self._info_px}px; color: {text}; background: transparent;"
        )
        self.set_label.setStyleSheet(
            f"font-size: {self._info_px}px; color: {text}; background: transparent;"
        )

        self.btn_prev.setIcon(self._get_icon("prev", text))
        self.btn_next.setIcon(self._get_icon("next", text))
        self.btn_reset.setIcon(self._get_icon("reset", text))
        pause_icon = "play" if self._is_paused else "pause"
        self.btn_pause.setIcon(self._get_icon(pause_icon, text))

        btn_style = f"""
            QPushButton {{
                background-color: rgba(0, 0, 0, 0.2);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 25px;
                padding: 0px;
            }}
            QPushButton:hover {{ background-color: rgba(0, 0, 0, 0.4); }}
            QPushButton:pressed {{ background-color: rgba(0, 0, 0, 0.6); }}
        """
        for b in (self.btn_prev, self.btn_pause, self.btn_reset, self.btn_next):
            b.setStyleSheet(btn_style)

    def _refresh_styles(self):
        self._compute_sizes()
        color = self._bg_color if (not self._blinking or self._blink_state) else "#FFFFFF"
        self._apply_colors(color)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._refresh_styles()

    def closeEvent(self, event):
        self.closed.emit()
        event.accept()