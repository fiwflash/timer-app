"""AppController — wires engine signals to overlay, handles lifecycle."""
from PySide6.QtCore import QObject, QTimer
from PySide6.QtWidgets import QApplication, QMessageBox

from models import Storage
from engine import TimerEngine
from ui.main_window import MainWindow
from ui.overlay import OverlayWindow


class AppController(QObject):
    def __init__(self):
        super().__init__()
        self.storage = Storage()
        self.engine = TimerEngine()
        self.main_window = MainWindow(self.storage, self)
        self.overlay = OverlayWindow()
        self._quitting = False

        self.engine.phase_changed.connect(self.overlay.update_phase)
        self.engine.tick.connect(self.overlay.update_time)
        self.engine.check_started.connect(self.overlay.show_check)
        self.engine.object_finished.connect(self._on_object_finished)
        self.engine.waiting_for_next.connect(self.overlay.start_blinking)
        self.overlay.check_set_toggled.connect(self.engine.set_check_state)
        self.overlay.auto_next_toggled.connect(self.engine.set_auto_next)

        self.overlay.btn_prev.clicked.connect(self._prev)
        self.overlay.btn_pause.clicked.connect(self._toggle_pause)
        self.overlay.btn_reset.clicked.connect(self._reset)
        self.overlay.btn_next.clicked.connect(self._next)
        self.overlay.closed.connect(self._on_overlay_closed)

    def start_group(self, group_id: str):
        group = next((g for g in self.storage.groups if g.id == group_id), None)
        if not group:
            return

        group.object_ids = [oid for oid in group.object_ids if self.storage.get_object(oid) is not None]
        if not group.object_ids:
            QMessageBox.warning(self.main_window, "Empty Group", "This group has no usable routines.")
            return

        self._quitting = False
        self.overlay.stop_blinking()
        self.overlay.set_pause_icon(False)
        self.overlay.set_auto_next(self.engine.auto_next)
        self.engine.start_group(group, self.storage)
        
        self.main_window.showMinimized()
        self.overlay.show()
        self.overlay.raise_()
        self.overlay.activateWindow()

    def _on_object_finished(self, is_last: bool):
        if is_last:
            self._quitting = True
            # Let the completion sound finish before the app closes.
            QTimer.singleShot(2200, lambda: QApplication.instance().quit())

    def _on_overlay_closed(self):
        if self._quitting:
            return
        self.engine.stop()
        self.overlay.stop_blinking()
        self.overlay.hide()
        self.main_window.showNormal()
        self.main_window.raise_()
        self.main_window.activateWindow()

    def _toggle_pause(self):
        if self.engine.finished:
            return
        paused = self.engine.toggle_pause()
        self.overlay.set_pause_icon(paused)

    def _reset(self):
        self.overlay.stop_blinking()
        self.overlay.set_pause_icon(False)
        self.engine.reset_current()

    def _prev(self):
        self.overlay.stop_blinking()
        self.overlay.set_pause_icon(False)
        self.engine.prev_object()

    def _next(self):
        self.overlay.stop_blinking()
        self.overlay.set_pause_icon(False)
        self.engine.next_object()