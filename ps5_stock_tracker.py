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

            add_to_cart_found = False

            add_to_cart_selectors = [
                "button:has-text('Add to cart')",
                "button:has-text('Add to Cart')",
                "text=Add to cart",
                "text=Add to Cart",
            ]

            for selector in add_to_cart_selectors:

                try:

                    locator = page.locator(
                        selector
                    ).first

                    if locator.is_visible(timeout=3000):

                        print(
                            f"Found Add to cart using: "
                            f"{selector}"
                        )

                        locator.click()

                        add_to_cart_found = True

                        break

                except Exception:
                    pass

            if not add_to_cart_found:

                result["reason"] = (
                    "Could not find Add to cart button"
                )

                print(result["reason"])

                page.screenshot(
                    path="jbhifi_debug.png",
                    full_page=True,
                )

                return result

            print("Added product to cart.")

            page.wait_for_timeout(5000)

            # ==================================================
            # STEP 3 — REVIEW CART
            # ==================================================

            print()
            print("Looking for Review cart...")

            review_cart_found = False

            review_selectors = [
                "text=Review cart",
                "text=Review Cart",
                "text=View cart",
                "text=View Cart",
                "a[href*='/cart']",
                "a[href*='cart']",
            ]

            for selector in review_selectors:

                try:

                    locator = page.locator(
                        selector
                    ).first

                    if locator.is_visible(timeout=3000):

                        print(
                            f"Found cart link using: "
                            f"{selector}"
                        )

                        locator.click()

                        review_cart_found = True

                        break

                except Exception:
                    pass

            if not review_cart_found:

                print(
                    "Review cart button not found."
                )

                print(
                    "Opening /cart directly..."
                )

                try:

                    page.goto(
                        "https://www.jbhifi.co.nz/cart",
                        wait_until="domcontentloaded",
                        timeout=60000,
                    )

                    review_cart_found = True

                except Exception as e:

                    print(
                        f"Could not open cart: {e}"
                    )

            page.wait_for_timeout(5000)

            print("Cart page loaded.")

            # ==================================================
            # STEP 4 — CHECK STORE AVAILABILITY
            # ==================================================

            print()
            print(
                "Looking for Check store availability..."
            )

            availability_found = False

            availability_selectors = [
                "text=Check store availability",
                "text=Check Store Availability",
                "text=Check availability",
                "text=Check Availability",
                "button:has-text('Check store availability')",
                "button:has-text('Check availability')",
            ]

            for selector in availability_selectors:

                try:

                    locator = page.locator(
                        selector
                    ).first

                    if locator.is_visible(timeout=3000):

                        print(
                            f"Found availability control: "
                            f"{selector}"
                        )

                        locator.click()

                        availability_found = True

                        break

                except Exception:
                    pass

            if not availability_found:

                current_text = get_page_text(page)

                if (
                    "store availability"
                    in current_text
                    or
                    "postcode or suburb"
                    in current_text
                    or
                    "getting your item"
                    in current_text
                ):

                    print(
                        "Store availability section "
                        "already visible."
                    )

                    availability_found = True

            if not availability_found:

                result["reason"] = (
                    "Could not find Check store availability"
                )

                print(result["reason"])

                page.screenshot(
                    path="jbhifi_debug.png",
                    full_page=True,
                )

                return result

            page.wait_for_timeout(3000)

            # ==================================================
            # STEP 5 — FIND "GETTING YOUR ITEM" TEXT BOX
            # ==================================================

            print()
            print(
                "Looking for 'Getting your item' text box..."
            )

            search_box = None

            # Find the Getting your item text.
            getting_item = None

            try:

                getting_item = page.get_by_text(
                    "Getting your item",
                    exact=True
                ).first

                if getting_item.is_visible(timeout=3000):

                    print(
                        "Found 'Getting your item' section."
                    )

            except Exception:
                getting_item = None

            # --------------------------------------------------
            # Look inside the parent containers of
            # "Getting your item" for the correct input.
            # --------------------------------------------------

            if getting_item:

                current = getting_item

                for level in range(8):

                    try:

                        parent = current.locator("..")

                        inputs = parent.locator(
                            "input"
                        )

                        count = inputs.count()

                        print(
                            f"Checking parent level "
                            f"{level}: {count} input(s)"
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

                                print(
                                    f"Input candidate: "
                                    f"placeholder="
                                    f"'{placeholder}', "
                                    f"aria-label="
                                    f"'{aria_label}'"
                                )

                                combined = (
                                    placeholder
                                    + " "
                                    + aria_label
                                ).lower()

                                # Ignore the global website
                                # product search box.
                                if (
                                    "search products"
                                    in combined
                                    or
                                    "search for products"
                                    in combined
                                ):
                                    continue

                                search_box = candidate

                                print(
                                    "Selected input associated "
                                    "with 'Getting your item'."
                                )

                                break

                            except Exception:
                                pass

                        if search_box:
                            break

                        current = parent

                    except Exception:
                        break

            # --------------------------------------------------
            # FALLBACK
            # --------------------------------------------------

            if not search_box:

                print(
                    "Could not find input directly under "
                    "'Getting your item'."
                )

                print(
                    "Trying visible inputs as fallback..."
                )

                try:

                    inputs = page.locator("input")

                    count = inputs.count()

                    print(
                        f"Found {count} total input fields."
                    )

                    for i in range(count):

                        try:

                            candidate = inputs.nth(i)

                            if not candidate.is_visible(
                                timeout=500
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

                            combined = (
                                placeholder
                                + " "
                                + aria_label
                            ).lower()

                            print(
                                f"Input {i}: "
                                f"placeholder="
                                f"'{placeholder}', "
                                f"aria-label="
                                f"'{aria_label}'"
                            )

                            if (
                                "search products"
                                in combined
                                or
                                "search for products"
                                in combined
                            ):
                                continue

                            search_box = candidate

                            print(
                                f"Selected input {i} "
                                "as store/location input."
                            )

                            break

                        except Exception:
                            pass

                except Exception as e:

                    print(
                        f"Fallback input search error: {e}"
                    )

            if not search_box:

                result["reason"] = (
                    "Could not find the "
                    "'Getting your item' text box"
                )

                print(result["reason"])

                page.screenshot(
                    path="jbhifi_debug.png",
                    full_page=True,
                )

                return result

            # ==================================================
            # STEP 6 — SEARCH FOR WAIRAU PARK
            # ==================================================

            print()
            print(
                f"Searching for: {STORE_SEARCH}"
            )

            search_box.fill(STORE_SEARCH)

            page.wait_for_timeout(2000)

            try:

                search_box.press("Enter")

            except Exception:
                pass

            page.wait_for_timeout(4000)

            # ==================================================
            # STEP 7 — SELECT WAIRAU PARK
            # ==================================================

            print()
            print(
                "Looking for Wairau Park result..."
            )

            wairau_found = False

            wairau_selectors = [
                "text=Wairau Park",
                "text=Wairau",
                "[aria-label*='Wairau Park']",
                "[aria-label*='Wairau']",
            ]

            for selector in wairau_selectors:

                try:

                    locator = page.locator(
                        selector
                    ).first

                    if locator.is_visible(timeout=3000):

                        print(
                            f"Found Wairau using: "
                            f"{selector}"
                        )

                        locator.click()

                        wairau_found = True

                        break

                except Exception:
                    pass

            if not wairau_found:

                current_text = get_page_text(page)

                if "wairau park" in current_text:

                    print(
                        "Wairau Park is already displayed."
                    )

                    wairau_found = True

            if not wairau_found:

                result["reason"] = (
                    "Wairau Park was not found after "
                    "store search"
                )

                print(result["reason"])

                page.screenshot(
                    path="jbhifi_debug.png",
                    full_page=True,
                )

                return result

            page.wait_for_timeout(3000)

            # ==================================================
            # STEP 8 — READ STORE AVAILABILITY
            # ==================================================

            print()
            print(
                "Checking Wairau Park availability..."
            )

            body_text = get_page_text(page)

            wairau_position = body_text.find(
                "wairau park"
            )

            if wairau_position == -1:

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

            wairau_section = body_text[
                wairau_position:
                wairau_position + 1500
            ]

            print()
            print("--- WAIRAU PARK SECTION ---")
            print(
                wairau_section[:1500]
            )
            print("--- END WAIRAU SECTION ---")
            print()

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

                    result["status"] = "out_of_stock"
                    result["stock"] = False
                    result["reason"] = (
                        "Wairau Park explicitly says "
                        "unavailable"
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

                    result["status"] = "in_stock"
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
                "Wairau Park was found but its "
                "availability could not be determined"
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

            print(result["reason"])

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

            print(result["reason"])

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
