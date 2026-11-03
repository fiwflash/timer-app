"""Always-on-top timer overlay window."""
import sys
import ctypes
from PySide6.QtCore import Qt, QTimer, Signal, QSize, QByteArray
from PySide6.QtGui import QColor, QPalette, QIcon, QPixmap, QPainter
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QStackedWidget,
)

from models import fmt_clock

PHASE_COLORS = {
    "prep": "#FFD54F",
    "work": "#66BB6A",
    "rest": "#EF5350",
    "check": "#3A7BD5",
    "idle": "#1E1E1E",
}
PHASE_NAMES = {
    "prep": "READY",
    "work": "WORK",
    "rest": "REST",
    "check": "SETS",
}

class OverlayWindow(QWidget):
    closed = Signal()
    check_set_toggled = Signal(int, bool)

    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.Window | Qt.WindowStaysOnTopHint | Qt.WindowTitleHint | Qt.WindowCloseButtonHint
        )
        self.setWindowTitle(" ")
        self.resize(520, 300) # ขยายความสูงขึ้นเล็กน้อยเพื่อให้พอดี 2 บรรทัด
        self.setMinimumSize(320, 200)

        self._bg_color = PHASE_COLORS["idle"]
        self._blinking = False
        self._blink_state = True
        self._is_paused = False
        self._mode = "timer"
        self._check_buttons = []

        self._blink_timer = QTimer(self)
        self._blink_timer.setInterval(400)
        self._blink_timer.timeout.connect(self._toggle_blink)

        self._time_px = 80
        self._phase_px = 28
        self._info_px = 15

        # 👇 แยก Label สำหรับชื่อท่า และคำอธิบาย
        self.name_label = QLabel("—")
        self.name_label.setAlignment(Qt.AlignCenter)
        self.name_label.setWordWrap(True)

        self.desc_label = QLabel("—")
        self.desc_label.setAlignment(Qt.AlignCenter)
        self.desc_label.setWordWrap(True)

        self.phase_label = QLabel("—")
        self.phase_label.setAlignment(Qt.AlignCenter)

        self.time_label = QLabel("00:00")
        self.time_label.setAlignment(Qt.AlignCenter)

        # Check mode: one large checkbox-style button per set.
        self.check_panel = QWidget()
        self.check_layout = QGridLayout(self.check_panel)
        self.check_layout.setContentsMargins(0, 0, 0, 0)
        self.check_layout.setHorizontalSpacing(8)
        self.check_layout.setVerticalSpacing(8)
        self.check_layout.setAlignment(Qt.AlignCenter)
        self.check_panel.setStyleSheet("background: transparent;")

        self.center_stack = QStackedWidget()
        self.center_stack.setStyleSheet("background: transparent;")
        self.center_stack.addWidget(self.time_label)
        self.center_stack.addWidget(self.check_panel)

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
        root.setSpacing(4)

        # จัดเรียงใหม่: Name (ใหญ่), Desc (เล็ก), Phase, Time/Checks, Set
        root.addWidget(self.name_label)
        root.addWidget(self.desc_label)
        root.addWidget(self.phase_label)
        root.addWidget(self.center_stack, 1)
        root.addWidget(self.set_label)
        root.addLayout(ctrl)

        self._refresh_styles()

    def showEvent(self, event):
        super().showEvent(event)
        if sys.platform == "win32":
            try:
                hwnd = int(self.winId())
                value = ctypes.c_int(1)
                ctypes.windll.dwmapi.DwmSetWindowAttribute(
                    hwnd, 20, ctypes.byref(value), ctypes.sizeof(value)
                )
            except Exception:
                pass

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

    def update_phase(self, phase, name, description, set_n, set_total):
        self._mode = "timer"
        self.center_stack.setCurrentWidget(self.time_label)
        self.btn_pause.setVisible(True)
        self._bg_color = PHASE_COLORS.get(phase, PHASE_COLORS["idle"])
        self.phase_label.setText(PHASE_NAMES.get(phase, ""))
        self.name_label.setText(name)
        self.desc_label.setText(description)
        self.set_label.setText(f"Set {set_n} / {set_total}" if set_total > 1 else "")
        if not self._blinking:
            self._refresh_styles()

    def show_check(self, name, description, set_total, state):
        """Switch the overlay to check mode (no countdown)."""
        self._mode = "check"
        self._blinking = False
        self._blink_timer.stop()
        self._bg_color = PHASE_COLORS["check"]
        self.name_label.setText(name)
        self.desc_label.setText(description)
        self.center_stack.setCurrentWidget(self.check_panel)
        self.btn_pause.setVisible(False)
        self._build_check_buttons(set_total, state)
        self._update_check_label()
        self._refresh_styles()

    def _clear_check_buttons(self):
        while self.check_layout.count():
            item = self.check_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self._check_buttons = []

    def _build_check_buttons(self, set_total, state):
        self._clear_check_buttons()
        total = max(1, int(set_total))
        state = state or []
        for i in range(total):
            btn = QPushButton(str(i + 1))
            btn.setCheckable(True)
            btn.setChecked(bool(state[i]) if i < len(state) else False)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFocusPolicy(Qt.NoFocus)
            btn.setFixedSize(54, 54)
            btn.setToolTip(f"Set {i + 1}")
            btn.toggled.connect(lambda checked, idx=i: self._on_check_toggled(idx, checked))
            row, col = divmod(i, 6)
            self.check_layout.addWidget(btn, row, col, Qt.AlignCenter)
            self._check_buttons.append(btn)

    def _on_check_toggled(self, index, checked):
        self._update_check_label()
        self.check_set_toggled.emit(index, checked)

    def _update_check_label(self):
        total = len(self._check_buttons)
        done = sum(1 for button in self._check_buttons if button.isChecked())
        self.phase_label.setText("DONE" if total and done == total else PHASE_NAMES["check"])
        self.set_label.setText(f"{done} / {total} sets" if total else "")

    def update_time(self, remaining, phase):
        if self._mode == "timer":
            self.time_label.setText(fmt_clock(remaining))

    def start_blinking(self):
        if self._mode == "check":
            return
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
        self._time_px = max(22, int(h * 0.34))
        self._phase_px = max(14, int(h * 0.10))
        self._info_px = max(10, int(h * 0.06))

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
        # Name ตัวใหญ่หนา, Desc ตัวเล็กจาง
        self.name_label.setStyleSheet(
            f"font-size: {self._info_px + 5}px; font-weight: 700; color: {text}; background: transparent;"
        )
        self.desc_label.setStyleSheet(
            f"font-size: {self._info_px}px; font-weight: 400; color: {text}; background: transparent; opacity: 0.8;"
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

        set_btn_style = f"""
            QPushButton {{
                background-color: rgba(0, 0, 0, 0.18);
                border: 2px solid {text};
                border-radius: 12px;
                color: {text};
                font-size: 20px;
                font-weight: 700;
                padding: 0px;
            }}
            QPushButton:hover {{ background-color: rgba(0, 0, 0, 0.32); }}
            QPushButton:pressed {{ background-color: rgba(0, 0, 0, 0.45); }}
            QPushButton:checked {{
                background-color: {text};
                color: {bg};
                border-color: {text};
            }}
        """
        for b in self._check_buttons:
            b.setStyleSheet(set_btn_style)

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