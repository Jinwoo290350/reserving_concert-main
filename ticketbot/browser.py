"""Chrome WebDriver factory with sane defaults for speed + stability."""
from __future__ import annotations

from contextlib import contextmanager

from selenium import webdriver
from selenium.webdriver.chrome.options import Options


def build_driver(
    *,
    headless: bool = False,
    detach: bool = True,
    disable_images: bool = True,
) -> webdriver.Chrome:
    """Construct a Chrome driver with eager page-load and optional headless."""
    opts = Options()
    opts.page_load_strategy = "eager"
    if detach and not headless:
        opts.add_experimental_option("detach", True)
    if headless:
        opts.add_argument("--headless=new")
        opts.add_argument("--disable-gpu")
    if disable_images:
        opts.add_experimental_option(
            "prefs", {"profile.managed_default_content_settings.images": 2}
        )
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_argument("--no-first-run")
    opts.add_argument("--no-default-browser-check")

    driver = webdriver.Chrome(options=opts)
    if not headless:
        driver.maximize_window()
    return driver


@contextmanager
def driver_session(**kwargs):
    """Context manager that quits the driver on exit unless ``detach=True``."""
    drv = build_driver(**kwargs)
    try:
        yield drv
    finally:
        if not kwargs.get("detach", True) or kwargs.get("headless"):
            drv.quit()
