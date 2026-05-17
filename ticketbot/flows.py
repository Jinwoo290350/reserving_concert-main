"""High-level booking orchestration with API-first + Selenium fallback."""
from __future__ import annotations

import logging
from datetime import datetime
from time import time

from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
)

from . import session
from .api_client import APIBotBlocked, TicketAPIClient
from .browser import build_driver
from .config import UserConfig
from .timing import ntp_offset_seconds, wait_until

log = logging.getLogger("ticketbot.flows")


def _save_crash(driver) -> None:
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    path = f"crash-{ts}.png"
    try:
        driver.save_screenshot(path)
        log.error("Saved crash screenshot to %s", path)
    except Exception:  # noqa: BLE001
        log.exception("Failed to save crash screenshot")


def book(cfg: UserConfig, *, headless: bool = False) -> int:
    """End-to-end booking. Returns process-exit code."""
    driver = build_driver(headless=headless)
    t0 = time()
    try:
        session.open_home(driver)
        session.login(driver, cfg.email, cfg.pwd, cfg.concert)

        if cfg.drop_at:
            offset = ntp_offset_seconds()
            log.info("NTP offset: %+0.3fs — waiting for drop_at %s", offset, cfg.drop_at)
            wait_until(cfg.drop_at, offset)

        session.select_show(driver)

        zones_to_try = [cfg.zone, *cfg.zones_fallback]
        selected = 0
        tried: set[str] = set()

        # --- Phase B: API attempt (no-op until recon is done) ---
        try:
            cookies = session.export_cookies(driver)
            with TicketAPIClient(cookies) as api:
                api.race_for_seats(cfg.show, cfg.zone, cfg.seats)
                log.info("API path locked seats — continuing in browser for payment.")
                # Once Phase B is implemented, navigate driver to the cart page here.
                selected = cfg.seats
        except APIBotBlocked as e:
            log.info("Falling back to Selenium flow: %s", e)

        # --- Phase C: Selenium fallback ---
        if selected == 0:
            for zone in zones_to_try:
                if zone in tried:
                    continue
                tried.add(zone)
                log.info("Trying zone %s", zone)
                if not session.select_zone(driver, zone):
                    continue
                selected = session.select_seat(driver, cfg.seats)
                if selected >= cfg.seats:
                    break
                if selected == 0:
                    session.go_back_and_open_availability(driver)

        if selected == 0:
            log.error("No seats secured.")
            return 2

        session.confirm_ticketprotect(driver)
        log.info("Reserved %d seats in %.2fs — finish payment manually.", selected, time() - t0)
        return 0
    except (TimeoutException, NoSuchElementException, StaleElementReferenceException):
        _save_crash(driver)
        log.exception("Selenium flow failed.")
        return 1
