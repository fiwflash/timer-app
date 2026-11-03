"""Entry point — Interval Timer"""
import sys
from pathlib import Path

from PySide6.QtCore import QLocale
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import QApplication

from audio import BELL_FILE, prewarm
from controller import AppController


def resource_path(relative_path: str) -> Path:
    """ หา Path ของไฟล์ที่ถูก bundle ไปกับ .exe (รองรับทั้งตอนรัน .py และ .exe) """
    try:
        # PyInstaller จะสร้างโฟลเดอร์ชั่วคราวและเก็บ path ไว้ใน sys._MEIPASS
        base_path = Path(sys._MEIPASS)
    except Exception:
        # ตอนรันด้วย python ปกติ
        base_path = Path(__file__).resolve().parent
    return base_path / relative_path


DARK_THEME_QSS = """
/* Global */
QWidget {
    background-color: #1C1C1E;
    color: #E6E6E6;
    font-family: "Segoe UI", "Leelawadee UI", sans-serif;
    font-size: 13px;
}
QMainWindow { background-color: #1C1C1E; }

/* Sidebar tabs */
QTabWidget::pane {
    border: none;
    background-color: #1C1C1E;
}
QTabBar::tab {
    background: transparent;
    color: #9A9A9A;
    padding: 12px 20px;
    font-size: 13px;
    text-align: left;
    border: none;
    border-left: 3px solid transparent;
    margin-bottom: 2px;
}
QTabBar::tab:selected {
    background: #262628;
    color: #FFFFFF;
    border-left: 3px solid #60CDFF;
    border-top-right-radius: 6px;
    border-bottom-right-radius: 6px;
}
QTabBar::tab:hover:!selected {
    background: #222224;
    color: #FFFFFF;
}

/* Lists */
QListWidget {
    background: #232325;
    border: 1px solid #303033;
    border-radius: 8px;
    padding: 4px;
    outline: none;
    font-size: 13px;
}
QListWidget::item {
    padding: 10px;
    border-radius: 6px;
    margin-bottom: 2px;
}
QListWidget::item:selected {
    background: #0F6CBD;
    color: #FFFFFF;
}
QListWidget::item:hover:!selected {
    background: #2C2C2F;
}

/* Buttons */
QPushButton {
    background-color: #2E2E31;
    border: 1px solid #3D3D41;
    border-radius: 6px;
    padding: 7px 12px;
    color: #F0F0F0;
}
QPushButton:hover { background-color: #39393D; }
QPushButton:pressed { background-color: #232326; }
QPushButton:disabled {
    background-color: #242426;
    color: #66666A;
    border-color: #2E2E31;
}

/* Primary action */
QPushButton#startBtn {
    background-color: #0078D4;
    color: #FFFFFF;
    border: none;
    font-weight: 600;
    font-size: 15px;
    padding: 12px;
}
QPushButton#startBtn:hover { background-color: #1888DB; }
QPushButton#startBtn:pressed { background-color: #005A9E; }
QPushButton#startBtn:disabled {
    background-color: #262628;
    color: #66666A;
    border: 1px solid #3D3D41;
}

/* Inputs */
QSpinBox, QLineEdit {
    background-color: #262628;
    border: 1px solid #3D3D41;
    border-radius: 6px;
    padding: 6px 10px;
    color: #FFFFFF;
    selection-background-color: #0F6CBD;
}
QLineEdit {
    font-size: 14px;
    padding: 9px 10px;
}
QSpinBox:focus, QLineEdit:focus {
    border: 1px solid #60CDFF;
}

QComboBox {
    background-color: #262628;
    border: 1px solid #3D3D41;
    border-radius: 6px;
    padding: 6px 10px;
    color: #FFFFFF;
}
QComboBox:hover { border-color: #4A4A4F; }
QComboBox::drop-down { border: none; width: 24px; }
QComboBox QAbstractItemView {
    background: #262628;
    border: 1px solid #3D3D41;
    color: #FFFFFF;
    selection-background-color: #0F6CBD;
    outline: none;
}

/* Checkbox */
QCheckBox { spacing: 8px; font-size: 13px; }
QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 1px solid #4A4A4F;
    background: #262628;
}
QCheckBox::indicator:checked {
    background: #0078D4;
    border: 1px solid #0078D4;
}

/* Minimal scrollbars */
QScrollBar:vertical {
    background: transparent;
    width: 10px;
    margin: 2px;
}
QScrollBar::handle:vertical {
    background: #3D3D41;
    border-radius: 4px;
    min-height: 28px;
}
QScrollBar::handle:vertical:hover { background: #4A4A4F; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }
"""

def main():
    app = QApplication(sys.argv)
    
    QLocale.setDefault(QLocale(QLocale.English, QLocale.UnitedStates))
    app.setStyle("Fusion")
    app.setFont(QFont("Segoe UI", 10))
    app.setStyleSheet(DARK_THEME_QSS)

    # 👇 ---------------------------------------------------------
    # โหลดไอคอน (รองรับทั้ง .py และ .exe)
    icon_ico = resource_path("icon.ico")
    icon_png = resource_path("icon.png")

    if icon_ico.exists():
        app.setWindowIcon(QIcon(str(icon_ico)))
    elif icon_png.exists():
        app.setWindowIcon(QIcon(str(icon_png)))
    # 👆 ---------------------------------------------------------

    if not BELL_FILE.exists():
        print(f"Warning: {BELL_FILE} not found. Bell sound disabled.")

    # Build the loud alert files in the background so the first cue is instant.
    prewarm()

    controller = AppController()
    controller.main_window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()