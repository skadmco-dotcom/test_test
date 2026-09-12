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
    print("STAGE 3 - SEARCH WAIRAU PARK")
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

            # ==================================================
            # OPEN PRODUCT PAGE
            # ==================================================

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

            # ==================================================
            # ADD PS5 PRO TO CART
            # ==================================================

            print()
            print("=" * 70)
            print("ADDING PS5 PRO TO CART")
            print("=" * 70)

            # The first Add to cart button is the
            # PS5 Pro product button.
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

            # ==================================================
            # FIND STORE AVAILABILITY FIELD
            # ==================================================

            print()
            print("=" * 70)
            print("FINDING STORE AVAILABILITY FIELD")
            print("=" * 70)

            search_input = page.locator(
                'input[name="store-availability-search"]'
            )

            count = search_input.count()

            print(
                "Store availability fields found:",
                count
            )

            if count == 0:

                print(
                    "ERROR: Store availability "
                    "search field not found."
                )

                return

            print(
                "✓ Store availability search "
                "field found."
            )

            # ==================================================
            # ENTER WAIRAU PARK
            # ==================================================

            print()
            print("=" * 70)
            print("SEARCHING FOR WAIRAU PARK")
            print("=" * 70)

            search_input.first.fill(
                WAIRAU_SEARCH
            )

            print(
                "Entered:",
                WAIRAU_SEARCH
            )

            # Give the website time to generate
            # the autocomplete/search results.
            page.wait_for_timeout(3000)

            # ==================================================
            # PRESS ENTER
            # ==================================================

            print()
            print(
                "Pressing Enter..."
            )

            search_input.first.press(
                "Enter"
            )

            page.wait_for_timeout(5000)

            # ==================================================
            # PRINT PAGE TEXT
            # ==================================================

            print()
            print("=" * 70)
            print("PAGE CONTENT AFTER WAIRAU SEARCH")
            print("=" * 70)

            text = page.locator(
                "body"
            ).inner_text()

            print(text)

            # ==================================================
            # SEARCH FOR IMPORTANT TERMS
            # ==================================================

            print()
            print("=" * 70)
            print("WAIRAU RESULT CHECK")
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
                "add to cart",
                "review cart"
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

            # ==================================================
            # FIND WAIRAU ELEMENTS
            # ==================================================

            print()
            print("=" * 70)
            print("WAIRAU ELEMENTS")
            print("=" * 70)

            wairau_elements = page.get_by_text(
                "Wairau",
                exact=False
            )

            wairau_count = (
                wairau_elements.count()
            )

            print(
                "Wairau elements found:",
                wairau_count
            )

            for i in range(
                min(wairau_count, 30)
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

            # ==================================================
            # FIND BUTTONS
            # ==================================================

            print()
            print("=" * 70)
            print("BUTTONS AFTER WAIRAU SEARCH")
            print("=" * 70)

            buttons = page.get_by_role(
                "button"
            )

            button_count = buttons.count()

            print(
                "Number of buttons:",
                button_count
            )

            for i in range(button_count):

                try:

                    button = buttons.nth(i)

                    name = button.inner_text(
                        timeout=1000
                    ).strip()

                    if name:

                        print(
                            f"[BUTTON {i}] {name}"
                        )

                except Exception:

                    pass

            # ==================================================
            # SAVE SCREENSHOT
            # ==================================================

            print()
            print("=" * 70)
            print("SAVING SCREENSHOT")
            print("=" * 70)

            page.screenshot(
                path="wairau_stage3.png",
                full_page=True
            )

            print(
                "Saved: wairau_stage3.png"
            )

            print()
            print(
                "Waiting before closing..."
            )

            time.sleep(5)

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
                    path="wairau_stage3_error.png",
                    full_page=True
                )

                print(
                    "Saved: wairau_stage3_error.png"
                )

            except Exception:

                pass

        finally:

            browser.close()

            print()
            print("=" * 70)
            print("STAGE 3 FINISHED")
            print("=" * 70)


if __name__ == "__main__":
    main()
