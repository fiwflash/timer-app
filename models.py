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


# ตาราง Progressive Overload (อ้างอิงตาราง 6.1)
# week -> (phase, delta, setsMul)
WEEKS = {
    1: ("Foundation", 0, 1.0),
    2: ("Foundation", 0, 1.0),
    3: ("Build", 1, 1.0),
    4: ("Deload", 0, 0.6),
    5: ("Intensify", 2, 1.0),
    6: ("Intensify", 2, 1.0),
    7: ("Peak", 3, 1.0),
    8: ("Deload", 0, 0.6),
}


def progression_for(week):
    phase, delta, sets_mul = WEEKS.get(int(week), WEEKS[1])
    return phase, delta, sets_mul


# ค่า base reps ของท่าเวทหลัก 10 ท่า (ใช้ migrate ข้อมูลเดิมที่ยังไม่มี rep fields)
PROGRESSIVE_BASE = {
    "Dumbbell Floor Press": (8, 10, "reps"),
    "One-Arm Dumbbell Row": (10, 12, "ต่อข้าง"),
    "Dumbbell Shoulder Press": (8, 10, "reps"),
    "Band Triceps Pushdown": (12, 15, "reps"),
    "Pull-up (หรือ Negative)": (5, 8, "reps"),
    "Push-up บนแท่น": (12, 15, "reps"),
    "Goblet Squat": (10, 12, "reps"),
    "Romanian Deadlift (RDL)": (10, 12, "reps"),
    "Reverse Lunge": (8, 10, "ต่อข้าง"),
    "Dumbbell Lateral Raise": (12, 15, "reps"),
}


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
    rep_min: int = 0  # progressive overload base (0 = ไม่บวก reps ตาม week)
    rep_max: int = 0
    rep_suffix: str = "reps"

    def effective_sets(self, week: int = 1) -> int:
        """จำนวนเซ็ตจริงตาม week (deload W4/W8 ลด ~40% อย่างน้อย 1)"""
        _, _, sets_mul = progression_for(week)
        return max(1, round(self.sets * sets_mul))

    def effective_target(self, week: int = 1) -> str:
        """เป้า reps ตาม week (บวก delta) หรือข้อความเดิมถ้าไม่ progressive"""
        if self.mode == "check" and self.rep_min > 0 and self.rep_max > 0:
            _, delta, _ = progression_for(week)
            return f"{self.rep_min + delta}–{self.rep_max + delta} {self.rep_suffix}"
        return self.target

    def description(self, week: int = 1) -> str:
        sets = self.effective_sets(week)
        if self.mode == "check":
            target = self.effective_target(week)
            base = f"{sets} × {target}" if target else f"{sets} sets"
            if self.weight:
                base += f" · {self.weight}"
            return base

        # Timer description
        base = f"{sets} × {fmt_time(self.work)}"
        if self.per_side:
            base += " /side"
        extras = []
        if self.prep > 0:
            extras.append(f"prep {self.prep}")
        if self.rest > 0 and sets > 1:
            extras.append(f"rest {self.rest}")
        if extras:
            base += " (" + ", ".join(extras) + ")"
        return base

    def list_description(self, week: int = 1) -> str:
        kind = "Check" if self.mode == "check" else "Timer"
        return f"{kind} · {self.description(week)}"


@dataclass
class Group:
    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    name: str = "New Group"
    object_ids: list = field(default_factory=list)


class Storage:
    def __init__(self):
        self.objects = []
        self.groups = []
        self.week = 1
        self.load()
        if not self.objects:
            self.objects.append(TimerObject())
            self.save()

    @property
    def current_week(self) -> int:
        return self.week

    def set_week(self, week):
        self.week = max(1, min(8, int(week)))
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
            self.week = max(1, min(8, int(data.get("week", 1))))
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
                obj = TimerObject(**o)
                # Migration: เติม rep fields ให้ท่า progressive เดิมที่ยังไม่มี
                base = PROGRESSIVE_BASE.get(obj.name)
                if base and "rep_min" not in o and "rep_max" not in o:
                    obj.rep_min, obj.rep_max, obj.rep_suffix = base
                self.objects.append(obj)

            self.groups = [Group(**g) for g in data.get("groups", [])]
        except Exception as e:
            print(f"Load error: {e}")

    def save(self):
        data = {
            "week": self.week,
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