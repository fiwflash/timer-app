"""Tab: manage TimerObject list (routines)."""
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QListWidget, QPushButton, QLabel, QLineEdit,
    QSpinBox, QCheckBox, QMessageBox,
)

from models import TimerObject, Storage


class ObjectsTab(QWidget):
    data_changed = Signal()

    def __init__(self, storage: Storage):
        super().__init__()
        self.storage = storage
        self._editing_id = None
        self._loading = False

        # --- Left Side: List ---
        self.list = QListWidget()
        self.list.setFixedWidth(280)
        self.list.currentRowChanged.connect(self._on_select)

        self.btn_new = QPushButton("+ New Routine")
        self.btn_del = QPushButton("Delete")
        self.btn_new.clicked.connect(self._new)
        self.btn_del.clicked.connect(self._delete)

        left = QVBoxLayout()
        left.setSpacing(10)
        left.addWidget(QLabel("<b>Routines</b>"))
        left.addWidget(self.list, 1)
        left.addWidget(self.btn_new)
        left.addWidget(self.btn_del)

        left_w = QWidget()
        left_w.setLayout(left)
        left_w.setFixedWidth(300)

        # --- Right Side: Editor ---
        self.sp_sets = QSpinBox()
        self.sp_sets.setRange(1, 99)
        
        self.sp_work = QSpinBox()
        self.sp_work.setRange(1, 3600)
        
        self.sp_prep = QSpinBox()
        self.sp_prep.setRange(0, 600)
        
        self.sp_rest = QSpinBox()
        self.sp_rest.setRange(0, 600)

        spinbox_style = """
            QSpinBox {
                font-size: 24px;
                font-weight: bold;
                color: #FFFFFF;
                padding: 10px;
                background-color: #252525;
                border: 1px solid #444;
                border-radius: 8px;
            }
            QSpinBox:focus {
                border: 1px solid #60CDFF;
                background-color: #2D2D2D;
            }
        """
        for sp in (self.sp_sets, self.sp_work, self.sp_prep, self.sp_rest):
            sp.setStyleSheet(spinbox_style)
            sp.setMinimumHeight(65)
            sp.valueChanged.connect(self._on_form_change)

        self.cb_side = QCheckBox("Per-side (prep-work-prep-work)")
        self.cb_side.setStyleSheet("font-size: 15px; margin-top: 10px;")
        self.cb_side.toggled.connect(self._on_form_change)

        grid = QGridLayout()
        grid.setSpacing(20)
        grid.addWidget(self._make_input_group("Sets", self.sp_sets), 0, 0)
        grid.addWidget(self._make_input_group("Work (sec)", self.sp_work), 0, 1)
        grid.addWidget(self._make_input_group("Prep (sec)", self.sp_prep), 1, 0)
        grid.addWidget(self._make_input_group("Rest (sec)", self.sp_rest), 1, 1)

        # 👇 เปลี่ยนจาก QLabel เป็น QLineEdit สำหรับกรอกชื่อ
        self.name_input = QLineEdit()
        self.name_input.setObjectName("previewBox")
        self.name_input.setStyleSheet("font-size: 20px; font-weight: bold; padding: 16px;")
        self.name_input.textChanged.connect(self._on_name_changed)

        editor_box = QVBoxLayout()
        editor_box.setSpacing(16)
        
        title = QLabel("<b>Routine Details</b>")
        title.setStyleSheet("font-size: 20px; margin-bottom: 10px;")
        editor_box.addWidget(title)
        
        editor_box.addLayout(grid)
        editor_box.addWidget(self.cb_side)
        
        editor_box.addSpacing(10)
        editor_box.addWidget(QLabel("Custom name (leave blank for auto-generate):"))
        editor_box.addWidget(self.name_input)
        
        editor_box.addStretch()

        right_w = QWidget()
        right_w.setLayout(editor_box)

        root = QHBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.addWidget(left_w)
        root.addWidget(right_w, 1)

        self.refresh()

    def _make_input_group(self, label_text, widget):
        box = QWidget()
        layout = QVBoxLayout(box)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        lbl = QLabel(label_text)
        lbl.setStyleSheet("color: #A0A0A0; font-size: 15px; font-weight: 600;")
        
        layout.addWidget(lbl)
        layout.addWidget(widget)
        return box

    # ---------------------------------------------------------------
    def refresh(self):
        self._loading = True
        self.list.clear()
        for o in self.storage.objects:
            self.list.addItem(o.name)
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

    def _update_editor_state(self):
        enabled = self._editing_id is not None
        for w in (self.sp_sets, self.sp_work, self.sp_prep, self.sp_rest, self.cb_side, self.name_input):
            w.setEnabled(enabled)
        self.btn_del.setEnabled(enabled)
        if not enabled:
            self.name_input.clear()
            self.name_input.setPlaceholderText("—")

    def _on_select(self, row):
        if self._loading:
            return
        if 0 <= row < len(self.storage.objects):
            obj = self.storage.objects[row]
            self._editing_id = obj.id
            self._loading = True
            
            self.sp_sets.setValue(obj.sets)
            self.sp_work.setValue(obj.work)
            self.sp_prep.setValue(obj.prep)
            self.sp_rest.setValue(obj.rest)
            self.cb_side.setChecked(obj.per_side)
            self.name_input.setText(obj.custom_name) # 👈 โหลด custom_name ลงช่อง
            
            self._loading = False
            self._update_placeholder()
            self._update_editor_state()
        else:
            self._editing_id = None
            self._update_editor_state()

    def _update_placeholder(self):
        # อัปเดตข้อความจางๆ ว่า "ถ้าไม่กรอก จะเป็นชื่อนี้"
        tmp = TimerObject(
            sets=self.sp_sets.value(),
            work=self.sp_work.value(),
            prep=self.sp_prep.value(),
            rest=self.sp_rest.value(),
            per_side=self.cb_side.isChecked(),
        )
        self.name_input.setPlaceholderText(tmp.auto_name)

    def _on_form_change(self):
        if self._loading or not self._editing_id:
            return
        obj = self.storage.get_object(self._editing_id)
        if obj is None:
            return
            
        obj.sets = self.sp_sets.value()
        obj.work = self.sp_work.value()
        obj.prep = self.sp_prep.value()
        obj.rest = self.sp_rest.value()
        obj.per_side = self.cb_side.isChecked()
        self.storage.save()

        self._update_placeholder()
        self._update_list_item(obj)
        self.data_changed.emit()

    def _on_name_changed(self, text):
        if self._loading or not self._editing_id:
            return
        obj = self.storage.get_object(self._editing_id)
        if obj is None:
            return
            
        obj.custom_name = text
        self.storage.save()
        self._update_list_item(obj)
        self.data_changed.emit()

    def _update_list_item(self, obj):
        # อัปเดตชื่อในลิสต์ด้านซ้าย
        for i in range(self.list.count()):
            if i < len(self.storage.objects) and \
                    self.storage.objects[i].id == obj.id:
                self.list.item(i).setText(obj.name)
                break

    def _new(self):
        obj = TimerObject()
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
        msg = "Delete this routine?"
        if used:
            msg += f"\n\nUsed in groups: {', '.join(used)}\nIt will be removed from those groups too."
        if QMessageBox.question(self, "Confirm", msg) != QMessageBox.Yes:
            return

        for g in self.storage.groups:
            if self._editing_id in g.object_ids:
                g.object_ids.remove(self._editing_id)
        self.storage.objects = [o for o in self.storage.objects if o.id != self._editing_id]
        self.storage.save()
        self._editing_id = None
        self.refresh()
        self.data_changed.emit()