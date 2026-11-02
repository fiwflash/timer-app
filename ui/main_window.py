"""Main window — combines routines & groups tabs."""
import sys
import ctypes
from PySide6.QtWidgets import QMainWindow, QTabWidget

from models import Storage
from ui.objects_tab import ObjectsTab
from ui.groups_tab import GroupsTab


class MainWindow(QMainWindow):
    def __init__(self, storage: Storage, controller):
        super().__init__()
        self.storage = storage
        self.controller = controller

        # ใช้ช่องว่างแทนชื่อ เพื่อไม่ให้แสดงข้อความบน Title Bar
        self.setWindowTitle(" ")
        self.resize(1000, 680)
        self.setMinimumSize(850, 550)

        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.West)
        self.tabs.setDocumentMode(True)

        self.objects_tab = ObjectsTab(storage)
        self.groups_tab = GroupsTab(storage)

        self.tabs.addTab(self.objects_tab, "Routines")
        self.tabs.addTab(self.groups_tab, "Groups")
        self.tabs.setCurrentIndex(1)
        self.setCentralWidget(self.tabs)

        self.objects_tab.data_changed.connect(self.groups_tab.refresh)
        self.groups_tab.start_group_requested.connect(
            self.controller.start_group
        )

    def showEvent(self, event):
        super().showEvent(event)
        # เปิดโหมด Dark Mode ให้กับ Title Bar ของ Windows
        if sys.platform == "win32":
            try:
                # ดึง handle ของหน้าต่าง
                hwnd = int(self.winId())
                # DWMWA_USE_IMMERSIVE_DARK_MODE = 20
                value = ctypes.c_int(1)
                ctypes.windll.dwmapi.DwmSetWindowAttribute(
                    hwnd, 20, ctypes.byref(value), ctypes.sizeof(value)
                )
            except Exception as e:
                print(f"Failed to apply dark title bar: {e}")