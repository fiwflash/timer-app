"""Timer state machine — produces a sequence of phases from a TimerObject."""
from PySide6.QtCore import QObject, QTimer, Signal

from models import TimerObject, Group, Storage
from audio import play_bell, play_beep


class TimerEngine(QObject):
    phase_changed = Signal(str, str, int, int)  # phase, name, set_n, set_total
    tick = Signal(int, str)                     # remaining, phase
    object_finished = Signal(bool)              # is_last_in_group
    waiting_for_next = Signal()

    def __init__(self):
        super().__init__()
        self.timer = QTimer()
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self._on_tick)

        self.group = None
        self.storage = None
        self.obj_index = 0
        self.sequence = []
        self.phase_index = 0
        self.remaining = 0
        self.paused = False
        self.finished = False

    # ---------------------------------------------------------------
    def build_sequence(self, obj: TimerObject) -> list:
        seq = []
        if obj.prep > 0:
            seq.append({"phase": "prep", "duration": obj.prep, "set": 1})

        for i in range(obj.sets):
            if obj.per_side:
                seq.append({"phase": "work", "duration": obj.work, "set": i + 1})
                if obj.prep > 0:
                    seq.append({"phase": "prep", "duration": obj.prep, "set": i + 1})
                seq.append({"phase": "work", "duration": obj.work, "set": i + 1})
            else:
                seq.append({"phase": "work", "duration": obj.work, "set": i + 1})

            if i < obj.sets - 1 and obj.rest > 0:
                seq.append({"phase": "rest", "duration": obj.rest, "set": i + 1})

        return seq

    # ---------------------------------------------------------------
    def start_group(self, group: Group, storage: Storage):
        self.group = group
        self.storage = storage
        self.obj_index = 0
        self._load_object()

    def _load_object(self):
        if not self.group or not self.storage:
            return
        if self.obj_index >= len(self.group.object_ids):
            return
        obj = self.storage.get_object(self.group.object_ids[self.obj_index])
        if obj is None:
            return

        self.sequence = self.build_sequence(obj)
        self.phase_index = 0
        self.finished = False
        self.paused = False

        if self.sequence:
            self.remaining = self.sequence[0]["duration"]
            self._emit_current()
            self.timer.start()

    def _emit_current(self):
        if self.phase_index >= len(self.sequence):
            return
        step = self.sequence[self.phase_index]
        obj = self.storage.get_object(self.group.object_ids[self.obj_index])
        self.phase_changed.emit(step["phase"], obj.name, step["set"], obj.sets)
        self.tick.emit(self.remaining, step["phase"])

    def _on_tick(self):
        if self.paused or self.finished:
            return
            
        self.remaining -= 1
        step = self.sequence[self.phase_index]

        # 1. เสียง "ติ๊ด" (Beep) จะดังตอนเหลือ 2 วินาที (ถ้าเวลาตั้งแต่ 3 วิขึ้นไป)
        if step["duration"] >= 3 and self.remaining == 2:
            play_beep()

        # 2. เสียง "กระดิ่ง" (Bell) จะดังตอนเหลือ 1 วินาทีสุดท้าย (ก่อนหน้าจอเปลี่ยน)
        if self.remaining == 1:
            play_bell()

        # 3. หมดเวลา (0 วินาที)
        if self.remaining <= 0:
            self._advance()
        else:
            self.tick.emit(self.remaining, step["phase"])

    def _advance(self):
        self.phase_index += 1
        if self.phase_index >= len(self.sequence):
            self.tick.emit(0, self.sequence[-1]["phase"])
            self._object_done()
            return
        
        step = self.sequence[self.phase_index]
        self.remaining = step["duration"]
        
        # ไม่ต้อง play_bell() ตรงนี้แล้ว เพราะย้ายไปเล่นที่ _on_tick ตอน 1 วิ
        self._emit_current()

    def _object_done(self):
        self.timer.stop()
        self.finished = True
        
        # ไม่ต้อง play_bell() ตรงนี้แล้ว เพื่อป้องกันเสียงกระดิ่งดังซ้ำซ้อน 2 รอบ
        is_last = self.obj_index >= len(self.group.object_ids) - 1
        self.object_finished.emit(is_last)
        if not is_last:
            self.waiting_for_next.emit()

    # ---------------------------------------------------------------
    def toggle_pause(self) -> bool:
        if self.finished:
            return self.paused
        self.paused = not self.paused
        if self.paused:
            self.timer.stop()
        else:
            self.timer.start()
        return self.paused

    def reset_current(self):
        self._load_object()

    def next_object(self):
        if not self.group:
            return
        if self.obj_index + 1 < len(self.group.object_ids):
            self.obj_index += 1
            self._load_object()
        else:
            self.timer.stop()
            self.finished = True
            self.waiting_for_next.emit()

    def prev_object(self):
        if self.obj_index > 0:
            self.obj_index -= 1
            self._load_object()

    def stop(self):
        self.timer.stop()
        self.finished = True
        self.group = None