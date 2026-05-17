"""NTP-synced wall clock + drop-time scheduler.

Sleep granularity isn't tight enough below ~16 ms on macOS, so we sleep
until the target minus a buffer and then busy-spin the final stretch.
"""
from __future__ import annotations

import logging
import time
from datetime import datetime, timezone

import ntplib

log = logging.getLogger("ticketbot.timing")

_BUSY_WAIT_BUFFER_S = 0.200


def ntp_offset_seconds(server: str = "pool.ntp.org") -> float:
    """Return (NTP time - local time) in seconds. Zero on failure."""
    try:
        client = ntplib.NTPClient()
        resp = client.request(server, version=3, timeout=2)
        return float(resp.offset)
    except Exception as e:  # noqa: BLE001
        log.warning("NTP sync failed (%s); using local clock.", e)
        return 0.0


def wait_until(target: datetime, offset_s: float = 0.0) -> None:
    """Block until ``target`` (timezone-aware). ``offset_s`` from ``ntp_offset_seconds``."""
    if target.tzinfo is None:
        raise ValueError("target must be timezone-aware")
    target_epoch = target.astimezone(timezone.utc).timestamp()

    while True:
        now_epoch = time.time() + offset_s
        remaining = target_epoch - now_epoch
        if remaining <= 0:
            return
        if remaining > _BUSY_WAIT_BUFFER_S:
            time.sleep(remaining - _BUSY_WAIT_BUFFER_S)
        else:
            # final busy-spin
            while time.time() + offset_s < target_epoch:
                pass
            return
