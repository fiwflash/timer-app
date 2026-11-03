"""Loud alert sounds for the interval timer.

The bundled bell samples are trimmed, normalised to full scale, and combined
with short synthesised tones so the alerts cut through background music.
Sounds are generated once per run in the system temp folder and played with
winsound, so there are still no extra dependencies.

Public API:
    prewarm()              build sounds in the background
    play_beep(urgent)      countdown pip (3, 2, 1)
    play_bell()            phase-change signal
    play_object_done()     one routine finished, waiting for the next
    play_finish()          the whole workout is complete
"""
from __future__ import annotations

import array
import math
import struct
import sys
import tempfile
import threading
import wave
from pathlib import Path

try:
    import winsound
    HAS_WINSOUND = True
except ImportError:
    winsound = None
    HAS_WINSOUND = False

SAMPLE_RATE = 48000
PEAK = 0.98
SOUND_VERSION = "v2"


# ---------------------------------------------------------------- resources
def resource_path(relative_path):
    """ หา Path ของไฟล์ที่ถูก bundle ไปกับ .exe """
    try:
        base_path = Path(sys._MEIPASS)
    except Exception:
        base_path = Path(__file__).resolve().parent
    return base_path / relative_path


BELL_FILE = resource_path("bell.wav")
BELL2_FILE = resource_path("bell2.wav")

_CACHE_DIR = Path(tempfile.gettempdir()) / "interval_timer_sounds"
_sounds: dict[str, Path] = {}
_sounds_ready = False
_lock = threading.Lock()


# ---------------------------------------------------------------- wav helpers
def _resample(values, source_rate, target_rate):
    if source_rate == target_rate or not values:
        return values
    count = int(len(values) * target_rate / source_rate)
    ratio = source_rate / target_rate
    out = []
    last = len(values) - 1
    for i in range(count):
        pos = i * ratio
        left = int(pos)
        right = min(left + 1, last)
        frac = pos - left
        out.append(values[left] * (1.0 - frac) + values[right] * frac)
    return out


def _read_wav(path):
    """Read a wav file as mono float samples in [-1, 1]."""
    with wave.open(str(path), "rb") as w:
        channels = w.getnchannels()
        width = w.getsampwidth()
        rate = w.getframerate()
        raw = w.readframes(w.getnframes())

    if width == 1:
        values = [(b - 128) / 128.0 for b in raw]
    elif width == 2:
        values = [v / 32768.0 for v in struct.unpack("<%dh" % (len(raw) // 2), raw)]
    elif width == 3:
        values = []
        for i in range(0, len(raw) - 2, 3):
            v = raw[i] | (raw[i + 1] << 8) | (raw[i + 2] << 16)
            if v & 0x800000:
                v -= 0x1000000
            values.append(v / 8388608.0)
    elif width == 4:
        values = [v / 2147483648.0 for v in struct.unpack("<%di" % (len(raw) // 4), raw)]
    else:
        raise ValueError("Unsupported wav sample width")

    if channels > 1:
        values = [
            sum(values[i:i + channels]) / channels
            for i in range(0, len(values), channels)
        ]
    return _resample(values, rate, SAMPLE_RATE)


def _trim_silence(values, threshold=0.008, pad_start=0.005, pad_end=0.05):
    start = next((i for i, v in enumerate(values) if abs(v) >= threshold), None)
    if start is None:
        return []
    end = next(
        (i for i in range(len(values) - 1, -1, -1) if abs(values[i]) >= threshold),
        start,
    )
    return (
        [0.0] * int(pad_start * SAMPLE_RATE)
        + values[start:end + 1]
        + [0.0] * int(pad_end * SAMPLE_RATE)
    )


def _normalize(values, peak=PEAK):
    loudest = max((abs(v) for v in values), default=0.0)
    if loudest <= 0:
        return list(values)
    scale = peak / loudest
    return [v * scale for v in values]


def _fade(values, fade_in=0.004, fade_out=0.08):
    out = list(values)
    n = len(out)
    if not n:
        return out
    fade_in_n = min(n, max(1, int(fade_in * SAMPLE_RATE)))
    fade_out_n = min(n, max(1, int(fade_out * SAMPLE_RATE)))
    for i in range(fade_in_n):
        out[i] *= i / fade_in_n
    for i in range(fade_out_n):
        out[n - 1 - i] *= i / fade_out_n
    return out


def _silence(seconds):
    return [0.0] * int(seconds * SAMPLE_RATE)


def _concat(*parts):
    out = []
    for part in parts:
        out.extend(part)
    return out


def _tone(frequency, duration, harmonics=((1, 1.0), (2, 0.38), (3, 0.18)), decay=1.4):
    """Short, punchy tone with a fast attack and a smooth decay."""
    count = max(1, int(duration * SAMPLE_RATE))
    attack = max(1, int(0.003 * SAMPLE_RATE))
    out = [0.0] * count
    for i in range(count):
        t = i / SAMPLE_RATE
        envelope = (1.0 - i / count) ** decay
        if i < attack:
            envelope *= i / attack
        sample = 0.0
        for harmonic, amplitude in harmonics:
            sample += amplitude * math.sin(2.0 * math.pi * frequency * harmonic * t)
        out[i] = sample * envelope
    return out


def _bell(path, max_seconds):
    """Load a bundled bell, remove its lead-in silence and normalise it."""
    try:
        values = _trim_silence(_read_wav(path))
        if not values:
            return None
        values = _normalize(values)[:int(max_seconds * SAMPLE_RATE)]
        return _fade(values, fade_out=0.12)
    except Exception:
        return None


def _synthetic_bell():
    """Fallback chime used only when the bundled wav cannot be read."""
    return _concat(
        _tone(880.0, 0.55, decay=1.6),
        _tone(1174.7, 0.75, decay=1.8),
        _tone(1568.0, 0.9, decay=2.0),
    )


# ---------------------------------------------------------------- cue builders
def _build_tick(urgent=False):
    if urgent:
        # Two quick high pips: a clear "get ready" before the phase changes.
        values = _concat(
            _tone(1864.7, 0.085, decay=1.1),
            _silence(0.04),
            _tone(2489.0, 0.13, decay=1.2),
        )
        return _normalize(_fade(values, fade_out=0.03))
    return _normalize(_fade(_tone(1760.0, 0.14, decay=1.1), fade_out=0.04))


def _build_phase():
    # A sharp attention pip followed by the familiar bell.
    pip = _tone(1568.0, 0.11, harmonics=((1, 1.0), (2, 0.45), (3, 0.2)), decay=1.1)
    bell = _bell(BELL_FILE, 1.8) or _synthetic_bell()
    return _normalize(_fade(_concat(pip, _silence(0.04), bell), fade_out=0.08))


def _build_object_done():
    bell = _bell(BELL2_FILE, 2.0) or _synthetic_bell()
    return _normalize(bell)


def _build_finish():
    # Rising three-note motif, then the louder bell as a clear finish.
    notes = []
    for frequency in (1046.5, 1318.5, 1568.0):
        notes.extend(_tone(frequency, 0.13, decay=1.1))
        notes.extend(_silence(0.035))
    bell = _bell(BELL2_FILE, 1.3) or _synthetic_bell()
    return _normalize(_fade(_concat(notes, bell), fade_out=0.15))


def _write_wav(path, values):
    values = _normalize(values)
    frames = array.array("h")
    for value in values:
        clamped = max(-1.0, min(1.0, value))
        frames.append(int(clamped * 32767))
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SAMPLE_RATE)
        w.writeframes(frames.tobytes())


# ---------------------------------------------------------------- sound cache
def _ensure_sounds():
    global _sounds_ready
    if _sounds_ready:
        return
    with _lock:
        if _sounds_ready:
            return
        try:
            _CACHE_DIR.mkdir(parents=True, exist_ok=True)
            builders = {
                "tick": lambda: _build_tick(False),
                "tick_final": lambda: _build_tick(True),
                "phase": _build_phase,
                "object_done": _build_object_done,
                "finish": _build_finish,
            }
            for name, builder in builders.items():
                path = _CACHE_DIR / f"{name}_{SOUND_VERSION}.wav"
                try:
                    _write_wav(path, builder())
                    _sounds[name] = path
                except Exception as exc:
                    print(f"Sound '{name}' could not be generated: {exc}")
        except Exception as exc:
            print(f"Sound cache error: {exc}")
        finally:
            _sounds_ready = True


def prewarm():
    """Generate the sound files in the background while the app starts."""
    if HAS_WINSOUND:
        threading.Thread(target=_ensure_sounds, daemon=True).start()


# ---------------------------------------------------------------- playback
def _play(name):
    if not HAS_WINSOUND:
        return
    _ensure_sounds()
    path = _sounds.get(name)
    if path is not None:
        try:
            winsound.PlaySound(
                str(path),
                winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT,
            )
            return
        except Exception:
            pass

    # Last-resort fallback: a plain high beep.
    def _beep():
        try:
            winsound.Beep(1500, 140)
        except Exception:
            pass

    threading.Thread(target=_beep, daemon=True).start()


def play_beep(urgent=False):
    _play("tick_final" if urgent else "tick")


def play_bell():
    _play("phase")


def play_object_done():
    _play("object_done")


def play_finish():
    _play("finish")
