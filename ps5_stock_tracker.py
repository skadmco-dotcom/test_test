import os
import re
import json
from datetime import datetime, timezone

import requests


TO_EMAIL = "skadmco@gmail.com"
TEST_MODE = os.getenv("TEST_MODE", "false").lower() == "true"
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")

STATE_FILE = "stock_state.json"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/150 Safari/537.36"
    ),
    "Accept-Language": "en-NZ,en;q=0.9",
}

PRODUCTS = {
    "JB Hi-Fi": {
        "url": "https://www.jbhifi.co.nz/products/ps5-playstation-5-pro-2tb-console",

        # These indicate that the product can actually be purchased.
        "positive": [
            "add to cart",
            "add to bag",
        ],

        # These indicate that it cannot currently be purchased online.
        "negative": [
            "not available",
            "out of stock",
            "sold out",
            "unavailable",
            "notify me",
        ],
    },

    "Noel Leeming": {
        "url": "https://www.noelleeming.co.nz/p/ps5-pro-console/N232261.html",

        "positive": [
            "add to cart",
            "add to bag",
        ],

        "negative": [
            "online out of stock",
            "out of stock",
            "sold out",
            "unavailable",
            "notify me",
        ],
    },

    "Harvey Norman": {
        "url": "https://www.harveynorman.co.nz/gaming/consoles/c-playstation/playstation-5-pro-console-2tb-white.html",

        "positive": [
            "add to cart",
            "add to bag",
        ],

        "negative": [
            "not currently available online",
            "out of stock",
            "sold out",
            "unavailable",
            "notify me",
        ],
    },

    "The Warehouse": {
        "url": "https://www.thewarehouse.co.nz/p/ps5-pro-console/R2956306.html",

        "positive": [
            "add to cart",
            "add to bag",
        ],

        "negative": [
            "online out of stock",
            "out of stock",
            "sold out",
            "unavailable",
            "notify me",
        ],
    },
}


def fetch(url):
    response = requests.get(
        url,
        headers=HEADERS,
        timeout=30,
    )

    response.raise_for_status()

    return response.text


def normalise(html):
    html = re.sub(
        r"(?is)<script.*?</script>",
        " ",
        html
    )

    html = re.sub(
        r"(?is)<style.*?</style>",
        " ",
        html
    )

    text = re.sub(
        r"(?is)<[^>]+>",
        " ",
        html
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.lower().strip()


def detect_stock(name, html):
    text = normalise(html)

    product = PRODUCTS[name]

    # Out-of-stock phrases take priority.
    for phrase in product["negative"]:
        if phrase in text:
            return False, f"Out of stock indicator: {phrase}"

    # Only use strong purchase indicators.
    for phrase in product["positive"]:
        if phrase in text:
            return True, f"Purchase indicator: {phrase}"

    return False, "No purchase button detected"


def load_state():
    if not os.path.exists(STATE_FILE):
        return {}

    try:
        with open(STATE_FILE, "r", encoding="utf-8") as file:
            return json.load(file)

    except Exception:
        return {}


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as file:
        json.dump(
            state,
            file,
            indent=2,
            ensure_ascii=False,
        )


def send_email(subject, html, text):
    if not RESEND_API_KEY:
        raise RuntimeError(
            "RESEND_API_KEY is not set."
        )

    payload = {
        "from": "PS5 Pro Stock Tracker <onboarding@resend.dev>",
        "to": [TO_EMAIL],
        "subject": subject,
        "html": html,
        "text": text,
    }

    response = requests.post(
        "https://api.resend.com/emails",
        headers={
            "Authorization": f"Bearer {RESEND_API_KEY}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=30,
    )

    if response.status_code >= 400:
        raise RuntimeError(
            f"Resend error {response.status_code}: "
            f"{response.text}"
        )

    return response.json()


def main():

    now = datetime.now(timezone.utc).astimezone()

    old_state = load_state()
    new_state = dict(old_state)

    results = []

    for name, product in PRODUCTS.items():

        previous = old_state.get(
            name,
            {}
        )

        previous_stock = previous.get(
            "in_stock",
            False
        )

        try:

            html = fetch(product["url"])

            in_stock, reason = detect_stock(
                name,
                html
            )

            result = {
                "store": name,
                "in_stock": in_stock,
                "reason": reason,
                "url": product["url"],
                "error": None,
            }

            results.append(result)

            new_state[name] = {
                "in_stock": in_stock,
                "last_checked": now.isoformat(),
                "reason": reason,
            }

            print(
                f"{name}: "
                f"{'IN STOCK' if in_stock else 'not detected'} "
                f"— {reason}"
            )

        except Exception as error:

            result = {
                "store": name,
                "in_stock": previous_stock,
                "reason": "Check failed",
                "url": product["url"],
                "error": str(error),
            }

            results.append(result)

            # Do NOT change the previous state when a retailer
            # temporarily blocks the request.
            new_state[name] = {
                "in_stock": previous_stock,
                "last_checked": now.isoformat(),
                "reason": "Check failed",
                "error": str(error),
            }

            print(
                f"{name}: ERROR — {error}"
            )

    # ---------------------------------------------------------
    # TEST EMAIL
    # ---------------------------------------------------------

    if TEST_MODE:

        rows = ""

        for result in results:

            rows += (
                f"<li>"
                f"<b>{result['store']}</b><br>"
                f"Test successful — tracker checked this retailer."
                f"<br>"
                f"<a href='{result['url']}'>"
                f"Open product page"
                f"</a>"
                f"</li>"
            )

        send_email(
            "🧪 PS5 Pro Stock Tracker — TEST EMAIL",

            f"""
            <h2>PS5 Pro Stock Tracker test</h2>

            <p>
            The cloud tracker successfully ran and sent this email.
            </p>

            <p>
            Test time: {now.isoformat()}
            </p>

            <ul>
            {rows}
            </ul>
            """,

            (
                "PS5 Pro Stock Tracker test successful.\n\n"
                f"Test time: {now.isoformat()}"
            ),
        )

        print("TEST EMAIL SENT")

        save_state(new_state)

        return

    # ---------------------------------------------------------
    # FIND NEW STOCK
    # ---------------------------------------------------------

    newly_in_stock = []

    for result in results:

        if result["error"] is not None:
            continue

        was_in_stock = old_state.get(
            result["store"],
            {}
        ).get(
            "in_stock",
            False
        )

        is_in_stock = result["in_stock"]

        if is_in_stock and not was_in_stock:
            newly_in_stock.append(result)

    # ---------------------------------------------------------
    # SEND STOCK ALERT
    # ---------------------------------------------------------

    if newly_in_stock:

        html_rows = []
        text_lines = []

        for result in newly_in_stock:

            html_rows.append(
                f"""
                <tr>
                    <td>
                        <b>{result['store']}</b>
                    </td>

                    <td>
                        <a href="{result['url']}">
                            🚨 CHECK STOCK
                        </a>
                    </td>
                </tr>
                """
            )

            text_lines.append(
                f"{result['store']}: "
                f"{result['url']}"
            )

        send_email(

            "🚨 PS5 Pro IN STOCK — Check now",

            f"""
            <h2>🚨 PS5 Pro appears to be in stock!</h2>

            <p>
            A retailer has changed from unavailable
            to apparently available.
            </p>

            <p>
            Checked: {now.isoformat()}
            </p>

            <table
                border="1"
                cellpadding="10"
                cellspacing="0"
            >
                <tr>
                    <th>Store</th>
                    <th>Action</th>
                </tr>

                {''.join(html_rows)}

            </table>

            <p>
            Stock can disappear quickly.
            Check the retailer immediately.
            </p>
            """,

            (
                "PS5 Pro appears to be in stock!\n\n"
                + "\n".join(text_lines)
            ),
        )

        print("STOCK ALERT SENT")

    else:

        print(
            "No new stock detected. "
            "No email sent."
        )

    # Save the latest state.
    save_state(new_state)


if __name__ == "__main__":
    main()
