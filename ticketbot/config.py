"""Strongly-typed user configuration loaded from ``userdetail.json``."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field, field_validator


class UserConfig(BaseModel):
    email: str
    pwd: str
    concert: str
    zone: str
    show: int
    seats: int = Field(ge=1, le=10)
    zones_fallback: list[str] = Field(default_factory=list)
    drop_at: datetime | None = None

    @field_validator("show", "seats", mode="before")
    @classmethod
    def _coerce_int(cls, v):
        if isinstance(v, str):
            return int(v)
        return v

    @classmethod
    def load(cls, path: str | Path = "userdetail.json") -> "UserConfig":
        data = json.loads(Path(path).read_text())
        return cls.model_validate(data)
