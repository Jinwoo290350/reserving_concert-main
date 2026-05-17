"""httpx-based booking client (Phase B).

The actual endpoint URLs and request schemas are discovered during the
HAR-capture step documented in README.md. This module ships as a typed
stub so ``flows.book`` can import it; once recon is complete, fill in
the marked sections and remove ``APIBotBlocked.RECON_NEEDED``.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Mapping

import httpx
from tenacity import retry, stop_after_attempt, wait_fixed

log = logging.getLogger("ticketbot.api_client")


class APIBotBlocked(RuntimeError):
    """Raised when the API path is not usable (recon incomplete or anti-bot).

    Callers should fall back to the Selenium flow on this exception.
    """

    RECON_NEEDED = "Phase B endpoints not yet captured — run HAR recon first."


@dataclass
class BookingResult:
    seat_ids: list[str]
    cart_token: str


class TicketAPIClient:
    """Thin wrapper around httpx for the booking endpoints.

    Cookies are populated from the Selenium driver via
    ``session.export_cookies`` so the API requests share the
    user's authenticated session.
    """

    BASE = "https://www.thaiticketmajor.com"

    def __init__(self, cookies: Mapping[str, str]) -> None:
        self._client = httpx.Client(
            base_url=self.BASE,
            http2=True,
            timeout=httpx.Timeout(connect=2.0, read=5.0, write=5.0, pool=2.0),
            cookies=dict(cookies),
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
                ),
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "X-Requested-With": "XMLHttpRequest",
            },
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "TicketAPIClient":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    @retry(stop=stop_after_attempt(5), wait=wait_fixed(0.1), reraise=True)
    def race_for_seats(self, show_id: int, zone: str, count: int) -> BookingResult:
        """Lock ``count`` seats in ``zone`` for ``show_id`` — placeholder.

        TODO(Phase B): fill in after HAR recon. Expected steps:
          1. POST /concert/api/seats/lock with show_id+zone+count
          2. parse seat_ids + cart_token from JSON response
          3. on 409 conflict (zone full) -> raise ZoneFullError
        """
        raise APIBotBlocked(APIBotBlocked.RECON_NEEDED)
