"""Bell + beep sounds (Windows only via winsound)."""
import sys
import threading
from pathlib import Path

try:
    import winsound
    HAS_WINSOUND = True
except ImportError:
    HAS_WINSOUND = False

def resource_path(relative_path):
    """ หา Path ของไฟล์ที่ถูก bundle ไปกับ .exe """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = Path(__file__).resolve().parent
    return Path(base_path) / relative_path

BELL_FILE = resource_path("bell.wav")


def play_bell():
    if not HAS_WINSOUND or not BELL_FILE.exists():
        return
    try:
        winsound.PlaySound(
            str(BELL_FILE),
            winsound.SND_FILENAME | winsound.SND_ASYNC,
        )
    except Exception:
        pass


def play_beep():
    if not HAS_WINSOUND:
        return

    def _run():
        try:
            winsound.Beep(880, 80)
        except Exception:
            pass

    threading.Thread(target=_run, daemon=True).start()