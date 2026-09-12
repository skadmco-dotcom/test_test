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
            # 1. OPEN PRODUCT
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
            # 2. ADD TO CART
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
            # 3. OPEN CART
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
            # 4. FIND GETTING YOUR ITEM
            # ==================================================

            print()
            print(
                "Looking for 'Getting your item'..."
            )

            getting = page.get_by_text(
                "Getting your item",
                exact=False,
            ).first

            if not getting.is_visible(timeout=5000):

                result["reason"] = (
                    "Could not find Getting your item"
                )

                print(result["reason"])

                page.screenshot(
                    path="jbhifi_debug.png",
                    full_page=True,
                )

                return result

            print(
                "Found 'Getting your item'."
            )

            # ==================================================
            # 5. IDENTIFY THE CORRECT SECTION
            # ==================================================

            print()
            print(
                "Inspecting elements around "
                "'Getting your item'..."
            )

            # Get the closest useful container.
            container = getting.locator(
                "xpath=ancestor::*[self::div or self::section]"
            ).first

            # Walk through several ancestors looking for
            # one containing an input.
            correct_container = None

            for level in range(1, 8):

                try:

                    ancestor = getting.locator(
                        "xpath="
                        + "/.." * level
                    ).first

                    inputs = ancestor.locator(
                        "input"
                    )

                    count = inputs.count()

                    print(
                        f"Ancestor level {level}: "
                        f"{count} input(s)"
                    )

                    if count > 0:

                        correct_container = ancestor

                        break

                except Exception:
                    pass

            # ==================================================
            # 6. FIND LOCATION INPUT INSIDE SECTION
            # ==================================================

            search_box = None

            if correct_container is not None:

                inputs = correct_container.locator(
                    "input"
                )

                count = inputs.count()

                print(
                    f"Inputs inside selected section: "
                    f"{count}"
                )

                for i in range(count):

                    try:

                        candidate = inputs.nth(i)

                        if not candidate.is_visible(
                            timeout=1000
                        ):
                            continue

                        placeholder = (
                            candidate.get_attribute(
                                "placeholder"
                            )
                            or ""
                        )

                        aria_label = (
                            candidate.get_attribute(
                                "aria-label"
                            )
                            or ""
                        )

                        name = (
                            candidate.get_attribute(
                                "name"
                            )
                            or ""
                        )

                        input_id = (
                            candidate.get_attribute(
                                "id"
                            )
                            or ""
                        )

                        print(
                            f"Section input {i}: "
                            f"placeholder='{placeholder}', "
                            f"aria='{aria_label}', "
                            f"name='{name}', "
                            f"id='{input_id}'"
                        )

                        # Reject the global product search.
                        combined = (
                            placeholder.lower()
                            + " "
                            + aria_label.lower()
                            + " "
                            + name.lower()
                            + " "
                            + input_id.lower()
                        )

                        if (
                            "search products" in combined
                            or
                            "search product" in combined
                        ):
                            print(
                                "Rejected global "
                                "product search."
                            )
                            continue

                        # Prefer anything suggesting location.
                        location_words = [
                            "postcode",
                            "suburb",
                            "store",
                            "location",
                            "address",
                        ]

                        if any(
                            word in combined
                            for word in location_words
                        ):

                            search_box = candidate

                            print(
                                "Selected location "
                                "input."
                            )

                            break

                        # If this is the only input inside
                        # the Getting your item section,
                        # use it.
                        if count == 1:

                            search_box = candidate

                            print(
                                "Selected the only "
                                "input in the section."
                            )

                            break

                    except Exception:
                        pass

            # ==================================================
            # 7. SECOND METHOD:
            # FIND INPUT BASED ON TEXT PROXIMITY
            # ==================================================

            if search_box is None:

                print()
                print(
                    "Trying text-proximity search..."
                )

                all_inputs = page.locator(
                    "input"
                )

                input_count = all_inputs.count()

                for i in range(input_count):

                    try:

                        candidate = all_inputs.nth(i)

                        if not candidate.is_visible(
                            timeout=500
                        ):
                            continue

                        # Get a large ancestor around the input.
                        ancestor = candidate.locator(
                            "xpath=ancestor::div[1]"
                        ).first

                        ancestor_text = (
                            ancestor.inner_text()
                            .lower()
                        )

                        # Skip main product search.
                        if (
                            "search products, brands"
                            in ancestor_text
                        ):
                            continue

                        # Look for location-related context.
                        if (
                            "getting your item"
                            in ancestor_text
                            or
                            "delivery"
                            in ancestor_text
                            or
                            "click & collect"
                            in ancestor_text
                            or
                            "click and collect"
                            in ancestor_text
                            or
                            "store"
                            in ancestor_text
                        ):

                            search_box = candidate

                            print(
                                f"Selected input {i} "
                                "based on surrounding text."
                            )

                            break

                    except Exception:
                        pass

            # ==================================================
            # 8. STOP IF WE CAN'T FIND THE RIGHT INPUT
            # ==================================================

            if search_box is None:

                result["reason"] = (
                    "Could not identify the Getting "
                    "your item location input"
                )

                print()
                print(result["reason"])

                print()
                print(
                    "All visible inputs on page:"
                )

                all_inputs = page.locator(
                    "input"
                )

                for i in range(
                    all_inputs.count()
                ):

                    try:

                        candidate = all_inputs.nth(i)

                        if not candidate.is_visible(
                            timeout=300
                        ):
                            continue

                        print(
                            f"Input {i}: "
                            f"placeholder="
                            f"'{candidate.get_attribute('placeholder')}', "
                            f"aria="
                            f"'{candidate.get_attribute('aria-label')}', "
                            f"name="
                            f"'{candidate.get_attribute('name')}', "
                            f"id="
                            f"'{candidate.get_attribute('id')}'"
                        )

                    except Exception:
                        pass

                page.screenshot(
                    path="jbhifi_debug.png",
                    full_page=True,
                )

                return result

            # ==================================================
            # 9. ENTER WAIRAU
            # ==================================================

            print()
            print(
                "Entering Wairau..."
            )

            search_box.click()

            search_box.fill(
                "Wairau"
            )

            page.wait_for_timeout(3000)

            # ==================================================
            # 10. PRINT WHAT APPEARED
            # ==================================================

            print()
            print(
                "Checking page after entering Wairau..."
            )

            body_text = page.locator(
                "body"
            ).inner_text()

            print(
                body_text[-5000:]
            )

            # ==================================================
            # 11. CLICK CHECK AVAILABILITY
            # ==================================================

            print()
            print(
                "Looking for Check availability..."
            )

            check_button = None

            selectors = [
                "button:has-text('Check availability')",
                "button:has-text('Check Availability')",
                "text=Check availability",
                "text=Check Availability",
                "[aria-label*='Check availability']",
            ]

            for selector in selectors:

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
                            f"using {selector}"
                        )

                        break

                except Exception:
                    pass

            if check_button is None:

                result["reason"] = (
                    "Could not find Check availability "
                    "after entering Wairau"
                )

                print(
                    result["reason"]
                )

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
            # 12. FIND WAIRAU PARK
            # ==================================================

            print()
            print(
                "Looking for Wairau Park..."
            )

            body_text = page.locator(
                "body"
            ).inner_text()

            lower_text = body_text.lower()

            if "wairau park" not in lower_text:

                result["reason"] = (
                    "Wairau Park did not appear "
                    "after availability check"
                )

                print(
                    result["reason"]
                )

                page.screenshot(
                    path="jbhifi_debug.png",
                    full_page=True,
                )

                return result

            print(
                "Wairau Park found."
            )

            # ==================================================
            # 13. CLICK IN-STORE
            # ==================================================

            print()
            print(
                "Looking for In-store..."
            )

            in_store = None

            selectors = [
                "text=In-store",
                "text=In store",
                "button:has-text('In-store')",
                "button:has-text('In store')",
            ]

            for selector in selectors:

                try:

                    candidate = page.locator(
                        selector
                    ).first

                    if candidate.is_visible(
                        timeout=3000
                    ):

                        in_store = candidate

                        print(
                            f"Found In-store "
                            f"using {selector}"
                        )

                        break

                except Exception:
                    pass

            if in_store is not None:

                in_store.click()

                print(
                    "Clicked In-store."
                )

                page.wait_for_timeout(3000)

            else:

                print(
                    "In-store button not found."
                )

            # ==================================================
            # 14. READ RESULT
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
                    "Wairau Park disappeared "
                    "before result could be read"
                )

                print(
                    result["reason"]
                )

                page.screenshot(
                    path="jbhifi_debug.png",
                    full_page=True,
                )

                return result

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

            unavailable = [
                "sorry, it's unavailable",
                "sorry, it’s unavailable",
                "currently unavailable",
                "not available",
                "unavailable",
            ]

            for phrase in unavailable:

                if phrase in wairau_section:

                    result["status"] = (
                        "out_of_stock"
                    )

                    result["stock"] = False

                    result["reason"] = (
                        "Wairau Park explicitly "
                        "says unavailable"
                    )

                    print(
                        "RESULT: OUT OF STOCK"
                    )

                    page.screenshot(
                        path="jbhifi_debug.png",
                        full_page=True,
                    )

                    return result

            # ==================================================
            # IN STOCK
            # ==================================================

            available = [
                "1 hour click & collect",
                "1 hour click and collect",
                "click & collect",
                "click and collect",
                "in-store",
                "in store",
            ]

            for phrase in available:

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

                    print(
                        "RESULT: IN STOCK!"
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
                "Wairau Park found but "
                "availability could not "
                "be determined"
            )

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
