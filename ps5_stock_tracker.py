import os
import json
import requests
from datetime import datetime, timezone

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError


# ============================================================
# SETTINGS
# ============================================================

TO_EMAIL = "skadmco@gmail.com"

RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
TEST_MODE = os.getenv("TEST_MODE", "false").lower() == "true"

STATE_FILE = "stock_state.json"

JB_HIFI_URL = (
    "https://www.jbhifi.co.nz/products/"
    "ps5-playstation-5-pro-2tb-console"
)

JB_HIFI_STORE = "Wairau Park"

# Product SKU shown by JB Hi-Fi
JB_HIFI_SKU = "446000"


# ============================================================
# OTHER RETAILERS
# ============================================================

PRODUCTS = {
    "JB Hi-Fi": JB_HIFI_URL,

    "Noel Leeming":
        "https://www.noelleeming.co.nz/p/ps5-pro-console/N232261.html",

    "Harvey Norman":
        "https://www.harveynorman.co.nz/gaming/consoles/"
        "c-playstation/playstation-5-pro-console-2tb-white.html",

    "The Warehouse":
        "https://www.thewarehouse.co.nz/p/ps5-pro-console/R2956306.html",
}


# ============================================================
# HEADERS
# ============================================================

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-NZ,en;q=0.9",
}


# ============================================================
# STATE
# ============================================================

def load_state():
    if not os.path.exists(STATE_FILE):
        return {}

    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


# ============================================================
# EMAIL
# ============================================================

def send_email(subject, body):
    if not RESEND_API_KEY:
        print("ERROR: RESEND_API_KEY is not configured.")
        return False

    url = "https://api.resend.com/emails"

    payload = {
        "from": "PS5 Stock Tracker <onboarding@resend.dev>",
        "to": [TO_EMAIL],
        "subject": subject,
        "text": body,
    }

    headers = {
        "Authorization": f"Bearer {RESEND_API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=30,
        )

        print("Email response:", response.status_code)
        print(response.text)

        return response.ok

    except Exception as e:
        print("Email error:", e)
        return False


# ============================================================
# TEST EMAIL
# ============================================================

def send_test_email():
    subject = "PS5 Stock Tracker - Test Email"

    body = """Your PS5 stock tracker is working.

This is a test email from GitHub Actions.

The tracker is configured to check:

JB Hi-Fi
Wairau Park

It will also check the other retailers configured in the script.

Time:
"""

    body += datetime.now(timezone.utc).strftime(
        "%Y-%m-%d %H:%M:%S UTC"
    )

    return send_email(subject, body)


# ============================================================
# JB HI-FI
# ============================================================

def check_jbhifi_wairau():
    """
    Uses a real Chromium browser to interact with JB Hi-Fi's
    store availability system.

    The important result is specifically Wairau Park.
    """

    print()
    print("=" * 60)
    print("CHECKING JB HI-FI Wairau Park")
    print("=" * 60)

    result = {
        "stock": False,
        "reason": "",
    }

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
            ],
        )

        context = browser.new_context(
            user_agent=HEADERS["User-Agent"],
            locale="en-NZ",
            timezone_id="Pacific/Auckland",
            viewport={
                "width": 1440,
                "height": 1000,
            },
        )

        page = context.new_page()

        try:
            print("Opening JB Hi-Fi product page...")

            page.goto(
                JB_HIFI_URL,
                wait_until="domcontentloaded",
                timeout=60000,
            )

            # Give the site's JavaScript time to load.
            page.wait_for_timeout(5000)

            print("Page loaded.")

            # ------------------------------------------------
            # First look for the store availability control.
            # ------------------------------------------------

            availability_found = False

            selectors = [
                "text=Check store availability",
                "text=Check availability",
                "text=store availability",
            ]

            for selector in selectors:
                try:
                    locator = page.locator(selector).first

                    if locator.is_visible(timeout=3000):
                        print(
                            f"Found availability control: {selector}"
                        )

                        locator.click()
                        availability_found = True
                        break

                except Exception:
                    pass

            # ------------------------------------------------
            # Sometimes the availability section is already
            # open, so this is not necessarily an error.
            # ------------------------------------------------

            page.wait_for_timeout(3000)

            body_text = page.locator("body").inner_text()

            print()
            print("Searching for Wairau Park...")

            # ------------------------------------------------
            # If Wairau is already visible, use it.
            # ------------------------------------------------

            if JB_HIFI_STORE.lower() in body_text.lower():

                print("Wairau Park already visible.")

            else:

                # ------------------------------------------------
                # Try the postcode/suburb search box.
                # ------------------------------------------------

                search_boxes = [
                    'input[placeholder*="postcode"]',
                    'input[placeholder*="suburb"]',
                    'input[placeholder*="postcode or suburb"]',
                    'input[type="search"]',
                ]

                search_box = None

                for selector in search_boxes:
                    try:
                        candidate = page.locator(selector).first

                        if candidate.is_visible(timeout=2000):
                            search_box = candidate
                            print(
                                f"Found store search box: {selector}"
                            )
                            break

                    except Exception:
                        pass

                if search_box:

                    search_box.fill(JB_HIFI_STORE)

                    page.wait_for_timeout(3000)

                    # Try pressing Enter as well.
                    try:
                        search_box.press("Enter")
                    except Exception:
                        pass

                    page.wait_for_timeout(3000)

            # ------------------------------------------------
            # Get all currently visible page text.
            # ------------------------------------------------

            body_text = page.locator("body").inner_text()

            print()
            print("Checking Wairau Park availability...")

            # Print the relevant portion if possible.
            lines = [
                line.strip()
                for line in body_text.splitlines()
                if line.strip()
            ]

            for i, line in enumerate(lines):

                if "wairau" in line.lower():

                    start = max(0, i - 2)
                    end = min(len(lines), i + 8)

                    print()
                    print("--- Wairau section ---")

                    for nearby_line in lines[start:end]:
                        print(nearby_line)

                    print("--- End Wairau section ---")
                    print()

            # ------------------------------------------------
            # IMPORTANT:
            #
            # "Sorry, it's unavailable." = OUT OF STOCK
            #
            # "1 hour Click & Collect"
            # "In-store"
            # etc. = IN STOCK
            # ------------------------------------------------

            lower_text = body_text.lower()

            # Find Wairau's section specifically.
            wairau_index = lower_text.find(
                JB_HIFI_STORE.lower()
            )

            if wairau_index == -1:

                result["stock"] = False
                result["reason"] = (
                    "Could not find Wairau Park on the page"
                )

                print("Wairau Park was NOT found.")

            else:

                # Only inspect text around Wairau.
                wairau_section = lower_text[
                    wairau_index:
                    wairau_index + 1200
                ]

                # OUT OF STOCK
                unavailable_phrases = [
                    "sorry, it's unavailable",
                    "sorry, it’s unavailable",
                    "unavailable",
                    "not available",
                ]

                # IN STOCK
                available_phrases = [
                    "1 hour click & collect",
                    "click & collect",
                    "in-store",
                    "in store",
                ]

                found_unavailable = any(
                    phrase in wairau_section
                    for phrase in unavailable_phrases
                )

                found_available = any(
                    phrase in wairau_section
                    for phrase in available_phrases
                )

                if found_unavailable and not found_available:

                    result["stock"] = False
                    result["reason"] = (
                        "Wairau Park says unavailable"
                    )

                    print(
                        "RESULT: Wairau Park is OUT OF STOCK"
                    )

                elif found_available:

                    result["stock"] = True
                    result["reason"] = (
                        "Wairau Park has Click & Collect / "
                        "In-store availability"
                    )

                    print(
                        "RESULT: Wairau Park is IN STOCK!"
                    )

                else:

                    result["stock"] = False
                    result["reason"] = (
                        "Wairau Park found, but availability "
                        "could not be determined"
                    )

                    print(
                        "RESULT: Could not determine stock."
                    )

            # ------------------------------------------------
            # Save a screenshot for debugging.
            # ------------------------------------------------

            try:
                page.screenshot(
                    path="jbhifi_debug.png",
                    full_page=True,
                )
                print("Saved jbhifi_debug.png")
            except Exception:
                pass

        except PlaywrightTimeoutError as e:

            result["stock"] = False
            result["reason"] = (
                f"JB Hi-Fi page timed out: {e}"
            )

            print(result["reason"])

        except Exception as e:

            result["stock"] = False
            result["reason"] = (
                f"JB Hi-Fi browser error: {e}"
            )

            print(result["reason"])

        finally:

            browser.close()

    return result


# ============================================================
# OTHER RETAILER CHECK
# ============================================================

def check_generic_retailer(name, url):

    print()
    print("=" * 60)
    print(f"CHECKING {name}")
    print("=" * 60)

    try:

        response = requests.get(
            url,
            headers=HEADERS,
            timeout=30,
        )

        print("HTTP status:", response.status_code)

        if response.status_code != 200:

            return {
                "stock": False,
                "reason": (
                    f"HTTP {response.status_code}"
                ),
            }

        text = response.text.lower()

        # ------------------------------------------------
        # Negative phrases FIRST.
        # ------------------------------------------------

        negative_phrases = [
            "out of stock",
            "sold out",
            "currently unavailable",
            "not available",
            "unavailable",
            "no stock",
            "temporarily unavailable",
        ]

        for phrase in negative_phrases:

            if phrase in text:

                return {
                    "stock": False,
                    "reason": f"Detected: {phrase}",
                }

        # ------------------------------------------------
        # Positive purchase phrases.
        # ------------------------------------------------

        positive_phrases = [
            "add to cart",
            "add to bag",
            "buy now",
            "purchase",
        ]

        for phrase in positive_phrases:

            if phrase in text:

                return {
                    "stock": True,
                    "reason": f"Detected: {phrase}",
                }

        return {
            "stock": False,
            "reason": "No purchase button detected",
        }

    except Exception as e:

        return {
            "stock": False,
            "reason": f"Error: {e}",
        }


# ============================================================
# EMAIL WHEN STOCK BECOMES AVAILABLE
# ============================================================

def send_stock_email(available_retailers):

    subject = "🚨 PS5 Pro STOCK AVAILABLE!"

    body = """PS5 Pro stock has been detected!

"""

    for retailer, details in available_retailers.items():

        body += f"""
{retailer}
Status: IN STOCK
Reason: {details['reason']}

"""

    body += """
This alert was triggered because stock changed from unavailable
to available.

The tracker will continue checking automatically.
"""

    return send_email(subject, body)


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("PS5 PRO STOCK TRACKER")
    print("=" * 60)

    print("TEST_MODE:", TEST_MODE)
    print(
        "Email configured:",
        bool(RESEND_API_KEY),
    )

    # --------------------------------------------------------
    # TEST MODE
    # --------------------------------------------------------

    if TEST_MODE:

        print()
        print("TEST MODE ENABLED")
        print("Sending test email...")

        success = send_test_email()

        if success:
            print("Test email sent successfully.")
        else:
            print("Test email failed.")

        return

    # --------------------------------------------------------
    # Load previous state.
    # --------------------------------------------------------

    previous_state = load_state()

    print()
    print("Previous state:")

    for retailer, state in previous_state.items():

        print(
            f"  {retailer}: "
            f"{state.get('stock', False)}"
        )

    # --------------------------------------------------------
    # Check all retailers.
    # --------------------------------------------------------

    current_state = {}

    # --------------------------------------------------------
    # JB HI-FI — SPECIAL Wairau CHECK
    # --------------------------------------------------------

    jb_result = check_jbhifi_wairau()

    current_state["JB Hi-Fi"] = jb_result

    # --------------------------------------------------------
    # OTHER RETAILERS
    # --------------------------------------------------------

    for retailer in [
        "Noel Leeming",
        "Harvey Norman",
        "The Warehouse",
    ]:

        result = check_generic_retailer(
            retailer,
            PRODUCTS[retailer],
        )

        current_state[retailer] = result

        print(
            f"{retailer}: "
            f"Stock={result['stock']}, "
            f"Reason={result['reason']}"
        )

    # --------------------------------------------------------
    # Print final state.
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("CURRENT STOCK STATE")
    print("=" * 60)

    for retailer, result in current_state.items():

        print(
            f"{retailer}: "
            f"{'IN STOCK' if result['stock'] else 'OUT OF STOCK'}"
        )

        print(
            f"  Reason: {result['reason']}"
        )

    # --------------------------------------------------------
    # Find NEWLY available products.
    # --------------------------------------------------------

    newly_available = {}

    for retailer, result in current_state.items():

        current_stock = result["stock"]

        previous_stock = previous_state.get(
            retailer,
            {}
        ).get(
            "stock",
            False
        )

        if current_stock and not previous_stock:

            newly_available[retailer] = result

    # --------------------------------------------------------
    # Send alert.
    # --------------------------------------------------------

    if newly_available:

        print()
        print("🚨 NEW STOCK DETECTED!")

        for retailer in newly_available:

            print(
                f"  {retailer}"
            )

        send_stock_email(
            newly_available
        )

    else:

        print()
        print("No newly available stock.")
        print("No alert email sent.")

    # --------------------------------------------------------
    # Save state.
    # --------------------------------------------------------

    save_state(current_state)

    print()
    print("New state saved.")

    print()
    print("=" * 60)
    print("TRACKER FINISHED")
    print("=" * 60)


if __name__ == "__main__":
    main()
