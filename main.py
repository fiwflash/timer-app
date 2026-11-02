"""Entry point — Interval Timer"""
import sys
from pathlib import Path 
from PySide6.QtCore import QLocale
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import QApplication

from audio import BELL_FILE
from controller import AppController

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = Path(__file__).resolve().parent
    return Path(base_path) / relative_path
    
DARK_THEME_QSS = """
/* Global */
QWidget {
    background-color: #1E1E1E;
    color: #E0E0E0;
    font-family: "Segoe UI", "Leelawadee UI", sans-serif;
    font-size: 13px;
}
QMainWindow { background-color: #1E1E1E; }

/* Tab Widget (Sidebar Style) */
QTabWidget::pane {
    border: none;
    background-color: #1E1E1E;
}
QTabBar::tab {
    background: transparent;
    color: #A0A0A0;
    padding: 14px 24px;
    font-size: 14px;
    text-align: left;
    border: none;
    border-left: 4px solid transparent;
    margin-bottom: 4px;
}
QTabBar::tab:selected {
    background: #2D2D2D;
    color: #FFFFFF;
    border-left: 4px solid #60CDFF;
    border-top-right-radius: 6px;
    border-bottom-right-radius: 6px;
}
QTabBar::tab:hover:!selected {
    background: #2A2A2A;
    color: #FFFFFF;
}

/* Lists */
QListWidget {
    background: #252525;
    border: 1px solid #333333;
    border-radius: 8px;
    padding: 6px;
    outline: none;
    font-size: 14px;
}
QListWidget::item {
    padding: 12px;
    border-radius: 6px;
    margin-bottom: 2px;
}
QListWidget::item:selected {
    background: #0078D4;
    color: white;
}
QListWidget::item:hover:!selected {
    background: #333333;
}

/* Buttons */
QPushButton {
    background-color: #333333;
    border: 1px solid #444444;
    border-radius: 6px;
    padding: 8px 16px;
    color: #FFFFFF;
}
QPushButton:hover { background-color: #444444; }
QPushButton:pressed { background-color: #222222; }
QPushButton:disabled {
    background-color: #252525;
    color: #666666;
    border-color: #333333;
}

/* Start Button (Special) */
QPushButton#startBtn {
    background-color: #0078D4;
    color: #FFFFFF;
    border: none;
    font-weight: 600;
    font-size: 16px;
    padding: 14px;
}
QPushButton#startBtn:hover { background-color: #1084D0; }
QPushButton#startBtn:pressed { background-color: #005A9E; }
QPushButton#startBtn:disabled {
    background-color: #2D2D2D;
    color: #666666;
    border: 1px solid #444444;
}

/* Inputs */
QSpinBox, QLineEdit {
    background-color: #2D2D2D;
    border: 1px solid #444444;
    border-radius: 6px;
    padding: 6px 10px;
    color: white;
    selection-background-color: #0078D4;
}
QLineEdit { font-size: 15px; padding: 10px; }
QSpinBox:focus, QLineEdit:focus { border: 1px solid #60CDFF; }

/* Checkbox */
QCheckBox { spacing: 8px; font-size: 14px; }
QCheckBox::indicator {
    width: 20px;
    height: 20px;
    border-radius: 4px;
    border: 1px solid #555555;
    background: #2D2D2D;
}
QCheckBox::indicator:checked {
    background: #0078D4;
    border: 1px solid #0078D4;
}

/* Preview Box */
QLabel#previewBox {
    background-color: #2D2D2D;
    color: #60CDFF;
    border: 1px solid #444444;
    border-radius: 8px;
    padding: 20px;
}
"""

def main():
    app = QApplication(sys.argv)
    
    QLocale.setDefault(QLocale(QLocale.English, QLocale.UnitedStates))
    app.setStyle("Fusion")
    app.setFont(QFont("Segoe UI", 10))
    app.setStyleSheet(DARK_THEME_QSS)

    # 👇 ---------------------------------------------------------
    # หา Path ของไอคอน (รองรับทั้งตอนรัน .py และ .exe)
    icon_ico = resource_path("icon.ico")
    icon_png = resource_path("icon.png")

    if icon_ico.exists():
        app.setWindowIcon(QIcon(str(icon_ico)))
    elif icon_png.exists():
        app.setWindowIcon(QIcon(str(icon_png)))
    # 👆 ---------------------------------------------------------

    if not BELL_FILE.exists():
        print(f"Warning: {BELL_FILE} not found. Bell sound disabled.")

    controller = AppController()
    controller.main_window.show()
    sys.exit(app.exec())