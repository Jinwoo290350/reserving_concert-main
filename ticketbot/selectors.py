"""Single source of truth for every DOM selector the bot touches.

Centralising selectors means a site DOM change is fixed in one place,
and ``tests/test_selectors.py`` can parse a saved fixture against this
module to catch drift before drop time.
"""
from selenium.webdriver.common.by import By

# Login page
SIGNIN_BTN = (By.CSS_SELECTOR, ".btn-signin.item.d-none.d-lg-inline-block")
USERNAME_INPUT = (By.NAME, "username")
PASSWORD_INPUT = (By.NAME, "password")
SIGNIN_SUBMIT = (By.CSS_SELECTOR, ".btn-red.btn-signin")

# Concert / show page
BUY_NOW_BTN = (By.CSS_SELECTOR, ".btn-red.btn-buynow.btn-item")
VERIFY_AGREE_RADIO = (By.ID, "rdagree")
VERIFY_SUBMIT_BTN = (By.ID, "btn_verify")

# Seat map
ZONE_AREA_FIRST = (By.XPATH, '//*[@name="uMap2Map"]/area')
SEAT_UNCHECKED_CLASS = "seatuncheck"
SEAT_CHECKED_CLASS = "seatchecked"

# Availability popup / fallback flow
BACK_LINK = (By.PARTIAL_LINK_TEXT, "ย้อนกลับ / Back")
SEATS_AVAILABLE_LINK = (By.PARTIAL_LINK_TEXT, "ที่นั่งว่าง / Seats Available")
BOOK_NOW_LINK = (By.PARTIAL_LINK_TEXT, "ยืนยันที่นั่ง / Book Now")
CONTINUE_LINK = (By.PARTIAL_LINK_TEXT, "Continue")

# JS snippets — keep here so they're testable in isolation.
JS_ZONE_HREFS = (
    "return Array.from(document.querySelectorAll('map[name=\"uMap2Map\"] area'))"
    ".map(a => a.getAttribute('href'));"
)
JS_SEAT_IDS = (
    "return Array.from(document.getElementsByClassName('seatuncheck'))"
    ".map(el => el.id || el.getAttribute('data-seat') || '');"
)
JS_CLICK_BY_ID = (
    "var el = document.getElementById(arguments[0]); "
    "if (el) { el.click(); return true; } return false;"
)
JS_CHECKED_COUNT = "return document.getElementsByClassName('seatchecked').length"
JS_ZONE_TABLE_ROWS = """
const rows = document.querySelectorAll('.container-popup table tbody tr');
return Array.from(rows).slice(1).map(r => {
    const tds = r.querySelectorAll('td');
    return [tds[0] ? tds[0].innerText.trim() : '',
            tds[1] ? tds[1].innerText.trim() : ''];
});
"""
