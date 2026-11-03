"""Data models + storage (JSON) + time formatting."""
import json
import shutil
import sys
import uuid
from dataclasses import dataclass, field, asdict
from pathlib import Path


def _app_dir() -> Path:
    """โฟลเดอร์ที่ใช้เก็บ data.json — ข้าง ๆ .exe เมื่อ build แล้ว"""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


BASE_DIR = _app_dir()
DATA_FILE = BASE_DIR / "data.json"
DEFAULT_DATA_FILE = Path(getattr(sys, "_MEIPASS", BASE_DIR)) / "default_data.json"


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
    name: str = "New Exercise"
    mode: str = "timer"  # "timer" | "check"
    sets: int = 3
    work: int = 30
    prep: int = 5
    rest: int = 15
    per_side: bool = False
    target: str = ""  # check mode: "10–12 reps", "60s", "40m"
    weight: str = ""  # check mode: "14 kg", "Bodyweight", "Band"

    @property
    def description(self) -> str:
        if self.mode == "check":
            base = f"{self.sets} × {self.target}" if self.target else f"{self.sets} sets"
            if self.weight:
                base += f" · {self.weight}"
            return base

        # Timer description
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
    def list_description(self) -> str:
        kind = "Check" if self.mode == "check" else "Timer"
        return f"{kind} · {self.description}"


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
        # ครั้งแรก: คัดลอก template ข้อมูลเริ่มต้นมาเป็น data.json
        if not DATA_FILE.exists() and DEFAULT_DATA_FILE.exists() \
                and DEFAULT_DATA_FILE != DATA_FILE:
            try:
                shutil.copy2(DEFAULT_DATA_FILE, DATA_FILE)
            except Exception as e:
                print(f"Seed data copy error: {e}")

        if not DATA_FILE.exists():
            return
        try:
            data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
            self.objects = []
            for o in data.get("objects", []):
                # Backward compatibility: ถ้าไฟล์เก่ามี custom_name ให้ย้ายมาเป็น name
                if "custom_name" in o and o["custom_name"]:
                    o["name"] = o.pop("custom_name")
                elif "custom_name" in o:
                    o.pop("custom_name")
                # ถ้าไม่มี name ให้ใส่ Default
                if "name" not in o:
                    o["name"] = "Exercise"
                self.objects.append(TimerObject(**o))

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