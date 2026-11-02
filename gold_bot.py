#!/usr/bin/env python3
"""Posts the daily WARDOGS gold bar rate to a Discord channel via a webhook.

The rate turns over at midnight UTC, so run this once a day shortly after
00:00 UTC (e.g. 00:10). Standard library only, no installs needed.

Setup:
  export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..."
  python3 gold_bot.py
"""
import json
import os
import re
import sys
import urllib.request
from pathlib import Path

WEBHOOK_URL = os.environ["DISCORD_WEBHOOK_URL"]
PAGE_URL = "https://wardogshub.gg/gold-market/"
STATE = Path(os.environ.get("GOLD_STATE_FILE", Path(__file__).with_name("last_rate.json")))
UA = "wardogs-gold-discord-bot/1.0 (personal use; one request per day)"

# Matches the sentence in the page's meta description, e.g.
# "One WARDOGS gold bar costs $396,210 on 2 November 2026."
PATTERN = re.compile(r"gold bar costs \$([\d,]+) on (\d{1,2} \w+ \d{4})")


def request(url, data=None, headers=None):
    req = urllib.request.Request(url, data=data, headers={"User-Agent": UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read().decode("utf-8", "replace")


def money(n):
    return f"{'+' if n >= 0 else '-'}${abs(n):,}"


def main():
    html = request(PAGE_URL)
    m = PATTERN.search(html)
    if not m:
        sys.exit("Couldn't find the rate on the page - the layout may have changed.")
    price, day = int(m.group(1).replace(",", "")), m.group(2)

    last = json.loads(STATE.read_text()) if STATE.exists() else None
    if last and last["day"] == day:
        return  # already posted this day's rate (or the site hasn't updated yet)

    msg = f"\U0001F947 **Gold bar, {day}:** ${price:,}"
    if last:
        diff = price - last["price"]
        msg += f"\n{money(diff)} ({diff / last['price']:+.1%}) vs {last['day']}"

    request(WEBHOOK_URL, json.dumps({"content": msg}).encode(), {"Content-Type": "application/json"})
    STATE.write_text(json.dumps({"day": day, "price": price}))


if __name__ == "__main__":
    main()
