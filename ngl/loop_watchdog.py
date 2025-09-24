# loop_watchdog.py
import asyncio
import time
import logging

logger = logging.getLogger("checkpoint")

_loop_lag_ms = 0.0
_loop_lag_last_ts = 0.0

def get_loop_lag_snapshot():
    """Return (latest_lag_ms, timestamp_perf_counter)."""
    return _loop_lag_ms, _loop_lag_last_ts

async def loop_watchdog(period_ms: int = 20, warn_ms: int = 50):
    """
    Periodically measures event-loop lag. If the loop is blocked by sync work
    (e.g., time.sleep or CPU-heavy code), lag spikes. During proper 'await's,
    lag remains small.
    """
    global _loop_lag_ms, _loop_lag_last_ts
    period = period_ms / 1000.0
    expected = time.perf_counter()
    while True:
        expected += period
        await asyncio.sleep(max(0.0, expected - time.perf_counter()))
        now = time.perf_counter()
        lag = max(0.0, (now - expected) * 1000.0)  # milliseconds
        _loop_lag_ms = lag
        _loop_lag_last_ts = now
        if lag >= warn_ms:
            logger.warning(f"[loop] lag={lag:.1f}ms (event loop likely blocked)")
