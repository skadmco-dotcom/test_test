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
    print("STAGE 4 - OPEN STORE SEARCH + SEARCH WAIRAU PARK")
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
            # PRINT STORE AVAILABILITY TEXT
            # ============================================================

            print()
            print("=" * 70)
            print("LOOKING FOR STORE AVAILABILITY")
            print("=" * 70)

            body_text = page.locator(
                "body"
            ).inner_text()

            print(body_text)

            # ============================================================
            # CLICK "ENTER POSTCODE OR SUBURB"
            # ============================================================

            print()
            print("=" * 70)
            print("OPENING STORE SEARCH")
            print("=" * 70)

            postcode_text = page.get_by_text(
                "Enter postcode or suburb",
                exact=True
            )

            print(
                "Enter postcode/suburb elements:",
                postcode_text.count()
            )

            if postcode_text.count() > 0:

                try:

                    postcode_text.first.click(
                        timeout=10000
                    )

                    print(
                        "✓ Clicked 'Enter postcode or suburb'."
                    )

                except Exception as e:

                    print(
                        "Text click failed:",
                        repr(e)
                    )

                    # Try clicking the parent element
                    try:

                        postcode_text.first.locator(
                            ".."
                        ).click(
                            timeout=10000
                        )

                        print(
                            "✓ Clicked parent of "
                            "'Enter postcode or suburb'."
                        )

                    except Exception as e2:

                        print(
                            "Parent click also failed:",
                            repr(e2)
                        )

            else:

                print(
                    "ERROR: 'Enter postcode or suburb' "
                    "was not found."
                )

            # Give the UI time to open
            page.wait_for_timeout(2000)

            # ============================================================
            # FIND STORE SEARCH INPUT
            # ============================================================

            print()
            print("=" * 70)
            print("FINDING STORE SEARCH INPUT")
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
                    "ERROR: Store availability search "
                    "field not found."
                )
                return

            print(
                "✓ Store availability search "
                "field exists."
            )

            # Check visibility
            print(
                "Field visible:",
                search_input.first.is_visible()
            )

            # ============================================================
            # SEARCH WAIRAU PARK
            # ============================================================

            print()
            print("=" * 70)
            print("SEARCHING FOR WAIRAU PARK")
            print("=" * 70)

            # Wait until visible
            try:

                search_input.first.wait_for(
                    state="visible",
                    timeout=10000
                )

                print(
                    "✓ Search field is now visible."
                )

            except Exception as e:

                print(
                    "ERROR: Search field did not "
                    "become visible."
                )

                print(
                    repr(e)
                )

                # Print all inputs for debugging
                inputs = page.locator("input")

                print()
                print("CURRENT INPUTS:")

                for i in range(inputs.count()):

                    try:

                        inp = inputs.nth(i)

                        print(
                            f"INPUT {i}: "
                            f"name={inp.get_attribute('name')!r} "
                            f"type={inp.get_attribute('type')!r} "
                            f"visible={inp.is_visible()} "
                            f"value={inp.input_value()!r}"
                        )

                    except Exception:
                        pass

                page.screenshot(
                    path="wairau_stage4_error.png",
                    full_page=True
                )

                return

            # Fill the field
            search_input.first.fill(
                WAIRAU_SEARCH
            )

            print(
                "Entered:",
                WAIRAU_SEARCH
            )

            page.wait_for_timeout(3000)

            print(
                "Pressing Enter..."
            )

            search_input.first.press(
                "Enter"
            )

            page.wait_for_timeout(5000)

            # ============================================================
            # PRINT RESULTS
            # ============================================================

            print()
            print("=" * 70)
            print("PAGE CONTENT AFTER WAIRAU SEARCH")
            print("=" * 70)

            text = page.locator(
                "body"
            ).inner_text()

            print(text)

            # ============================================================
            # KEYWORD CHECK
            # ============================================================

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

            # ============================================================
            # WAIRAU ELEMENTS
            # ============================================================

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

            # ============================================================
            # BUTTONS
            # ============================================================

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

            # ============================================================
            # SAVE SCREENSHOT
            # ============================================================

            print()
            print("=" * 70)
            print("SAVING SCREENSHOT")
            print("=" * 70)

            page.screenshot(
                path="wairau_stage4.png",
                full_page=True
            )

            print(
                "Saved: wairau_stage4.png"
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
                    path="wairau_stage4_error.png",
                    full_page=True
                )

                print(
                    "Saved: wairau_stage4_error.png"
                )

            except Exception:
                pass

        finally:

            browser.close()

            print()
            print("=" * 70)
            print("STAGE 4 FINISHED")
            print("=" * 70)


if __name__ == "__main__":
    main()
