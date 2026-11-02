"""Data models + storage (JSON) + time formatting."""
import json
import uuid
from dataclasses import dataclass, field, asdict
from pathlib import Path

# หาที่อยู่ของโปรแกรม (ถ้ารันเป็น .exe ให้ใช้โฟลเดอร์ที่ .exe อยู่)
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).resolve().parent

DATA_FILE = BASE_DIR / "data.json"


def fmt_time(sec: int) -> str:
    m, s = divmod(sec, 60)
    if m and s:
        return f"{m}m {s}s"
    if m:
        return f"{m}m"
    return f"{s}s"


def fmt_clock(sec: int) -> str:
    sec = max(0, int(sec))
    m, s = divmod(sec, 60)
    return f"{m:02d}:{s:02d}"


@dataclass
class TimerObject:
    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    sets: int = 3
    work: int = 30
    prep: int = 5
    rest: int = 15
    per_side: bool = False
    custom_name: str = ""  # 👈 เพิ่มช่องนี้

    @property
    def name(self) -> str:
        # ถ้าผู้ใช้ตั้งชื่อเอง ให้ใช้ชื่อนั้น
        if self.custom_name.strip():
            return self.custom_name.strip()
            
        # ถ้าไม่ได้ตั้ง ให้สร้างอัตโนมัติแบบเดิม
        base = f"{self.sets} × {fmt_time(self.work)}"
        if self.per_side:
            base += " /side"
        extras = []
        if self.prep > 0:
            extras.append(f"prep {self.prep}")
        if self.rest > 0 and self.sets > 1:
            extras.append(f"rest {self.rest}")
        if extras:
            base += " (" + ", ".join(extras) + ")"
        return base

    @property
    def auto_name(self) -> str:
        # สร้างชื่ออัตโนมัติแยกออกมา เพื่อเอาไปโชว์เป็น Placeholder
        base = f"{self.sets} × {fmt_time(self.work)}"
        if self.per_side:
            base += " /side"
        extras = []
        if self.prep > 0:
            extras.append(f"prep {self.prep}")
        if self.rest > 0 and self.sets > 1:
            extras.append(f"rest {self.rest}")
        if extras:
            base += " (" + ", ".join(extras) + ")"
        return base


@dataclass
class Group:
    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    name: str = "New Group"
    object_ids: list = field(default_factory=list)


class Storage:
    def __init__(self):
        self.objects = []
        self.groups = []
        self.load()
        if not self.objects:
            self.objects.append(TimerObject())
            self.save()

    def load(self):
        if not DATA_FILE.exists():
            return
        try:
            data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
            # ใช้ **o เพื่อรับค่า ถ้าไฟล์เก่าไม่มี custom_name มันจะใช้ค่า default ""
            self.objects = [TimerObject(**o) for o in data.get("objects", [])]
            self.groups = [Group(**g) for g in data.get("groups", [])]
        except Exception as e:
            print(f"Load error: {e}")

    def save(self):
        data = {
            "objects": [asdict(o) for o in self.objects],
            "groups": [asdict(g) for g in self.groups],
        }
        try:
            DATA_FILE.write_text(
                json.dumps(data, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception as e:
            print(f"Save error: {e}")

    def get_object(self, oid):
        for o in self.objects:
            if o.id == oid:
                return o
        return None