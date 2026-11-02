"""Tab: manage Group list — selects and orders routines."""
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QLabel, QLineEdit, QMessageBox,
)

from models import Group, Storage


class GroupsTab(QWidget):
    start_group_requested = Signal(str)

    def __init__(self, storage: Storage):
        super().__init__()
        self.storage = storage
        self._current_group = None
        self._loading = False

        # --- Left Side: Groups List ---
        self.group_list = QListWidget()
        self.group_list.setFixedWidth(280)
        self.group_list.currentRowChanged.connect(self._on_group_select)

        self.btn_new = QPushButton("+ New Group")
        self.btn_del = QPushButton("Delete")
        self.btn_new.clicked.connect(self._new_group)
        self.btn_del.clicked.connect(self._delete_group)

        left = QVBoxLayout()
        left.setSpacing(10)
        left.addWidget(QLabel("<b>Groups</b>"))
        left.addWidget(self.group_list, 1)
        left.addWidget(self.btn_new)
        left.addWidget(self.btn_del)
        left_w = QWidget()
        left_w.setLayout(left)
        left_w.setFixedWidth(300)

        # --- Right Side: Group Editor ---
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g. Monday")
        self.name_edit.textChanged.connect(self._on_name_change)

        self.avail_list = QListWidget()
        self.mem_list = QListWidget()

        self.btn_add = QPushButton("Add →")
        self.btn_remove = QPushButton("← Remove")
        self.btn_up = QPushButton("↑ Up")
        self.btn_down = QPushButton("↓ Down")
        self.btn_add.clicked.connect(self._add)
        self.btn_remove.clicked.connect(self._remove)
        self.btn_up.clicked.connect(lambda: self._move(-1))
        self.btn_down.clicked.connect(lambda: self._move(1))

        self.btn_start = QPushButton("▶  Start")
        self.btn_start.setObjectName("startBtn")
        self.btn_start.clicked.connect(self._start)

        right = QVBoxLayout()
        right.setSpacing(16)

        name_row = QHBoxLayout()
        name_row.addWidget(QLabel("Group name:"))
        name_row.addWidget(self.name_edit, 1)
        right.addLayout(name_row)

        lists_row = QHBoxLayout()
        lists_row.setSpacing(12)

        avail_box = QVBoxLayout()
        avail_box.addWidget(QLabel("Available routines"))
        avail_box.addWidget(self.avail_list, 1)

        mid_box = QVBoxLayout()
        mid_box.addStretch()
        mid_box.addWidget(self.btn_add)
        mid_box.addWidget(self.btn_remove)
        mid_box.addStretch()

        mem_box = QVBoxLayout()
        mem_box.addWidget(QLabel("Order in group"))
        mem_box.addWidget(self.mem_list, 1)
        order_box = QHBoxLayout()
        order_box.addWidget(self.btn_up)
        order_box.addWidget(self.btn_down)
        mem_box.addLayout(order_box)

        lists_row.addLayout(avail_box, 1)
        lists_row.addLayout(mid_box)
        lists_row.addLayout(mem_box, 1)

        right.addLayout(lists_row, 1)
        right.addWidget(self.btn_start)

        right_w = QWidget()
        right_w.setLayout(right)

        # --- Main Layout ---
        root = QHBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.addWidget(left_w)
        root.addWidget(right_w, 1)

        self.refresh()

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

        for w in (
            self.name_edit, self.btn_add, self.btn_remove,
            self.btn_up, self.btn_down, self.btn_start, self.btn_del,
        ):
            w.setEnabled(enabled)

        self.avail_list.clear()
        self.mem_list.clear()

        if not enabled:
            self.name_edit.setText("")
            self._loading = False
            return

        self.name_edit.setText(g.name)

        g.object_ids = [oid for oid in g.object_ids if self.storage.get_object(oid)]

        for oid in g.object_ids:
            obj = self.storage.get_object(oid)
            if obj:
                item = QListWidgetItem(obj.name)
                item.setData(Qt.UserRole, oid)
                self.mem_list.addItem(item)

        for obj in self.storage.objects:
            if obj.id not in g.object_ids:
                item = QListWidgetItem(obj.name)
                item.setData(Qt.UserRole, obj.id)
                self.avail_list.addItem(item)

        self._loading = False

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

    def _add(self):
        if not self._current_group:
            return
        item = self.avail_list.currentItem()
        if not item:
            return
        oid = item.data(Qt.UserRole)
        self._current_group.object_ids.append(oid)
        self.storage.save()
        self._update_editor()
        self.mem_list.setCurrentRow(self.mem_list.count() - 1)

    def _remove(self):
        if not self._current_group:
            return
        item = self.mem_list.currentItem()
        if not item:
            return
        oid = item.data(Qt.UserRole)
        if oid in self._current_group.object_ids:
            self._current_group.object_ids.remove(oid)
            self.storage.save()
            self._update_editor()

    def _move(self, direction):
        if not self._current_group:
            return
        item = self.mem_list.currentItem()
        if not item:
            return
        row = self.mem_list.row(item)
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
                "This group has no routines yet. Add at least one routine before starting.",
            )
            return
        self.start_group_requested.emit(self._current_group.id)