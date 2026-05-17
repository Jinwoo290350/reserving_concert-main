# Reserving Concert Automation

Concerts from Thaiticketmajor.

> ⚠️ **Educational / personal-use tool.** Respect the site's terms of service
> and any anti-bot measures. Don't run this against a live drop you're not
> entitled to participate in.

## What changed in this refactor

The original script was a single 130-LOC `reserve.py`. It had several
crash-causing bugs (deprecated Selenium 3 API calls, off-by-one + live
HTMLCollection bug in seat selection, a never-incremented `count`
counter, a hardcoded `zone_list = 0`, a 100-second `sleep` after seat
selection, etc.). It's been split into a small package:

```
reserving_concert-main/
├─ reserve.py                 # thin CLI entry point
├─ ticketbot/
│  ├─ config.py               # pydantic model for userdetail.json
│  ├─ selectors.py            # all XPaths / CSS in one place
│  ├─ browser.py              # Chrome setup, eager load, headless option
│  ├─ session.py              # login + seat-map Selenium flow (with retries)
│  ├─ api_client.py           # httpx client (Phase B — see Recon below)
│  ├─ flows.py                # orchestration: Selenium → API → fallback
│  ├─ timing.py               # NTP sync + drop-time scheduler
│  └─ logging_setup.py
├─ tests/                     # pytest: config, selectors, timing
└─ requirements.txt
```

Selenium is used to log in and warm a session; once authenticated, the
booking endpoints can be raced with `httpx` (lower latency, no DOM
brittleness). If the API path is blocked or unknown, the Selenium flow
takes over automatically.

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

You also need a recent Chrome + matching `chromedriver` on `$PATH`
(Selenium Manager will fetch one automatically on Selenium ≥ 4.6).

## Configuration

Copy `userdetail.example.json` to `userdetail.json` and fill it in.
**`userdetail.json` is git-ignored** — never commit credentials.

| key             | type      | required | description |
|-----------------|-----------|----------|-------------|
| `email`         | string    | yes      | login email |
| `pwd`           | string    | yes      | login password |
| `concert`       | string    | yes      | partial concert name shown on the home page |
| `zone`          | string    | yes      | preferred zone code, e.g. `V1` |
| `show`          | int/str   | yes      | round / show number |
| `seats`         | int/str   | yes      | 1–10 |
| `zones_fallback`| string[]  | no       | ordered list of fallback zones |
| `drop_at`       | ISO-8601  | no       | timezone-aware drop time — bot waits until then |

## Usage

```bash
python reserve.py                # uses ./userdetail.json
python reserve.py --headless     # no visible browser
python reserve.py --config other.json
```

## Phase B reconnaissance (manual, one-time)

`ticketbot/api_client.py` is currently a stub — until the real booking
endpoints are captured, the bot uses the Selenium path end-to-end. To
unlock the fast path:

1. Open Chrome with DevTools open → **Network** tab → tick **Preserve log**.
2. Log in manually and complete a real (low-stakes) booking.
3. Right-click the network panel → **Save all as HAR with content**.
4. From the HAR, identify and record for each step:
   - **Show selection** — method, URL, request headers, body schema, response shape.
   - **Zone availability** — same.
   - **Seat lock** — same. Note any CSRF / signed-token headers.
   - **Cart confirm** — same.
5. Fill in `TicketAPIClient.race_for_seats()` (and add sibling methods)
   in `ticketbot/api_client.py`, and remove the `APIBotBlocked` raise.

If the requests carry a signed nonce baked into JS (common anti-bot
defence), Phase B isn't worth pursuing — the Selenium flow still works
and is much more stable than the original script.

## Testing

```bash
pytest tests/
```

The selector regression test (`test_selectors.py`) currently asserts
shape; once you have a saved HTML fixture from the live site, drop it
into `tests/fixtures/` and extend the test to parse it and assert each
selector resolves to exactly one element.

## Reference images

| field       | screenshot         |
|-------------|--------------------|
| concert     | ![name](/img/name.png) |
| show round  | ![show](/img/show.png) |
| zone        | ![zone](/img/zone.png) |
