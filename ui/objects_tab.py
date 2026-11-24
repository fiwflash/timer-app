"""Tab: manage TimerObject list (Bank)."""
import json
from pathlib import Path
from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QListWidget, QListWidgetItem, QPushButton, QLabel, QLineEdit,
    QSpinBox, QCheckBox, QMessageBox, QFileDialog, QDialog, QTextEdit,
    QComboBox, QStackedWidget,
)

from models import TimerObject, Group, Storage  # 👈 เพิ่ม Group


class JSONTemplateDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("JSON Template")
        self.resize(500, 450)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("You can import just exercises, or exercises + groups."))
        layout.addWidget(QLabel("Use this structure:"))

        text = QTextEdit()
        text.setReadOnly(True)
        text.setStyleSheet("font-family: Consolas, monospace; font-size: 13px;")
        # 👇 อัปเดตตัวอย่าง JSON ให้โชว์ทั้ง Exercise และ Group
        text.setText("""{
  "exercises": [
    {
      "name": "Push Ups",
      "sets": 3,
      "work": 30,
      "prep": 5,
      "rest": 15,
      "per_side": false
    },
    {
      "name": "Squats",
      "sets": 4,
      "work": 45,
      "prep": 0,
      "rest": 20,
      "per_side": true
    }
  ],
  "groups": [
    {
      "name": "Monday Workout",
      "sequence": ["Push Ups", "Squats", "Push Ups"]
    }
  ]
}""")
        layout.addWidget(text)

        btn = QPushButton("Got it")
        btn.clicked.connect(self.accept)
        layout.addWidget(btn)


class ObjectsTab(QWidget):
    data_changed = Signal()

    def __init__(self, storage: Storage):
        super().__init__()
        self.storage = storage
        self._editing_id = None
        self._loading = False

        # --- Left Side: Bank List ---
        self.list = QListWidget()
        self.list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.list.setWordWrap(True)
        self.list.currentRowChanged.connect(self._on_select)

        self.btn_new = QPushButton("+ New")
        self.btn_import = QPushButton("Import")
        self.btn_del = QPushButton("Delete")

        self.btn_new.clicked.connect(self._new)
        self.btn_import.clicked.connect(self._import_json)
        self.btn_del.clicked.connect(self._delete)

        left = QVBoxLayout()
        left.setSpacing(8)
        left.addWidget(self.list, 1)

        row1 = QHBoxLayout()
        row1.setSpacing(8)
        row1.addWidget(self.btn_new, 1)
        row1.addWidget(self.btn_import)
        row1.addWidget(self.btn_del)
        left.addLayout(row1)

        left_w = QWidget()
        left_w.setLayout(left)
        left_w.setFixedWidth(270)

        # --- Right Side: Editor ---
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Exercise name")
        self.name_input.setStyleSheet(
            "font-size: 18px; font-weight: 600; padding: 10px;"
        )
        self.name_input.textChanged.connect(self._on_form_change)

        self.desc_label = QLabel("—")
        self.desc_label.setStyleSheet(
            "font-size: 13px; color: #60CDFF; padding: 2px 1px;"
        )

        self.mode_combo = QComboBox()
        self.mode_combo.addItem("Timer", "timer")
        self.mode_combo.addItem("Check", "check")
        self.mode_combo.currentIndexChanged.connect(self._on_mode_changed)

        self.sp_sets = QSpinBox()
        self.sp_sets.setRange(1, 99)
        self.sp_work = QSpinBox()
        self.sp_work.setRange(1, 3600)
        self.sp_prep = QSpinBox()
        self.sp_prep.setRange(0, 600)
        self.sp_rest = QSpinBox()
        self.sp_rest.setRange(0, 600)

        spinbox_style = "QSpinBox { font-size: 16px; font-weight: 600; padding: 8px 10px; }"
        for sp in (self.sp_sets, self.sp_work, self.sp_prep, self.sp_rest):
            sp.setStyleSheet(spinbox_style)
            sp.setMinimumHeight(46)
            sp.valueChanged.connect(self._on_form_change)

        self.cb_side = QCheckBox("Per-side")
        self.cb_side.setToolTip("Runs prep → work → prep → work for each set")
        self.cb_side.toggled.connect(self._on_form_change)

        self.target_input = QLineEdit()
        self.target_input.setPlaceholderText("e.g. 10–12 reps / 60s / 40m")
        self.target_input.textChanged.connect(self._on_form_change)

        self.weight_input = QLineEdit()
        self.weight_input.setPlaceholderText("e.g. 14 kg / Bodyweight / Band")
        self.weight_input.textChanged.connect(self._on_form_change)

        self.sp_rep_min = QSpinBox()
        self.sp_rep_min.setRange(0, 99)
        self.sp_rep_min.setToolTip("ค่าล่างของช่วง reps (0 = ไม่ปรับตาม week)")
        self.sp_rep_min.valueChanged.connect(self._on_form_change)
        self.sp_rep_max = QSpinBox()
        self.sp_rep_max.setRange(0, 99)
        self.sp_rep_max.setToolTip("ค่าบนของช่วง reps")
        self.sp_rep_max.valueChanged.connect(self._on_form_change)
        self.rep_suffix_input = QLineEdit()
        self.rep_suffix_input.setPlaceholderText("reps")
        self.rep_suffix_input.setToolTip("หน่วย เช่น reps / ต่อข้าง")
        self.rep_suffix_input.textChanged.connect(self._on_form_change)

        top_row = QHBoxLayout()
        top_row.setSpacing(12)
        top_row.addWidget(self._make_input_group("Type", self.mode_combo), 1)
        top_row.addWidget(self._make_input_group("Sets", self.sp_sets), 1)

        timer_page = QWidget()
        timer_layout = QVBoxLayout(timer_page)
        timer_layout.setContentsMargins(0, 0, 0, 0)
        timer_layout.setSpacing(10)

        timer_grid = QGridLayout()
        timer_grid.setSpacing(12)
        timer_grid.addWidget(self._make_input_group("Work (s)", self.sp_work), 0, 0)
        timer_grid.addWidget(self._make_input_group("Prep (s)", self.sp_prep), 0, 1)
        timer_grid.addWidget(self._make_input_group("Rest (s)", self.sp_rest), 1, 0)
        timer_layout.addLayout(timer_grid)
        timer_layout.addWidget(self.cb_side)
        timer_layout.addStretch()

        check_page = QWidget()
        check_layout = QVBoxLayout(check_page)
        check_layout.setContentsMargins(0, 0, 0, 0)
        check_layout.setSpacing(10)

        check_grid = QGridLayout()
        check_grid.setSpacing(12)
        check_grid.addWidget(self._make_input_group("Target", self.target_input), 0, 0)
        check_grid.addWidget(self._make_input_group("Weight / Equipment", self.weight_input), 0, 1)
        check_layout.addLayout(check_grid)

        prog_label = QLabel("Progressive (0 = ปิด) — reps บวกตาม week อัตโนมัติ")
        prog_label.setStyleSheet("color: #8A8A8A; font-size: 12px;")
        check_layout.addWidget(prog_label)
        prog_row = QHBoxLayout()
        prog_row.setSpacing(12)
        prog_row.addWidget(self._make_input_group("Reps Min", self.sp_rep_min), 1)
        prog_row.addWidget(self._make_input_group("Reps Max", self.sp_rep_max), 1)
        prog_row.addWidget(self._make_input_group("Unit", self.rep_suffix_input), 1)
        check_layout.addLayout(prog_row)
        check_layout.addStretch()

        self.editor_stack = QStackedWidget()
        self.editor_stack.addWidget(timer_page)
        self.editor_stack.addWidget(check_page)

        editor_box = QVBoxLayout()
        editor_box.setContentsMargins(0, 0, 0, 0)
        editor_box.setSpacing(10)
        editor_box.addWidget(self.name_input)
        editor_box.addWidget(self.desc_label)
        editor_box.addLayout(top_row)
        editor_box.addWidget(self.editor_stack)
        editor_box.addStretch()

        right_w = QWidget()
        right_w.setLayout(editor_box)

        root = QHBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(18)
        root.addWidget(left_w)
        root.addWidget(right_w, 1)

        self.refresh()

    def _make_input_group(self, label_text, widget):
        box = QWidget()
        layout = QVBoxLayout(box)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        lbl = QLabel(label_text)
        lbl.setStyleSheet("color: #8A8A8A; font-size: 12px;")
        layout.addWidget(lbl)
        layout.addWidget(widget)
        return box

    # ---------------------------------------------------------------
    def refresh(self):
        self._loading = True
        self.list.clear()
        for o in self.storage.objects:
            item = QListWidgetItem()
            item.setText(f"{o.name}\n{o.list_description(self.storage.current_week)}")
            item.setData(Qt.UserRole, o.id)
            self.list.addItem(item)
        self._loading = False

        if self.storage.objects:
            row = 0
            for i, o in enumerate(self.storage.objects):
                if o.id == self._editing_id:
                    row = i
                    break
            self.list.setCurrentRow(row)
            self._on_select(row)
        else:
            self._editing_id = None
            self._update_editor_state()

    def _current_mode(self):
        return self.mode_combo.currentData() or "timer"

    def _on_mode_changed(self):
        self.editor_stack.setCurrentIndex(0 if self._current_mode() == "timer" else 1)
        self._on_form_change()

    def _update_editor_state(self):
        enabled = self._editing_id is not None
        for w in (
            self.mode_combo, self.name_input, self.sp_sets, self.sp_work,
            self.sp_prep, self.sp_rest, self.cb_side,
            self.target_input, self.weight_input,
            self.sp_rep_min, self.sp_rep_max, self.rep_suffix_input,
        ):
            w.setEnabled(enabled)
        self.btn_del.setEnabled(enabled)
        if not enabled:
            self.name_input.clear()
            self.target_input.clear()
            self.weight_input.clear()
            self.rep_suffix_input.clear()
            self.sp_rep_min.setValue(0)
            self.sp_rep_max.setValue(0)
            self.desc_label.setText("—")

    def _on_select(self, row):
        if self._loading:
            return
        if 0 <= row < len(self.storage.objects):
            obj = self.storage.objects[row]
            self._editing_id = obj.id
            self._loading = True
            self.name_input.setText(obj.name)
            mode = getattr(obj, "mode", "timer")
            mode_index = self.mode_combo.findData(mode)
            self.mode_combo.setCurrentIndex(mode_index if mode_index >= 0 else 0)
            self.editor_stack.setCurrentIndex(0 if mode == "timer" else 1)
            self.sp_sets.setValue(obj.sets)
            self.sp_work.setValue(obj.work)
            self.sp_prep.setValue(obj.prep)
            self.sp_rest.setValue(obj.rest)
            self.cb_side.setChecked(obj.per_side)
            self.target_input.setText(obj.target)
            self.weight_input.setText(obj.weight)
            self.sp_rep_min.setValue(obj.rep_min)
            self.sp_rep_max.setValue(obj.rep_max)
            self.rep_suffix_input.setText(obj.rep_suffix)
            self._loading = False
            self._update_preview()
            self._update_editor_state()

    def _update_preview(self):
        tmp = TimerObject(
            mode=self._current_mode(),
            sets=self.sp_sets.value(), work=self.sp_work.value(),
            prep=self.sp_prep.value(), rest=self.sp_rest.value(),
            per_side=self.cb_side.isChecked(),
            target=self.target_input.text().strip(),
            weight=self.weight_input.text().strip(),
            rep_min=self.sp_rep_min.value(), rep_max=self.sp_rep_max.value(),
            rep_suffix=self.rep_suffix_input.text().strip() or "reps",
        )
        self.desc_label.setText(tmp.description(self.storage.current_week))

    def _on_form_change(self):
        if self._loading or not self._editing_id:
            return
        obj = self.storage.get_object(self._editing_id)
        if obj is None:
            return

        obj.name = self.name_input.text().strip() or "Exercise"
        obj.mode = self._current_mode()
        obj.sets = self.sp_sets.value()
        obj.work = self.sp_work.value()
        obj.prep = self.sp_prep.value()
        obj.rest = self.sp_rest.value()
        obj.per_side = self.cb_side.isChecked()
        obj.target = self.target_input.text().strip()
        obj.weight = self.weight_input.text().strip()
        obj.rep_min = self.sp_rep_min.value()
        obj.rep_max = self.sp_rep_max.value()
        obj.rep_suffix = self.rep_suffix_input.text().strip() or "reps"
        self.storage.save()

        self._update_preview()
        self._update_list_item(obj)
        self.data_changed.emit()

    def _update_list_item(self, obj):
        for i in range(self.list.count()):
            if i < len(self.storage.objects) and self.storage.objects[i].id == obj.id:
                item = self.list.item(i)
                item.setText(f"{obj.name}\n{obj.list_description(self.storage.current_week)}")
                break

    def _new(self):
        obj = TimerObject(name="New Exercise")
        self.storage.objects.append(obj)
        self.storage.save()
        self._editing_id = obj.id
        self.refresh()
        self.list.setCurrentRow(len(self.storage.objects) - 1)
        self.data_changed.emit()

    def _delete(self):
        if not self._editing_id:
            return
        used = [g.name for g in self.storage.groups if self._editing_id in g.object_ids]
        msg = "Delete this exercise?"
        if used:
            msg += f"\n\nUsed in groups: {', '.join(used)}\nIt will be removed from those groups too."
        if QMessageBox.question(self, "Confirm", msg) != QMessageBox.Yes:
            return

        for g in self.storage.groups:
            g.object_ids = [oid for oid in g.object_ids if oid != self._editing_id]

        self.storage.objects = [o for o in self.storage.objects if o.id != self._editing_id]
        self.storage.save()
        self._editing_id = None
        self.refresh()
        self.data_changed.emit()

    # 👇 อัปเดตฟังก์ชัน Import ครั้งใหญ่
    def _import_json(self):
        dlg = JSONTemplateDialog(self)
        dlg.exec()

        file_path, _ = QFileDialog.getOpenFileName(self, "Open JSON", "", "JSON Files (*.json)")
        if not file_path:
            return

        try:
            data = json.loads(Path(file_path).read_text(encoding="utf-8"))

            count_ex = 0
            count_gr = 0
            name_to_id = {}

            # 1. สร้าง Dictionary ของท่าที่มีอยู่แล้วใน Bank (ชื่อ -> ID) เผื่อเอาไว้อ้างอิง
            for obj in self.storage.objects:
                name_to_id[obj.name] = obj.id

            def process_exercise(item):
                nonlocal count_ex
                name = item.get("name", "Exercise")
                obj = TimerObject(
                    name=name,
                    sets=int(item.get("sets", 3)),
                    work=int(item.get("work", 30)),
                    prep=int(item.get("prep", 0)),
                    rest=int(item.get("rest", 0)),
                    per_side=bool(item.get("per_side", False)),
                )
                self.storage.objects.append(obj)
                name_to_id[name] = obj.id  # อัปเดต ID ล่าสุด
                count_ex += 1

            # 2. ตรวจสอบโครงสร้าง JSON (รองรับทั้งแบบ List เดิม และ Dict ใหม่)
            if isinstance(data, list):
                # แบบเก่า: List ของ Exercise
                for item in data:
                    process_exercise(item)

            elif isinstance(data, dict):
                # แบบใหม่: มี Exercises และ Groups
                if "exercises" in data:
                    for item in data["exercises"]:
                        process_exercise(item)

                if "groups" in data:
                    for g_item in data["groups"]:
                        g_name = g_item.get("name", "Imported Group")
                        seq = g_item.get("sequence", [])

                        new_group = Group(name=g_name, object_ids=[])

                        for ex_name in seq:
                            if ex_name in name_to_id:
                                new_group.object_ids.append(name_to_id[ex_name])
                            else:
                                print(f"Warning: Exercise '{ex_name}' not found. Skipped.")

                        self.storage.groups.append(new_group)
                        count_gr += 1

            # 3. บันทึกและอัปเดต UI
            self.storage.save()
            self.refresh()
            self.data_changed.emit()

            msg = f"Imported {count_ex} exercises"
            if count_gr > 0:
                msg += f" and {count_gr} groups"
            QMessageBox.information(self, "Success", msg + "!")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to import JSON:\n{e}")