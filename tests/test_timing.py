from datetime import datetime, timedelta, timezone
from time import perf_counter

import pytest

from ticketbot.timing import wait_until


def test_wait_until_raises_on_naive_target() -> None:
    with pytest.raises(ValueError):
        wait_until(datetime.now())


def test_wait_until_returns_immediately_for_past_target() -> None:
    past = datetime.now(timezone.utc) - timedelta(seconds=10)
    t0 = perf_counter()
    wait_until(past)
    assert perf_counter() - t0 < 0.05


def test_wait_until_blocks_until_close_to_target() -> None:
    target = datetime.now(timezone.utc) + timedelta(milliseconds=300)
    t0 = perf_counter()
    wait_until(target)
    elapsed = perf_counter() - t0
    assert 0.25 < elapsed < 0.5
