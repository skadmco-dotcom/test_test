import os
import json
from datetime import datetime, timezone

import requests


# ============================================================
# SETTINGS
# ============================================================

TO_EMAIL = "skadmco@gmail.com"
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
TEST_MODE = os.getenv("TEST_MODE", "false").lower() == "true"

STATE_FILE = "stock_state.json"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-NZ,en;q=0.9",
}


# ============================================================
# PRODUCTS
# ============================================================

PRODUCTS = {
    "JB Hi-Fi": {
        "url": "https://www.jbhifi.co.nz/products/ps5-playstation-5-pro-2tb-console",
        "positive": [
            "add to cart",
            "add to bag",
        ],
        "negative": [
            "not available",
            "out of stock",
            "sold out",
            "unavailable",
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
        ],
    },

    "Harvey Norman": {
        "url": "https://www.harveynorman.co.nz/gaming/consoles/c-playstation/playstation-5-pro-console-2tb-white.html",
        "positive": [
            "add to cart",
            "add to bag",
        ],
        "negative": [
            "out of stock",
            "sold out",
            "unavailable",
        ],
    },

    "The Warehouse": {
        "url": "https://www.thewarehouse.co.nz/p/ps5-pro-console/R2956306.html",
        "positive": [
            "add to cart",
            "add to bag",
        ],
        "negative": [
            "out of stock",
            "sold out",
            "unavailable",
        ],
    },
}


# ============================================================
# HELPERS
# ============================================================

def now():
    return datetime.now(timezone.utc).isoformat()


def fetch_page(url):
    response = requests.get(
        url,
        headers=HEADERS,
        timeout=30,
    )

    response.raise_for_status()

    return response.text


def clean_html(html):
    """
    Convert HTML into simpler lowercase text.
    """
    import re

    html = re.sub(
        r"<script.*?</script>",
        " ",
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )

    html = re.sub(
        r"<style.*?</style>",
        " ",
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )

    html = re.sub(
        r"<[^>]+>",
        " ",
        html,
    )

    html = re.sub(
        r"\s+",
        " ",
        html,
    )

    return html.lower()


def detect_stock(retailer, html):
    product = PRODUCTS[retailer]

    text = clean_html(html)

    # Check strong out-of-stock indicators first.
    for phrase in product["negative"]:
        if phrase in text:
            return False, f"Detected: {phrase}"

    # Then check purchase buttons.
    for phrase in product["positive"]:
        if phrase in text:
            return True, f"Detected: {phrase}"

    return False, "No purchase button detected"


# ============================================================
# STATE
# ============================================================

def load_state():
    if not os.path.exists(STATE_FILE):
        return {}

    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    except Exception as e:
        print(f"Could not load state: {e}")
        return {}


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(
            state,
            f,
            indent=2,
        )


# ============================================================
# EMAIL
# ============================================================

def send_email(subject, html):
    if not RESEND_API_KEY:
        raise RuntimeError("RESEND_API_KEY is missing")

    response = requests.post(
        "https://api.resend.com/emails",
        headers={
            "Authorization": f"Bearer {RESEND_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "from": "onboarding@resend.dev",
            "to": [TO_EMAIL],
            "subject": subject,
            "html": html,
        },
        timeout=30,
    )

    print("Email status:", response.status_code)
    print("Email response:", response.text)

    response.raise_for_status()

    print("EMAIL SENT SUCCESSFULLY")


# ============================================================
# MAIN
# ============================================================

def main():

    print("======================================")
    print("PS5 Pro Stock Tracker")
    print("======================================")

    print("TEST_MODE:", TEST_MODE)
    print("Email configured:", bool(RESEND_API_KEY))

    old_state = load_state()

    print("Previous state:")
    print(json.dumps(old_state, indent=2))

    new_state = {}
    newly_in_stock = []

    # --------------------------------------------------------
    # TEST EMAIL
    # --------------------------------------------------------

    if TEST_MODE:

        print("TEST MODE ENABLED")
        print("Sending test email...")

        send_email(
            "PS5 Pro Stock Tracker - Test",
            """
            <h2>PS5 Pro Stock Tracker</h2>

            <p>This is a test email.</p>

            <p>
            Your GitHub Actions workflow and Resend email system
            are working correctly.
            </p>

            <p>
            The tracker is ready to monitor PS5 Pro stock.
            </p>
            """,
        )

        print("Test completed.")

        return

    # --------------------------------------------------------
    # CHECK EACH RETAILER
    # --------------------------------------------------------

    for retailer, product in PRODUCTS.items():

        print()
        print("--------------------------------------")
        print(retailer)
        print("--------------------------------------")

        previous = old_state.get(
            retailer,
            {}
        )

        previous_stock = previous.get(
            "in_stock",
            False
        )

        try:

            html = fetch_page(
                product["url"]
            )

            in_stock, reason = detect_stock(
                retailer,
                html
            )

            print("Stock:", in_stock)
            print("Reason:", reason)

            new_state[retailer] = {
                "in_stock": in_stock,
                "last_checked": now(),
                "reason": reason,
            }

            # Only alert when changing from
            # OUT OF STOCK -> IN STOCK.
            if in_stock and not previous_stock:

                newly_in_stock.append({
                    "retailer": retailer,
                    "url": product["url"],
                    "reason": reason,
                })

        except Exception as e:

            print(
                f"ERROR checking {retailer}: {e}"
            )

            # If a website temporarily fails,
            # keep the previous state instead of
            # incorrectly treating it as out of stock.
            new_state[retailer] = {
                "in_stock": previous_stock,
                "last_checked": now(),
                "reason": f"ERROR: {e}",
            }

    # --------------------------------------------------------
    # SAVE STATE
    # --------------------------------------------------------

    save_state(new_state)

    print()
    print("New state:")
    print(json.dumps(new_state, indent=2))

    # --------------------------------------------------------
    # SEND STOCK ALERT
    # --------------------------------------------------------

    if newly_in_stock:

        print()
        print("NEW STOCK FOUND!")

        rows = ""

        for item in newly_in_stock:

            rows += f"""
            <tr>
                <td style="padding:10px;">
                    <strong>{item["retailer"]}</strong>
                </td>

                <td style="padding:10px;">
                    {item["reason"]}
                </td>

                <td style="padding:10px;">
                    <a href="{item["url"]}">
                        View product
                    </a>
                </td>
            </tr>
            """

        email_html = f"""
        <h2>🚨 PS5 Pro Stock Alert</h2>

        <p>
        A PS5 Pro has just been detected as available.
        </p>

        <table
            border="1"
            cellpadding="0"
            cellspacing="0"
            style="border-collapse:collapse;"
        >

            <tr>
                <th style="padding:10px;">Retailer</th>
                <th style="padding:10px;">Detection</th>
                <th style="padding:10px;">Product</th>
            </tr>

            {rows}

        </table>

        <p>
        Checked by your automated PS5 Pro tracker.
        </p>
        """

        send_email(
            "🚨 PS5 Pro IN STOCK!",
            email_html
        )

    else:

        print()
        print("No newly available PS5 Pro stock.")
        print("No email required.")

    print()
    print("Tracker finished successfully.")


if __name__ == "__main__":
    main()
