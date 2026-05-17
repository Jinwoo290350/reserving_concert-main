"""Sanity-check that every selector is a valid (By, locator) tuple.

The full DOM-fixture regression test belongs here too — drop a saved
HTML page into ``tests/fixtures/`` and assert each selector resolves
against it via ``html.parser`` or ``lxml``. Skipped for now because we
don't have a captured fixture yet (recon step gathers it).
"""
from selenium.webdriver.common.by import By

from ticketbot import selectors as S


VALID_BYS = {
    By.ID, By.NAME, By.XPATH, By.CSS_SELECTOR,
    By.CLASS_NAME, By.TAG_NAME, By.LINK_TEXT, By.PARTIAL_LINK_TEXT,
}


def test_all_selectors_are_well_formed() -> None:
    for name in dir(S):
        if name.startswith("_") or name.startswith("JS_"):
            continue
        attr = getattr(S, name)
        if isinstance(attr, tuple) and len(attr) == 2:
            by, locator = attr
            assert by in VALID_BYS, f"{name}: bad By value {by!r}"
            assert isinstance(locator, str) and locator, f"{name}: empty locator"


def test_js_snippets_are_non_empty() -> None:
    for name in ("JS_ZONE_HREFS", "JS_SEAT_IDS", "JS_CLICK_BY_ID",
                 "JS_CHECKED_COUNT", "JS_ZONE_TABLE_ROWS"):
        snippet = getattr(S, name)
        assert isinstance(snippet, str) and snippet.strip(), name
