import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from ticketbot.config import UserConfig


def test_loads_string_int_fields(tmp_path: Path) -> None:
    p = tmp_path / "u.json"
    p.write_text(
        json.dumps(
            {
                "email": "a@b.co",
                "pwd": "x",
                "concert": "C",
                "zone": "V1",
                "show": "1",
                "seats": "4",
            }
        )
    )
    cfg = UserConfig.load(p)
    assert cfg.show == 1
    assert cfg.seats == 4
    assert cfg.zones_fallback == []
    assert cfg.drop_at is None


def test_rejects_missing_fields(tmp_path: Path) -> None:
    p = tmp_path / "u.json"
    p.write_text(json.dumps({"email": "a@b.co"}))
    with pytest.raises(ValidationError):
        UserConfig.load(p)


def test_rejects_zero_seats(tmp_path: Path) -> None:
    p = tmp_path / "u.json"
    p.write_text(
        json.dumps(
            {
                "email": "a@b.co",
                "pwd": "x",
                "concert": "C",
                "zone": "V1",
                "show": "1",
                "seats": "0",
            }
        )
    )
    with pytest.raises(ValidationError):
        UserConfig.load(p)


def test_accepts_fallback_and_drop_at(tmp_path: Path) -> None:
    p = tmp_path / "u.json"
    p.write_text(
        json.dumps(
            {
                "email": "a@b.co",
                "pwd": "x",
                "concert": "C",
                "zone": "V1",
                "show": 1,
                "seats": 2,
                "zones_fallback": ["V2", "BR"],
                "drop_at": "2026-05-20T10:00:00+07:00",
            }
        )
    )
    cfg = UserConfig.load(p)
    assert cfg.zones_fallback == ["V2", "BR"]
    assert cfg.drop_at is not None
    assert cfg.drop_at.tzinfo is not None
