"""Timer state machine — produces a sequence of phases from a TimerObject."""
from PySide6.QtCore import QObject, QTimer, Signal
from models import TimerObject, Group, Storage
from audio import play_bell, play_beep, play_finish, play_object_done


class TimerEngine(QObject):
    phase_changed = Signal(str, str, str, int, int)  # phase, name, description, set_n, set_total
    tick = Signal(int, str)
    check_started = Signal(str, str, int, list)  # name, description, set_total, checked_state
    object_finished = Signal(bool)
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
        self.mode = "timer"
        self.current_obj = None
        self.check_states = {}

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

    def start_group(self, group: Group, storage: Storage):
        self.group = group
        self.storage = storage
        self.obj_index = 0
        self.current_obj = None
        self.mode = "timer"
        self.check_states = {}
        self._load_object()

    def _load_object(self):
        if not self.group or not self.storage:
            return
        if self.obj_index >= len(self.group.object_ids):
            return
        obj = self.storage.get_object(self.group.object_ids[self.obj_index])
        if obj is None:
            return

        self.current_obj = obj
        self.finished = False
        self.paused = False

        # Check item: no countdown, just one checkbox per set.
        if getattr(obj, "mode", "timer") == "check":
            self.mode = "check"
            self.sequence = []
            self.phase_index = 0
            self.remaining = 0
            self.timer.stop()
            total = max(1, obj.sets)
            state = self.check_states.get(obj.id)
            if not isinstance(state, list) or len(state) != total:
                state = [False] * total
                self.check_states[obj.id] = state
            self.check_started.emit(obj.name, obj.description, total, list(state))
            return

        self.mode = "timer"
        self.sequence = self.build_sequence(obj)
        self.phase_index = 0

        if self.sequence:
            self.remaining = self.sequence[0]["duration"]
            self._emit_current()
            self.timer.start()

    def _emit_current(self):
        if self.phase_index >= len(self.sequence):
            return
        step = self.sequence[self.phase_index]
        obj = self.storage.get_object(self.group.object_ids[self.obj_index])
        # ส่ง name และ description แยกกัน
        self.phase_changed.emit(step["phase"], obj.name, obj.description, step["set"], obj.sets)
        self.tick.emit(self.remaining, step["phase"])

    def _on_tick(self):
        if self.mode != "timer" or self.paused or self.finished:
            return
        self.remaining -= 1
        step = self.sequence[self.phase_index]

        if self.remaining > 0:
            # Countdown pips at 3, 2 and 1 seconds.
            if step["duration"] >= 3 and self.remaining <= 3:
                play_beep(urgent=self.remaining == 1)
            self.tick.emit(self.remaining, step["phase"])
        else:
            self._advance()

    def _advance(self):
        self.phase_index += 1
        if self.phase_index >= len(self.sequence):
            self.tick.emit(0, self.sequence[-1]["phase"])
            self._object_done()
            return
        step = self.sequence[self.phase_index]
        self.remaining = step["duration"]
        # Sound the new phase exactly when it begins.
        play_bell()
        self._emit_current()

    def _object_done(self):
        self.timer.stop()
        self.finished = True
        is_last = self.obj_index >= len(self.group.object_ids) - 1
        if is_last:
            play_finish()
        else:
            play_object_done()
        self.object_finished.emit(is_last)
        if not is_last:
            self.waiting_for_next.emit()

    def toggle_pause(self) -> bool:
        if self.mode != "timer" or self.finished:
            return False
        self.paused = not self.paused
        if self.paused:
            self.timer.stop()
        else:
            self.timer.start()
        return self.paused

    def set_check_state(self, index: int, checked: bool):
        """Remember the checkbox state for the current check item."""
        if self.mode != "check" or self.current_obj is None:
            return
        state = self.check_states.get(self.current_obj.id)
        if state is not None and 0 <= index < len(state):
            state[index] = bool(checked)

    def reset_current(self):
        if self.mode == "check" and self.current_obj is not None:
            total = max(1, self.current_obj.sets)
            self.check_states[self.current_obj.id] = [False] * total
        self._load_object()

    def next_object(self):
        if not self.group:
            return
        if self.obj_index + 1 < len(self.group.object_ids):
            self.obj_index += 1
            self._load_object()
        elif (
            self.current_obj is not None
            and getattr(self.current_obj, "mode", "timer") == "check"
            and not self.finished
        ):
            # Last check item: pressing Next ends the workout.
            self._object_done()
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
        self.current_obj = None
        self.mode = "timer"
        self.check_states = {}