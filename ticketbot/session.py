"""Selenium-driven login + seat-map flows.

Every step here either succeeds or raises a Selenium exception — let the
caller (``flows.book``) decide whether to retry or take a screenshot.
"""
from __future__ import annotations

import logging

from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from . import selectors as S

BASE_URL = "https://www.thaiticketmajor.com/concert/"
DEFAULT_TIMEOUT = 20

log = logging.getLogger("ticketbot.session")

_RETRY = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=0.3, max=2),
    retry=retry_if_exception_type(TimeoutException),
    reraise=True,
)


def _wait(driver, timeout: int = DEFAULT_TIMEOUT) -> WebDriverWait:
    return WebDriverWait(driver, timeout)


def js_click(driver, elm: WebElement) -> None:
    ActionChains(driver).move_to_element(elm).perform()
    driver.execute_script("arguments[0].click();", elm)


def open_home(driver) -> None:
    driver.get(BASE_URL)


@_RETRY
def login(driver, email: str, password: str, concert: str) -> None:
    _wait(driver).until(EC.element_to_be_clickable(S.SIGNIN_BTN)).click()
    _wait(driver).until(EC.visibility_of_element_located(S.USERNAME_INPUT)).send_keys(email)
    driver.find_element(*S.PASSWORD_INPUT).send_keys(password)
    driver.find_element(*S.SIGNIN_SUBMIT).click()

    _wait(driver, 30).until(
        lambda d: d.current_url != BASE_URL or _has_concert_link(d, concert)
    )
    concert_link = _wait(driver).until(
        EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, concert))
    )
    js_click(driver, concert_link)
    _wait(driver).until(lambda d: "concert" in d.current_url.lower())


def _has_concert_link(driver, concert: str) -> bool:
    try:
        driver.find_element(By.PARTIAL_LINK_TEXT, concert)
        return True
    except NoSuchElementException:
        return False


@_RETRY
def select_show(driver) -> None:
    _wait(driver).until(EC.element_to_be_clickable(S.BUY_NOW_BTN))
    buy = driver.find_element(*S.BUY_NOW_BTN)
    js_click(driver, buy)

    if "verify_condition" in driver.current_url:
        agree = _wait(driver).until(EC.element_to_be_clickable(S.VERIFY_AGREE_RADIO))
        js_click(driver, agree)
        _wait(driver).until(EC.element_to_be_clickable(S.VERIFY_SUBMIT_BTN)).click()


@_RETRY
def select_zone(driver, zone: str) -> bool:
    _wait(driver).until(EC.presence_of_element_located(S.ZONE_AREA_FIRST))
    hrefs: list[str] = driver.execute_script(S.JS_ZONE_HREFS)
    for i, href in enumerate(hrefs, start=1):
        parts = href.split("#")
        if len(parts) >= 3 and parts[2] == zone:
            driver.find_element(By.XPATH, f'//*[@name="uMap2Map"]/area[{i}]').click()
            return True
    log.warning("Zone %s not found among %d areas", zone, len(hrefs))
    return False


def select_seat(driver, number: int) -> int:
    """Click up to ``number`` seats. Returns count actually selected."""
    _wait(driver).until(
        lambda d: d.execute_script(
            f"return document.getElementsByClassName('{S.SEAT_UNCHECKED_CLASS}').length"
        )
        > 0
    )
    seat_ids: list[str] = driver.execute_script(S.JS_SEAT_IDS)
    if not any(seat_ids):
        # Site uses anonymous nodes — fall back to click-by-index on a static snapshot.
        log.warning("No seat IDs available; using indexed click fallback.")
        return _select_seat_by_index(driver, number)

    for sid in seat_ids:
        if not sid:
            continue
        clicked = driver.execute_script(S.JS_CLICK_BY_ID, sid)
        if not clicked:
            continue
        if driver.execute_script(S.JS_CHECKED_COUNT) >= number:
            break

    checked = driver.execute_script(S.JS_CHECKED_COUNT)
    log.info("select_seat: %d/%d", checked, number)
    return checked


def _select_seat_by_index(driver, number: int) -> int:
    """Click seats by collection-index, re-fetching the live collection each loop.

    Safer than caching indices: every iteration re-reads index 0, which is
    always the next unchecked seat after a successful click.
    """
    while True:
        remaining = driver.execute_script(
            f"return document.getElementsByClassName('{S.SEAT_UNCHECKED_CLASS}').length"
        )
        if remaining == 0:
            break
        clicked = driver.execute_script(
            f"const c = document.getElementsByClassName('{S.SEAT_UNCHECKED_CLASS}');"
            "if (c.length) { c[0].click(); return true; } return false;"
        )
        if not clicked:
            break
        if driver.execute_script(S.JS_CHECKED_COUNT) >= number:
            break
    return driver.execute_script(S.JS_CHECKED_COUNT)


def zone_availability(driver) -> list[tuple[str, str]]:
    """Return [(zone_name, amount_string), ...] from the availability popup."""
    return driver.execute_script(S.JS_ZONE_TABLE_ROWS)


@_RETRY
def go_back_and_open_availability(driver) -> None:
    _wait(driver).until(EC.element_to_be_clickable(S.BACK_LINK)).click()
    _wait(driver).until(EC.element_to_be_clickable(S.SEATS_AVAILABLE_LINK)).click()


@_RETRY
def confirm_ticketprotect(driver) -> None:
    _wait(driver).until(EC.element_to_be_clickable(S.BOOK_NOW_LINK)).click()
    _wait(driver).until(EC.element_to_be_clickable(S.CONTINUE_LINK)).click()


def export_cookies(driver) -> dict[str, str]:
    """Snapshot the cookie jar for hand-off to the httpx client."""
    return {c["name"]: c["value"] for c in driver.get_cookies()}
