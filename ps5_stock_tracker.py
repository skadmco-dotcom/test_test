import os
import re
import json
import hashlib
from datetime import datetime, timezone
from urllib.parse import urljoin

import requests

# PS5 Pro Stock Tracker
# Checks four NZ retailers. Intended to run from GitHub Actions once per hour.
#
# IMPORTANT:
# - Never put your RESEND_API_KEY directly in this file.
# - Put it in GitHub Settings -> Secrets and variables -> Actions.
# - TEST_MODE=true forces a test email so you can verify the email system.

TO_EMAIL = "skadmco@gmail.com"
TEST_MODE = os.getenv("TEST_MODE", "false").lower() == "true"
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150 Safari/537.36"
    ),
    "Accept-Language": "en-NZ,en;q=0.9",
}

PRODUCTS = {
    "JB Hi-Fi": {
        "url": "https://www.jbhifi.co.nz/products/ps5-playstation-5-pro-2tb-console",
        "positive": [
            "add to cart", "add to bag", "in stock", "available",
            "click & collect", "click and collect",
        ],
        "negative": [
            "not available", "out of stock", "sold out",
            "unavailable", "notify me",
        ],
    },
    "Noel Leeming": {
        "url": "https://www.noelleeming.co.nz/p/ps5-pro-console/N232261.html",
        "positive": ["add to cart", "in stock", "available"],
        "negative": ["online out of stock", "out of stock", "sold out"],
    },
    "Harvey Norman": {
        "url": "https://www.harveynorman.co.nz/gaming/consoles/c-playstation/playstation-5-pro-console-2tb-white.html",
        "positive": ["add to cart", "in stock", "available"],
        "negative": ["out of stock", "sold out", "unavailable"],
    },
    "The Warehouse": {
        "url": "https://www.thewarehouse.co.nz/p/ps5-pro-console/R2956306.html",
        "positive": ["add to cart", "in stock", "available"],
        "negative": ["online out of stock", "out of stock", "sold out"],
    },
}

def fetch(url):
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.text

def normalise(html):
    # Strip scripts/styles but retain useful visible text.
    html = re.sub(r"(?is)<script.*?</script>", " ", html)
    html = re.sub(r"(?is)<style.*?</style>", " ", html)
    text = re.sub(r"(?is)<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text).strip()
    return text.lower()

def detect_stock(name, html):
    text = normalise(html)

    # Strong out-of-stock phrases win over generic "available" words.
    for phrase in PRODUCTS[name]["negative"]:
        if phrase in text:
            return False, f"Detected: {phrase}"

    for phrase in PRODUCTS[name]["positive"]:
        if phrase in text:
            return True, f"Detected: {phrase}"

    return False, "No stock indicator found"

def send_email(subject, html, text):
    if not RESEND_API_KEY:
        raise RuntimeError("RESEND_API_KEY is not set.")

    payload = {
        "from": "PS5 Pro Stock Tracker <onboarding@resend.dev>",
        "to": [TO_EMAIL],
        "subject": subject,
        "html": html,
        "text": text,
    }

    r = requests.post(
        "https://api.resend.com/emails",
        headers={
            "Authorization": f"Bearer {RESEND_API_KEY}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=30,
    )
    if r.status_code >= 400:
        raise RuntimeError(f"Resend error {r.status_code}: {r.text}")
    return r.json()

def main():
    now = datetime.now(timezone.utc).astimezone()
    results = []

    for name, product in PRODUCTS.items():
        try:
            html = fetch(product["url"])
            in_stock, reason = detect_stock(name, html)
            results.append({
                "store": name,
                "in_stock": in_stock,
                "reason": reason,
                "url": product["url"],
                "error": None,
            })
            print(f"{name}: {'IN STOCK' if in_stock else 'not detected'} — {reason}")
        except Exception as e:
            results.append({
                "store": name,
                "in_stock": False,
                "reason": "Check failed",
                "url": product["url"],
                "error": str(e),
            })
            print(f"{name}: ERROR — {e}")

    # Test mode deliberately sends an email every manual test run.
    if TEST_MODE:
        rows = "".join(
            f"<li><b>{r['store']}</b>: TEST — stock alert system is working<br>"
            f"<a href='{r['url']}'>{r['url']}</a></li>"
            for r in results
        )
        send_email(
            "🧪 PS5 Pro Stock Tracker — TEST EMAIL",
            f"""
            <h2>PS5 Pro Stock Tracker test</h2>
            <p>This confirms the cloud script can run and send email to {TO_EMAIL}.</p>
            <p>Test time: {now.isoformat()}</p>
            <ul>{rows}</ul>
            """,
            f"PS5 Pro Stock Tracker test. Time: {now.isoformat()}",
        )
        print("TEST EMAIL SENT")
        return

    # GitHub Actions can persist a small state file between runs only if we
    # explicitly use an artifact/cache. To keep the basic version simple,
    # alert on any currently detected stock. The workflow also has a manual
    # test option. The next version can add persistent state if desired.
    in_stock = [r for r in results if r["in_stock"]]

    if in_stock:
        lines = []
        html_rows = []
        for r in in_stock:
            lines.append(f"{r['store']}: {r['url']}")
            html_rows.append(
                f"<tr><td><b>{r['store']}</b></td>"
                f"<td><a href='{r['url']}'>BUY / CHECK STOCK</a></td></tr>"
            )

        send_email(
            "🚨 PS5 Pro IN STOCK — Check now",
            f"""
            <h2>🚨 PS5 Pro appears to be in stock</h2>
            <p>Checked: {now.isoformat()}</p>
            <table border="1" cellpadding="8">{''.join(html_rows)}</table>
            <p>Stock can disappear quickly, so check the links immediately.</p>
            """,
            "PS5 Pro appears to be in stock:\n" + "\n".join(lines),
        )
        print("STOCK ALERT SENT")
    else:
        print("No stock detected. No email sent.")

if __name__ == "__main__":
    main()
