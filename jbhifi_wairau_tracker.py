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
    print("STAGE 5 - USE VISIBLE LOCATION SEARCH")
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
            # FIND VISIBLE LOCATION INPUT
            # ============================================================

            print()
            print("=" * 70)
            print("FINDING VISIBLE LOCATION SEARCH")
            print("=" * 70)

            location_input = page.locator(
                'input[name="location-search-pdp"]'
            )

            count = location_input.count()

            print(
                "Location search fields found:",
                count
            )

            if count == 0:
                print(
                    "ERROR: location-search-pdp "
                    "was not found."
                )
                return

            print(
                "Field visible:",
                location_input.first.is_visible()
            )

            if not location_input.first.is_visible():
                print(
                    "ERROR: location-search-pdp "
                    "is not visible."
                )
                return

            print(
                "✓ Visible location search found."
            )

            # ============================================================
            # CLICK LOCATION FIELD
            # ============================================================

            print()
            print("=" * 70)
            print("OPENING LOCATION SEARCH")
            print("=" * 70)

            location_input.first.click(
                timeout=10000
            )

            print(
                "✓ Clicked location search."
            )

            page.wait_for_timeout(2000)

            # ============================================================
            # INSPECT AFTER CLICK
            # ============================================================

            print()
            print("=" * 70)
            print("INPUTS AFTER CLICKING LOCATION SEARCH")
            print("=" * 70)

            inputs = page.locator("input")

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

            # ============================================================
            # CHECK STORE AVAILABILITY INPUT
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
            # CHECK PAGE TEXT
            # ============================================================

            print()
            print("=" * 70)
            print("PAGE TEXT AFTER LOCATION CLICK")
            print("=" * 70)

            text = page.locator(
                "body"
            ).inner_text()

            print(text)

            # ============================================================
            # SCREENSHOT
            # ============================================================

            print()
            print("=" * 70)
            print("SAVING SCREENSHOT")
            print("=" * 70)

            page.screenshot(
                path="wairau_stage5_after_location_click.png",
                full_page=True
            )

            print(
                "Saved: "
                "wairau_stage5_after_location_click.png"
            )

            # ============================================================
            # SEARCH WAIRAU IF STORE FIELD IS NOW VISIBLE
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

                print(
                    "Pressing Enter..."
                )

                store_input.first.press(
                    "Enter"
                )

                page.wait_for_timeout(5000)

                print()
                print("=" * 70)
                print("RESULT AFTER WAIRAU SEARCH")
                print("=" * 70)

                result_text = page.locator(
                    "body"
                ).inner_text()

                print(result_text)

                # --------------------------------------------------------
                # KEYWORDS
                # --------------------------------------------------------

                print()
                print("=" * 70)
                print("RESULT KEYWORDS")
                print("=" * 70)

                lower_text = result_text.lower()

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

                # --------------------------------------------------------
                # WAIRAU ELEMENTS
                # --------------------------------------------------------

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

                # --------------------------------------------------------
                # SAVE RESULT SCREENSHOT
                # --------------------------------------------------------

                page.screenshot(
                    path="wairau_stage5_result.png",
                    full_page=True
                )

                print(
                    "Saved: wairau_stage5_result.png"
                )

            else:

                print()
                print(
                    "Store availability field is STILL hidden."
                )

                print(
                    "We will use the Stage 5 output "
                    "to determine what opens."
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
                    path="wairau_stage5_error.png",
                    full_page=True
                )

                print(
                    "Saved: wairau_stage5_error.png"
                )

            except Exception:
                pass

        finally:

            browser.close()

            print()
            print("=" * 70)
            print("STAGE 5 FINISHED")
            print("=" * 70)


if __name__ == "__main__":
    main()
