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

# Search term used in JB Hi-Fi's store finder
STORE_SEARCH = "Wairau Park"


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
# BROWSER SETTINGS
# ============================================================

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)


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

JB Hi-Fi store:
Wairau Park

The tracker will check the store automatically.

Time:
"""

    body += datetime.now(timezone.utc).strftime(
        "%Y-%m-%d %H:%M:%S UTC"
    )

    return send_email(subject, body)


# ============================================================
# HELPER: SAFE CLICK
# ============================================================

def click_text(page, texts, timeout=3000):

    for text in texts:

        try:

            locator = page.get_by_text(
                text,
                exact=True
            ).first

            if locator.is_visible(timeout=timeout):

                print(f"Clicking: {text}")

                locator.click()

                return True

        except Exception:
            pass

    return False


# ============================================================
# HELPER: FIND VISIBLE TEXT
# ============================================================

def text_exists(page, texts):

    for text in texts:

        try:

            locator = page.get_by_text(
                text,
                exact=False
            ).first

            if locator.is_visible(timeout=1000):
                return True

        except Exception:
            pass

    return False


# ============================================================
# HELPER: GET PAGE TEXT
# ============================================================

def get_page_text(page):

    try:
        return page.locator("body").inner_text().lower()
    except Exception:
        return ""


# ============================================================
# JB HI-FI STORE CHECK
# ============================================================

def check_jbhifi_wairau():

    print()
    print("=" * 60)
    print("CHECKING JB HI-FI Wairau Park")
    print("=" * 60)

    result = {
        "status": "unknown",
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
            user_agent=USER_AGENT,
            locale="en-NZ",
            timezone_id="Pacific/Auckland",
            viewport={
                "width": 1440,
                "height": 1000,
            },
        )

        page = context.new_page()

        try:

            # ==================================================
            # STEP 1 — OPEN PRODUCT PAGE
            # ==================================================

            print("Opening JB Hi-Fi product page...")

            page.goto(
                JB_HIFI_URL,
                wait_until="domcontentloaded",
                timeout=60000,
            )

            page.wait_for_timeout(5000)

            print("Product page loaded.")

            # ==================================================
            # STEP 2 — ADD TO CART
            # ==================================================

            print()
            print("Looking for Add to cart...")

            add_to_cart = page.locator(
                "button:has-text('Add to cart')"
            ).first

            if not add_to_cart.is_visible(timeout=5000):

                result["reason"] = (
                    "Could not find Add to cart button"
                )

                print(result["reason"])

                page.screenshot(
                    path="jbhifi_debug.png",
                    full_page=True,
                )

                return result

            print("Found Add to cart.")

            add_to_cart.click()

            print("Added product to cart.")

            page.wait_for_timeout(4000)

            # ==================================================
            # STEP 3 — REVIEW CART
            # ==================================================

            print()
            print("Looking for Review cart...")

            review_cart = page.get_by_text(
                "Review cart",
                exact=True,
            ).first

            if review_cart.is_visible(timeout=5000):

                print("Found Review cart.")

                review_cart.click()

            else:

                print(
                    "Review cart not found."
                )

                print(
                    "Opening cart directly..."
                )

                page.goto(
                    "https://www.jbhifi.co.nz/cart",
                    wait_until="domcontentloaded",
                    timeout=60000,
                )

            page.wait_for_timeout(5000)

            print("Cart page loaded.")

            # ==================================================
            # STEP 4 — FIND "GETTING YOUR ITEM"
            # ==================================================

            print()
            print(
                "Looking for 'Getting your item'..."
            )

            getting_text = page.get_by_text(
                "Getting your item",
                exact=False,
            ).first

            if not getting_text.is_visible(timeout=5000):

                result["reason"] = (
                    "Could not find 'Getting your item' "
                    "section"
                )

                print(result["reason"])

                page.screenshot(
                    path="jbhifi_debug.png",
                    full_page=True,
                )

                return result

            print(
                "Found 'Getting your item' section."
            )

            # ==================================================
            # STEP 5 — FIND THE LOCATION INPUT
            # ==================================================

            print()
            print(
                "Looking for store/location input..."
            )

            search_box = None

            # We intentionally search broadly here because
            # JB Hi-Fi's input may not have a standard
            # placeholder or name.

            input_count = page.locator(
                "input"
            ).count()

            print(
                f"Found {input_count} input fields."
            )

            for i in range(input_count):

                try:

                    candidate = page.locator(
                        "input"
                    ).nth(i)

                    if not candidate.is_visible(
                        timeout=1000
                    ):
                        continue

                    placeholder = (
                        candidate.get_attribute(
                            "placeholder"
                        )
                        or ""
                    ).lower()

                    aria_label = (
                        candidate.get_attribute(
                            "aria-label"
                        )
                        or ""
                    ).lower()

                    name = (
                        candidate.get_attribute(
                            "name"
                        )
                        or ""
                    ).lower()

                    input_type = (
                        candidate.get_attribute(
                            "type"
                        )
                        or ""
                    ).lower()

                    print(
                        f"Input {i}: "
                        f"placeholder='{placeholder}', "
                        f"aria-label='{aria_label}', "
                        f"name='{name}', "
                        f"type='{input_type}'"
                    )

                    location_words = [
                        "postcode",
                        "suburb",
                        "store",
                        "location",
                        "address",
                        "search",
                    ]

                    combined = (
                        placeholder
                        + " "
                        + aria_label
                        + " "
                        + name
                    )

                    if any(
                        word in combined
                        for word in location_words
                    ):

                        search_box = candidate

                        print(
                            f"Selected input {i} "
                            "as store/location input."
                        )

                        break

                except Exception:
                    pass

            # ==================================================
            # FALLBACK — USE INPUT CLOSE TO GETTING YOUR ITEM
            # ==================================================

            if search_box is None:

                print(
                    "Could not identify the input "
                    "from its attributes."
                )

                print(
                    "Trying the first visible text input..."
                )

                for i in range(input_count):

                    try:

                        candidate = page.locator(
                            "input"
                        ).nth(i)

                        if not candidate.is_visible(
                            timeout=1000
                        ):
                            continue

                        input_type = (
                            candidate.get_attribute(
                                "type"
                            )
                            or ""
                        ).lower()

                        if input_type in [
                            "",
                            "text",
                            "search",
                        ]:

                            search_box = candidate

                            print(
                                f"Using visible input {i}."
                            )

                            break

                    except Exception:
                        pass

            if search_box is None:

                result["reason"] = (
                    "Could not find the location "
                    "input under Getting your item"
                )

                print(result["reason"])

                page.screenshot(
                    path="jbhifi_debug.png",
                    full_page=True,
                )

                return result

            # ==================================================
            # STEP 6 — ENTER WAIRAU
            # ==================================================

            print()
            print(
                "Entering Wairau into location field..."
            )

            search_box.click()

            search_box.fill(
                "Wairau"
            )

            page.wait_for_timeout(2000)

            # ==================================================
            # STEP 7 — CLICK CHECK AVAILABILITY
            # ==================================================

            print()
            print(
                "Looking for Check availability..."
            )

            check_button = None

            check_selectors = [
                "button:has-text('Check availability')",
                "button:has-text('Check Availability')",
                "text=Check availability",
                "text=Check Availability",
            ]

            for selector in check_selectors:

                try:

                    candidate = page.locator(
                        selector
                    ).first

                    if candidate.is_visible(
                        timeout=3000
                    ):

                        check_button = candidate

                        print(
                            f"Found Check availability "
                            f"using: {selector}"
                        )

                        break

                except Exception:
                    pass

            if check_button is None:

                result["reason"] = (
                    "Could not find Check availability "
                    "button"
                )

                print(result["reason"])

                page.screenshot(
                    path="jbhifi_debug.png",
                    full_page=True,
                )

                return result

            check_button.click()

            print(
                "Clicked Check availability."
            )

            page.wait_for_timeout(5000)

            # ==================================================
            # STEP 8 — FIND WAIRAU PARK
            # ==================================================

            print()
            print(
                "Looking for Wairau Park..."
            )

            body_text = page.locator(
                "body"
            ).inner_text()

            print()
            print(
                "--- STORE AVAILABILITY TEXT ---"
            )

            print(
                body_text[-5000:]
            )

            print(
                "--- END STORE AVAILABILITY TEXT ---"
            )

            lower_text = body_text.lower()

            if "wairau park" not in lower_text:

                result["reason"] = (
                    "Wairau Park did not appear after "
                    "checking availability"
                )

                print(result["reason"])

                page.screenshot(
                    path="jbhifi_debug.png",
                    full_page=True,
                )

                return result

            print(
                "Wairau Park found."
            )

            # ==================================================
            # STEP 9 — CLICK "IN-STORE"
            # ==================================================

            print()
            print(
                "Looking for In-store..."
            )

            in_store_clicked = False

            in_store_selectors = [
                "text=In-store",
                "text=In store",
                "button:has-text('In-store')",
                "button:has-text('In store')",
            ]

            for selector in in_store_selectors:

                try:

                    candidate = page.locator(
                        selector
                    ).first

                    if candidate.is_visible(
                        timeout=3000
                    ):

                        print(
                            f"Found In-store using: "
                            f"{selector}"
                        )

                        candidate.click()

                        in_store_clicked = True

                        break

                except Exception:
                    pass

            if in_store_clicked:

                print(
                    "Clicked In-store."
                )

                page.wait_for_timeout(3000)

            else:

                print(
                    "In-store button not found."
                )

                # This isn't automatically an error.
                # Some versions of the page display the
                # availability directly.

            # ==================================================
            # STEP 10 — READ WAIRAU RESULT
            # ==================================================

            body_text = page.locator(
                "body"
            ).inner_text()

            lower_text = body_text.lower()

            wairau_index = lower_text.find(
                "wairau park"
            )

            if wairau_index == -1:

                result["reason"] = (
                    "Wairau Park disappeared before "
                    "availability could be read"
                )

                print(result["reason"])

                page.screenshot(
                    path="jbhifi_debug.png",
                    full_page=True,
                )

                return result

            # Only inspect text surrounding Wairau.
            start = max(
                0,
                wairau_index - 100
            )

            end = min(
                len(lower_text),
                wairau_index + 1800
            )

            wairau_section = lower_text[
                start:end
            ]

            print()
            print(
                "--- WAIRAU RESULT ---"
            )

            print(
                wairau_section
            )

            print(
                "--- END WAIRAU RESULT ---"
            )

            # ==================================================
            # OUT OF STOCK
            # ==================================================

            unavailable_phrases = [
                "sorry, it's unavailable",
                "sorry, it’s unavailable",
                "currently unavailable",
                "not available",
                "unavailable",
            ]

            for phrase in unavailable_phrases:

                if phrase in wairau_section:

                    result["status"] = (
                        "out_of_stock"
                    )

                    result["stock"] = False

                    result["reason"] = (
                        "Wairau Park explicitly "
                        "says unavailable"
                    )

                    print()
                    print(
                        "RESULT: Wairau Park "
                        "is OUT OF STOCK"
                    )

                    page.screenshot(
                        path="jbhifi_debug.png",
                        full_page=True,
                    )

                    return result

            # ==================================================
            # IN STOCK
            # ==================================================

            available_phrases = [
                "1 hour click & collect",
                "1 hour click and collect",
                "click & collect",
                "click and collect",
                "in-store",
                "in store",
            ]

            for phrase in available_phrases:

                if phrase in wairau_section:

                    result["status"] = (
                        "in_stock"
                    )

                    result["stock"] = True

                    result["reason"] = (
                        "Wairau Park has "
                        "Click & Collect / "
                        "In-store availability"
                    )

                    print()
                    print(
                        "RESULT: Wairau Park "
                        "is IN STOCK!"
                    )

                    page.screenshot(
                        path="jbhifi_debug.png",
                        full_page=True,
                    )

                    return result

            # ==================================================
            # UNKNOWN
            # ==================================================

            result["status"] = "unknown"

            result["stock"] = False

            result["reason"] = (
                "Wairau Park was found but "
                "availability could not "
                "be determined"
            )

            print()
            print(
                "RESULT: UNKNOWN"
            )

            page.screenshot(
                path="jbhifi_debug.png",
                full_page=True,
            )

            return result

        except PlaywrightTimeoutError as e:

            result["status"] = "unknown"

            result["stock"] = False

            result["reason"] = (
                f"JB Hi-Fi browser timeout: {e}"
            )

            print(
                result["reason"]
            )

            try:

                page.screenshot(
                    path="jbhifi_debug.png",
                    full_page=True,
                )

            except Exception:
                pass

            return result

        except Exception as e:

            result["status"] = "unknown"

            result["stock"] = False

            result["reason"] = (
                f"JB Hi-Fi browser error: {e}"
            )

            print(
                result["reason"]
            )

            try:

                page.screenshot(
                    path="jbhifi_debug.png",
                    full_page=True,
                )

            except Exception:
                pass

            return result

        finally:

            browser.close()

# ============================================================
# OTHER RETAILERS
# ============================================================

def check_generic_retailer(name, url):

    print()
    print("=" * 60)
    print(f"CHECKING {name}")
    print("=" * 60)

    try:

        response = requests.get(
            url,
            headers={
                "User-Agent": USER_AGENT,
                "Accept-Language": "en-NZ,en;q=0.9",
            },
            timeout=30,
        )

        print(
            "HTTP status:",
            response.status_code
        )

        if response.status_code != 200:

            return {
                "status": "unknown",
                "stock": False,
                "reason": (
                    f"HTTP {response.status_code}"
                ),
            }

        text = response.text.lower()

        # Negative phrases first.
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
                    "status": "out_of_stock",
                    "stock": False,
                    "reason": (
                        f"Detected: {phrase}"
                    ),
                }

        positive_phrases = [
            "add to cart",
            "add to bag",
            "buy now",
            "purchase",
        ]

        for phrase in positive_phrases:

            if phrase in text:

                return {
                    "status": "in_stock",
                    "stock": True,
                    "reason": (
                        f"Detected: {phrase}"
                    ),
                }

        return {
            "status": "unknown",
            "stock": False,
            "reason": (
                "No reliable stock indicator detected"
            ),
        }

    except Exception as e:

        return {
            "status": "unknown",
            "stock": False,
            "reason": f"Error: {e}",
        }


# ============================================================
# STOCK EMAIL
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
The tracker detected a change from unavailable
to available.

It will continue checking automatically.
"""

    return send_email(
        subject,
        body,
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("PS5 PRO STOCK TRACKER")
    print("=" * 60)

    print(
        "TEST_MODE:",
        TEST_MODE
    )

    print(
        "Email configured:",
        bool(RESEND_API_KEY)
    )

    # ========================================================
    # TEST MODE
    # ========================================================

    if TEST_MODE:

        print()
        print("TEST MODE ENABLED")
        print("Sending test email...")

        if send_test_email():
            print(
                "Test email sent successfully."
            )
        else:
            print(
                "Test email failed."
            )

        return

    # ========================================================
    # LOAD PREVIOUS STATE
    # ========================================================

    previous_state = load_state()

    print()
    print("Previous state:")

    for retailer, state in previous_state.items():

        print(
            f"  {retailer}: "
            f"{state.get('status', 'unknown')}"
        )

    # ========================================================
    # CURRENT STATE
    # ========================================================

    current_state = {}

    # ========================================================
    # JB HI-FI
    # ========================================================

    jb_result = check_jbhifi_wairau()

    # --------------------------------------------------------
    # IMPORTANT:
    #
    # If JB Hi-Fi returns UNKNOWN, preserve the previous
    # state instead of changing it to OUT OF STOCK.
    # --------------------------------------------------------

    if jb_result["status"] == "unknown":

        previous_jb = previous_state.get(
            "JB Hi-Fi",
            {
                "status": "unknown",
                "stock": False,
                "reason": "No previous state",
            },
        )

        current_state["JB Hi-Fi"] = {
            "status": "unknown",
            "stock": previous_jb.get(
                "stock",
                False,
            ),
            "reason": jb_result["reason"],
        }

        print()
        print(
            "JB Hi-Fi result is UNKNOWN."
        )

        print(
            "Previous stock state will be preserved."
        )

    else:

        current_state["JB Hi-Fi"] = jb_result

    # ========================================================
    # OTHER RETAILERS
    # ========================================================

    for retailer in [
        "Noel Leeming",
        "Harvey Norman",
        "The Warehouse",
    ]:

        result = check_generic_retailer(
            retailer,
            PRODUCTS[retailer],
        )

        # Preserve previous state if the request failed.
        if result["status"] == "unknown":

            previous_result = previous_state.get(
                retailer,
                {
                    "stock": False,
                    "status": "unknown",
                },
            )

            result["stock"] = previous_result.get(
                "stock",
                False,
            )

        current_state[retailer] = result

        print(
            f"{retailer}: "
            f"Status={result['status']}, "
            f"Stock={result['stock']}, "
            f"Reason={result['reason']}"
        )

    # ========================================================
    # PRINT CURRENT STATE
    # ========================================================

    print()
    print("=" * 60)
    print("CURRENT STOCK STATE")
    print("=" * 60)

    for retailer, result in current_state.items():

        if result["status"] == "in_stock":
            display_status = "IN STOCK"

        elif result["status"] == "out_of_stock":
            display_status = "OUT OF STOCK"

        else:
            display_status = "UNKNOWN"

        print(
            f"{retailer}: {display_status}"
        )

        print(
            f"  Reason: {result['reason']}"
        )

    # ========================================================
    # FIND NEWLY AVAILABLE STOCK
    # ========================================================

    newly_available = {}

    for retailer, result in current_state.items():

        current_stock = result["stock"]

        previous_stock = previous_state.get(
            retailer,
            {},
        ).get(
            "stock",
            False,
        )

        # Only alert when we have positively identified
        # that the product is in stock.
        if current_stock and not previous_stock:

            newly_available[retailer] = result

    # ========================================================
    # SEND ALERT
    # ========================================================

    if newly_available:

        print()
        print(
            "🚨 NEW STOCK DETECTED!"
        )

        for retailer in newly_available:

            print(
                f"  {retailer}"
            )

        send_stock_email(
            newly_available
        )

    else:

        print()
        print(
            "No newly available stock."
        )

        print(
            "No alert email sent."
        )

    # ========================================================
    # SAVE STATE
    # ========================================================

    save_state(current_state)

    print()
    print(
        "New state saved."
    )

    print()
    print("=" * 60)
    print("TRACKER FINISHED")
    print("=" * 60)


if __name__ == "__main__":
    main()
