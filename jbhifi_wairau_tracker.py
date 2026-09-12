import time
from playwright.sync_api import sync_playwright

PRODUCT_URL = (
    "https://www.jbhifi.co.nz/products/"
    "ps5-playstation-5-pro-2tb-console"
)

WAIRAU_SEARCH = "Wairau Park"


def main():

    print("=" * 70)
    print("JB HI-FI WAIRAU PS5 PRO TRACKER")
    print("STAGE 6 - CLOSE CART SLIDEOUT")
    print("=" * 70)

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=True
        )

        page = browser.new_page(
            viewport={
                "width": 1440,
                "height": 1200
            },
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            )
        )

        try:

            # ============================================================
            # OPEN PRODUCT
            # ============================================================

            print()
            print("=" * 70)
            print("OPENING PS5 PRO")
            print("=" * 70)

            response = page.goto(
                PRODUCT_URL,
                wait_until="domcontentloaded",
                timeout=60000
            )

            if response:
                print(
                    "HTTP status:",
                    response.status
                )

            page.wait_for_timeout(5000)

            print(
                "Page title:",
                page.title()
            )

            # ============================================================
            # ADD TO CART
            # ============================================================

            print()
            print("=" * 70)
            print("ADDING PS5 PRO TO CART")
            print("=" * 70)

            add_buttons = page.get_by_role(
                "button",
                name="Add to cart",
                exact=False
            )

            print(
                "Add to cart buttons found:",
                add_buttons.count()
            )

            if add_buttons.count() == 0:
                print(
                    "ERROR: Add to cart button not found."
                )
                return

            add_buttons.first.click(
                timeout=10000
            )

            print(
                "✓ PS5 Pro added to cart."
            )

            page.wait_for_timeout(3000)

            # ============================================================
            # CART SLIDEOUT
            # ============================================================

            print()
            print("=" * 70)
            print("CHECKING CART SLIDEOUT")
            print("=" * 70)

            slideout = page.locator(
                '[data-testid="attach-slideout"]'
            )

            print(
                "Cart slideout count:",
                slideout.count()
            )

            if slideout.count() > 0:

                print(
                    "Cart slideout visible:",
                    slideout.first.is_visible()
                )

            # ============================================================
            # TRY ESCAPE
            # ============================================================

            print()
            print("=" * 70)
            print("CLOSING CART WITH ESCAPE")
            print("=" * 70)

            page.keyboard.press("Escape")

            page.wait_for_timeout(1500)

            if slideout.count() > 0:

                print(
                    "Cart slideout visible after Escape:",
                    slideout.first.is_visible()
                )

            # ============================================================
            # IF STILL OPEN, INSPECT BUTTONS INSIDE SLIDEOUT
            # ============================================================

            if (
                slideout.count() > 0
                and slideout.first.is_visible()
            ):

                print()
                print("=" * 70)
                print("CART STILL OPEN - INSPECTING BUTTONS")
                print("=" * 70)

                slide_buttons = slideout.first.get_by_role(
                    "button"
                )

                print(
                    "Buttons inside cart slideout:",
                    slide_buttons.count()
                )

                for i in range(
                    slide_buttons.count()
                ):

                    try:

                        button = slide_buttons.nth(i)

                        print(
                            f"[SLIDEOUT BUTTON {i}] "
                            f"text={button.inner_text(
                                timeout=1000
                            )!r} "
                            f"aria-label={button.get_attribute(
                                'aria-label'
                            )!r} "
                            f"title={button.get_attribute(
                                'title'
                            )!r}"
                        )

                    except Exception:
                        pass

                # --------------------------------------------------------
                # Look for common close buttons
                # --------------------------------------------------------

                close_candidates = [
                    '[aria-label="Close"]',
                    '[aria-label="close"]',
                    'button[title="Close"]',
                    'button[data-testid*="close"]'
                ]

                closed = False

                for selector in close_candidates:

                    try:

                        close_button = slideout.first.locator(
                            selector
                        )

                        if (
                            close_button.count() > 0
                            and close_button.first.is_visible()
                        ):

                            print(
                                "Trying close button:",
                                selector
                            )

                            close_button.first.click(
                                timeout=5000
                            )

                            page.wait_for_timeout(1500)

                            print(
                                "✓ Close button clicked."
                            )

                            closed = True
                            break

                    except Exception as e:

                        print(
                            "Close attempt failed:",
                            repr(e)
                        )

                if not closed:

                    print(
                        "No obvious close button found."
                    )

            # ============================================================
            # FINAL SLIDEOUT CHECK
            # ============================================================

            print()
            print("=" * 70)
            print("FINAL CART SLIDEOUT CHECK")
            print("=" * 70)

            if slideout.count() > 0:

                print(
                    "Cart slideout visible:",
                    slideout.first.is_visible()
                )

            # ============================================================
            # LOCATION INPUT
            # ============================================================

            print()
            print("=" * 70)
            print("CHECKING LOCATION SEARCH")
            print("=" * 70)

            location_input = page.locator(
                'input[name="location-search-pdp"]'
            )

            print(
                "Location fields:",
                location_input.count()
            )

            if location_input.count() == 0:
                print(
                    "ERROR: location-search-pdp not found."
                )
                return

            print(
                "Location field visible:",
                location_input.first.is_visible()
            )

            # ============================================================
            # CLICK LOCATION FIELD
            # ============================================================

            if location_input.first.is_visible():

                print()
                print("=" * 70)
                print("CLICKING LOCATION SEARCH")
                print("=" * 70)

                location_input.first.click(
                    timeout=10000
                )

                print(
                    "✓ Location search clicked."
                )

                page.wait_for_timeout(2000)

            else:

                print(
                    "ERROR: Location field is not visible."
                )
                return

            # ============================================================
            # INSPECT STORE FIELD
            # ============================================================

            print()
            print("=" * 70)
            print("CHECKING STORE AVAILABILITY FIELD")
            print("=" * 70)

            store_input = page.locator(
                'input[name="store-availability-search"]'
            )

            print(
                "Store availability fields:",
                store_input.count()
            )

            if store_input.count() > 0:

                print(
                    "Store field visible:",
                    store_input.first.is_visible()
                )

            # ============================================================
            # SEARCH WAIRAU
            # ============================================================

            if (
                store_input.count() > 0
                and store_input.first.is_visible()
            ):

                print()
                print("=" * 70)
                print("SEARCHING FOR WAIRAU PARK")
                print("=" * 70)

                store_input.first.fill(
                    WAIRAU_SEARCH
                )

                print(
                    "Entered:",
                    WAIRAU_SEARCH
                )

                page.wait_for_timeout(3000)

                store_input.first.press(
                    "Enter"
                )

                print(
                    "✓ Pressed Enter."
                )

                page.wait_for_timeout(5000)

                # ========================================================
                # RESULT
                # ========================================================

                print()
                print("=" * 70)
                print("PAGE CONTENT AFTER WAIRAU SEARCH")
                print("=" * 70)

                text = page.locator(
                    "body"
                ).inner_text()

                print(text)

                print()
                print("=" * 70)
                print("RESULT KEYWORDS")
                print("=" * 70)

                lower_text = text.lower()

                keywords = [
                    "wairau",
                    "wairau park",
                    "available",
                    "unavailable",
                    "in stock",
                    "out of stock",
                    "click & collect",
                    "click and collect",
                    "collect",
                    "pickup",
                    "pick up",
                    "store",
                    "review cart",
                    "checkout"
                ]

                for keyword in keywords:

                    if keyword.lower() in lower_text:

                        print(
                            "FOUND:",
                            keyword
                        )

                    else:

                        print(
                            "NOT FOUND:",
                            keyword
                        )

                # ========================================================
                # WAIRAU ELEMENTS
                # ========================================================

                print()
                print("=" * 70)
                print("WAIRAU ELEMENTS")
                print("=" * 70)

                wairau_elements = page.get_by_text(
                    "Wairau",
                    exact=False
                )

                print(
                    "Wairau elements:",
                    wairau_elements.count()
                )

                for i in range(
                    min(wairau_elements.count(), 30)
                ):

                    try:

                        element = (
                            wairau_elements.nth(i)
                        )

                        print(
                            f"[WAIRAU {i}] "
                            f"{element.inner_text(
                                timeout=1000
                            )}"
                        )

                    except Exception:
                        pass

                # ========================================================
                # SCREENSHOT
                # ========================================================

                page.screenshot(
                    path="wairau_stage6_result.png",
                    full_page=True
                )

                print(
                    "Saved: wairau_stage6_result.png"
                )

            else:

                print()
                print(
                    "ERROR: Store availability field "
                    "is still hidden."
                )

                page.screenshot(
                    path="wairau_stage6_error.png",
                    full_page=True
                )

        except Exception as e:

            print()
            print("=" * 70)
            print("ERROR")
            print("=" * 70)

            print(
                repr(e)
            )

            try:

                page.screenshot(
                    path="wairau_stage6_error.png",
                    full_page=True
                )

                print(
                    "Saved: wairau_stage6_error.png"
                )

            except Exception:
                pass

        finally:

            browser.close()

            print()
            print("=" * 70)
            print("STAGE 6 FINISHED")
            print("=" * 70)


if __name__ == "__main__":
    main()
