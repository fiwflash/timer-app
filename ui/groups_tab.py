"""Tab: manage Group list — selects and orders routines via double-click."""
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QLabel, QLineEdit, QMessageBox, QComboBox,
)

from models import Group, Storage, progression_for


class GroupsTab(QWidget):
    start_group_requested = Signal(str)
    week_changed = Signal()

    def __init__(self, storage: Storage):
        super().__init__()
        self.storage = storage
        self._current_group = None
        self._loading = False

        # --- Left Side: Groups List ---
        self.group_list = QListWidget()
        self.group_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.group_list.currentRowChanged.connect(self._on_group_select)

        self.btn_new = QPushButton("+ New")
        self.btn_del = QPushButton("Delete")
        self.btn_new.clicked.connect(self._new_group)
        self.btn_del.clicked.connect(self._delete_group)

        left = QVBoxLayout()
        left.setSpacing(8)
        left.addWidget(self.group_list, 1)

        left_buttons = QHBoxLayout()
        left_buttons.setSpacing(8)
        left_buttons.addWidget(self.btn_new, 1)
        left_buttons.addWidget(self.btn_del)
        left.addLayout(left_buttons)

        left_w = QWidget()
        left_w.setLayout(left)
        left_w.setFixedWidth(270)

        # --- Right Side: Group Editor ---
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Group name")
        self.name_edit.setStyleSheet(
            "font-size: 16px; font-weight: 600; padding: 9px 10px;"
        )
        self.name_edit.textChanged.connect(self._on_name_change)

        self.avail_list = QListWidget()
        self.mem_list = QListWidget()

        for list_widget in (self.avail_list, self.mem_list):
            list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            list_widget.setWordWrap(True)

        self.avail_list.setToolTip("Double-click to add to the group")
        self.mem_list.setToolTip("Double-click to remove from the group")

        self.avail_list.itemDoubleClicked.connect(self._on_avail_double_click)
        self.mem_list.itemDoubleClicked.connect(self._on_mem_double_click)

        self.btn_up = QPushButton("↑")
        self.btn_down = QPushButton("↓")
        self.btn_up.setToolTip("Move up")
        self.btn_down.setToolTip("Move down")
        for btn in (self.btn_up, self.btn_down):
            btn.setFixedWidth(38)
        self.btn_up.clicked.connect(lambda: self._move(-1))
        self.btn_down.clicked.connect(lambda: self._move(1))

        self.btn_start = QPushButton("Start")
        self.btn_start.setObjectName("startBtn")
        self.btn_start.setMinimumHeight(44)
        self.btn_start.clicked.connect(self._start)

        right = QVBoxLayout()
        right.setSpacing(10)
        right.addWidget(self.name_edit)

        lists_row = QHBoxLayout()
        lists_row.setSpacing(12)

        avail_box = QVBoxLayout()
        avail_box.setSpacing(4)
        avail_box.addWidget(self._section_label("Routines"))
        avail_box.addWidget(self.avail_list, 1)

        mem_box = QVBoxLayout()
        mem_box.setSpacing(4)
        mem_box.addWidget(self._section_label("Order"))
        mem_box.addWidget(self.mem_list, 1)

        order_box = QHBoxLayout()
        order_box.setSpacing(8)
        order_box.addWidget(self.btn_up)
        order_box.addWidget(self.btn_down)
        order_box.addStretch()
        mem_box.addLayout(order_box)

        lists_row.addLayout(avail_box, 1)
        lists_row.addLayout(mem_box, 1)

        right.addLayout(lists_row, 1)
        right.addWidget(self.btn_start)

        right_w = QWidget()
        right_w.setLayout(right)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(18, 18, 18, 18)
        outer.setSpacing(12)

        week_bar = QHBoxLayout()
        week_bar.setSpacing(8)
        week_lbl = QLabel("Week")
        week_lbl.setStyleSheet("color: #8A8A8A; font-size: 13px;")
        self.week_combo = QComboBox()
        for w in range(1, 9):
            phase, _, _ = progression_for(w)
            self.week_combo.addItem(f"Week {w} · {phase}", w)
        self.week_combo.setCurrentIndex(self.storage.week - 1)
        self.week_combo.currentIndexChanged.connect(self._on_week_change)
        week_bar.addWidget(week_lbl)
        week_bar.addWidget(self.week_combo)
        week_bar.addStretch()
        outer.addLayout(week_bar)

        root = QHBoxLayout()
        root.setSpacing(18)
        root.addWidget(left_w)
        root.addWidget(right_w, 1)
        outer.addLayout(root, 1)

        self.refresh()

    @staticmethod
    def _section_label(text):
        label = QLabel(text)
        label.setStyleSheet(
            "color: #8A8A8A; font-size: 12px; padding-left: 2px;"
        )
        return label

    def _on_week_change(self):
        if self._loading:
            return
        self.storage.set_week(self.week_combo.currentData())
        self._update_editor()
        self.week_changed.emit()

    # ---------------------------------------------------------------
    def refresh(self):
        self._loading = True
        current_id = self._current_group.id if self._current_group else None
        self.group_list.clear()
        for g in self.storage.groups:
            self.group_list.addItem(g.name)
        self._loading = False

        sel = -1
        for i, g in enumerate(self.storage.groups):
            if g.id == current_id:
                sel = i
                break

        if sel >= 0:
            self._current_group = self.storage.groups[sel]
            self.group_list.setCurrentRow(sel)
        elif self.storage.groups:
            self._current_group = self.storage.groups[0]
            self.group_list.setCurrentRow(0)
        else:
            self._current_group = None

        self._update_editor()

    def _on_group_select(self, row):
        if self._loading:
            return
        if 0 <= row < len(self.storage.groups):
            self._current_group = self.storage.groups[row]
        else:
            self._current_group = None
        self._update_editor()

    def _update_editor(self):
        self._loading = True
        g = self._current_group
        enabled = g is not None

        for w in (self.name_edit, self.btn_up, self.btn_down, self.btn_start, self.btn_del):
            w.setEnabled(enabled)

        self.avail_list.clear()
        self.mem_list.clear()

        if not enabled:
            self.name_edit.setText("")
            self._loading = False
            return

        self.name_edit.setText(g.name)

        # Bank List (ทุกท่า)
        for obj in self.storage.objects:
            item = QListWidgetItem(f"{obj.name}\n{obj.list_description(self.storage.current_week)}")
            item.setData(Qt.UserRole, obj.id)
            self.avail_list.addItem(item)

        # Sequence List (ใช้ Index อ้างอิง ไม่ใช่ ID ตรงๆ)
        for idx, oid in enumerate(g.object_ids):
            obj = self.storage.get_object(oid)
            if obj:
                item = QListWidgetItem(f"{obj.name}\n{obj.list_description(self.storage.current_week)}")
                # เก็บ Index ใน Group ไว้ใช้ลบ (เพราะมี ID ซ้ำได้)
                item.setData(Qt.UserRole, idx)
                self.mem_list.addItem(item)

        self._loading = False

    def _on_avail_double_click(self, item):
        if not self._current_group:
            return
        oid = item.data(Qt.UserRole)
        # เพิ่มต่อท้าย Group (ซ้ำได้)
        self._current_group.object_ids.append(oid)
        self.storage.save()
        self._update_editor()
        # เลื่อน Scroll ลงไปล่างสุด
        self.mem_list.scrollToBottom()

    def _on_mem_double_click(self, item):
        if not self._current_group:
            return
        idx = item.data(Qt.UserRole)
        if 0 <= idx < len(self._current_group.object_ids):
            # ลบตัวที่คลิกออก
            del self._current_group.object_ids[idx]
            self.storage.save()
            self._update_editor()

    def _on_name_change(self, text):
        if self._loading or not self._current_group:
            return
        self._current_group.name = text
        self.storage.save()

        for i in range(self.group_list.count()):
            if i < len(self.storage.groups) and \
                    self.storage.groups[i].id == self._current_group.id:
                self.group_list.item(i).setText(text)
                break

    def _new_group(self):
        g = Group()
        self.storage.groups.append(g)
        self.storage.save()
        self._current_group = g
        self.refresh()

    def _delete_group(self):
        if not self._current_group:
            return
        reply = QMessageBox.question(
            self, "Confirm", f"Delete group '{self._current_group.name}'?"
        )
        if reply != QMessageBox.Yes:
            return
        self.storage.groups = [g for g in self.storage.groups if g.id != self._current_group.id]
        self.storage.save()
        self._current_group = None
        self.refresh()

    def _move(self, direction):
        if not self._current_group:
            return
        row = self.mem_list.currentRow()
        if row < 0:
            return
        new_row = row + direction
        ids = self._current_group.object_ids
        if new_row < 0 or new_row >= len(ids):
            return
        ids[row], ids[new_row] = ids[new_row], ids[row]
        self.storage.save()
        self._update_editor()
        self.mem_list.setCurrentRow(new_row)

    def _start(self):
        if not self._current_group:
            return
        if not self._current_group.object_ids:
            QMessageBox.warning(
                self, "Empty Group",
                "This group has no routines yet. Double-click items in the Bank to add them.",
            )
            return
        self.start_group_requested.emit(self._current_group.id)