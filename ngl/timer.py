# timers.py
import time
import logging
from .loop_watchdog import get_loop_lag_snapshot

logger = logging.getLogger("checkpoint")
_has_thread_time = hasattr(time, "thread_time_ns")

class CheckTimer:
    """
    Drop-in checkpoint timer.
    Use: t = CheckTimer("add_message"); t.cp("after db.get"); ...
    Emits wall time, CPU time (process & thread), off-CPU estimate, and loop lag.
    """

    def __init__(self, name: str):
        self.name = name
        self._start_wall = time.perf_counter_ns()
        self._start_cpu_proc = time.process_time_ns()
        self._start_cpu_thread = time.thread_time_ns() if _has_thread_time else None
        self._last_wall = self._start_wall
        self._last_cpu_proc = self._start_cpu_proc
        self._last_cpu_thread = self._start_cpu_thread
        logger.info(f"[{self.name}] start")

    def cp(self, label: str):
        now_wall = time.perf_counter_ns()
        now_cpu_proc = time.process_time_ns()
        now_cpu_thread = time.thread_time_ns() if _has_thread_time else None

        seg_wall_ns = now_wall - self._last_wall
        seg_cpu_proc_ns = now_cpu_proc - self._last_cpu_proc
        seg_cpu_thread_ns = (now_cpu_thread - self._last_cpu_thread) if _has_thread_time else None

        total_wall_ms = (now_wall - self._start_wall) / 1e6
        total_cpu_proc_ms = (now_cpu_proc - self._start_cpu_proc) / 1e6
        total_cpu_thread_ms = ((now_cpu_thread - self._start_cpu_thread) / 1e6) if _has_thread_time else None

        offcpu_ms = (seg_wall_ns - seg_cpu_proc_ns) / 1e6
        lag_ms, _ = get_loop_lag_snapshot()

        parts = [
            f"[{self.name}] {label}",
            f"seg_wall={seg_wall_ns/1e6:.3f}ms",
            f"seg_cpu_proc={seg_cpu_proc_ns/1e6:.3f}ms",
            f"seg_offcpu≈{offcpu_ms:.3f}ms",
            f"total_wall={total_wall_ms:.3f}ms",
            f"total_cpu_proc={total_cpu_proc_ms:.3f}ms",
            f"loop_lag≈{lag_ms:.1f}ms",
        ]
        if seg_cpu_thread_ns is not None:
            parts.insert(3, f"seg_cpu_thread={seg_cpu_thread_ns/1e6:.3f}ms")
            parts.append(f"total_cpu_thread={total_cpu_thread_ms:.3f}ms")

        logger.info(" | ".join(parts))

        self._last_wall = now_wall
        self._last_cpu_proc = now_cpu_proc
        self._last_cpu_thread = now_cpu_thread
