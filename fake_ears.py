import threading
import time
from enum import Enum, auto
from dataclasses import dataclass
from typing import Optional


class EarMode(Enum):
    FOLLOW = auto()
    THINK = auto()
    STOPPED = auto()
    SCAN = auto()
    FAST = auto()


@dataclass(frozen=True)
class EarBehaviour:
    move_rate: int   # Hz
    scan_rate: int   # Hz


EAR_BEHAVIOURS = {
    EarMode.FOLLOW: EarBehaviour(move_rate=0,  scan_rate=10),
    EarMode.THINK:  EarBehaviour(move_rate=50, scan_rate=0),
    EarMode.STOPPED: EarBehaviour(move_rate=0,  scan_rate=0),
    EarMode.SCAN:   EarBehaviour(move_rate=20, scan_rate=10),
    EarMode.FAST:   EarBehaviour(move_rate=75, scan_rate=20),
}


class RepeatingTimer:
    """Simple repeating timer using a thread."""

    def __init__(self, rate_hz: int, callback):
        self._period = 1.0 / rate_hz
        self._callback = callback
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    def start(self):
        if self._thread is not None:
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        while not self._stop_event.is_set():
            start = time.time()
            self._callback()
            elapsed = time.time() - start
            time.sleep(max(0.0, self._period - elapsed))

    def stop(self):
        if self._thread is None:
            return
        self._stop_event.set()
        self._thread.join()
        self._thread = None


class FakeEars:
    """
    Simulation / placeholder implementation of K9's laser ears.
    Mirrors the behaviour of the Espruino firmware.
    """

    def __init__(self) -> None:
        self._mode: EarMode = EarMode.STOPPED
        self._move_timer: Optional[RepeatingTimer] = None
        self._scan_timer: Optional[RepeatingTimer] = None

        # Internal state (equivalent to Espruino globals)
        self._step = 0
        self._direction = 1
        self._num_steps = 50

        print("[EARS] Initialised in STOPPED mode")

    # ─────────────────────────────
    # Public API
    # ─────────────────────────────

    def set_mode(self, mode: EarMode):
        if mode == self._mode:
            return

        print(f"[EARS] Mode change: {self._mode.name} → {mode.name}")
        self._mode = mode
        self._apply_behaviour(EAR_BEHAVIOURS[mode])

    # ─────────────────────────────
    # Behaviour application
    # ─────────────────────────────

    def _apply_behaviour(self, behaviour: EarBehaviour):
        self._stop_timers()

        if behaviour.move_rate > 0:
            self._move_timer = RepeatingTimer(
                behaviour.move_rate,
                self._move_ears
            )
            self._move_timer.start()
        else:
            self._reset_ears()

        if behaviour.scan_rate > 0:
            self._scan_timer = RepeatingTimer(
                behaviour.scan_rate,
                self._take_readings
            )
            self._scan_timer.start()

    def _stop_timers(self):
        if self._move_timer:
            self._move_timer.stop()
            self._move_timer = None
        if self._scan_timer:
            self._scan_timer.stop()
            self._scan_timer = None

    # ─────────────────────────────
    # Behaviour implementations
    # ─────────────────────────────

    def _move_ears(self):
        """Equivalent of moveEars() in Espruino."""
        self._step += self._direction

        if self._step >= self._num_steps:
            self._direction = -1
            self._step = self._num_steps - 1
        elif self._step <= 0:
            self._direction = 1
            self._step = 1

        print(f"[EARS] Moving ears: step={self._step}, dir={self._direction}")

    def _reset_ears(self):
        """Equivalent of resetEars()."""
        self._step = self._num_steps // 2
        self._direction = 1
        print("[EARS] Ears reset to forward position")

    def _take_readings(self):
        """Equivalent of takeReading()."""
        # In simulation, just emit placeholders
        left_distance = 1.2   # metres
        right_distance = 1.3  # metres
        print(
            f"[EARS] LIDAR readings: "
            f"L={left_distance:.2f}m, R={right_distance:.2f}m"
        )

    # ─────────────────────────────
    # Convenience wrappers (match old commands)
    # ─────────────────────────────

    def follow(self):
        self.set_mode(EarMode.FOLLOW)

    def think(self):
        self.set_mode(EarMode.THINK)

    def stop(self):
        self.set_mode(EarMode.STOPPED)

    def scan(self):
        self.set_mode(EarMode.SCAN)

    def fast(self):
        self.set_mode(EarMode.FAST)
