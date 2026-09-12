import time
from playwright.sync_api import sync_playwright

PRODUCT_URL = (
    "https://www.jbhifi.co.nz/products/"
    "ps5-playstation-5-pro-2tb-console"
)


def main():

    print("=" * 70)
    print("JB HI-FI WAIRAU PS5 PRO TRACKER")
    print("STAGE 7 - INSPECT LOCATION UI")
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
                "Add to cart buttons:",
                add_buttons.count()
            )

            add_buttons.first.click(
                timeout=10000
            )

            print(
                "✓ PS5 Pro added to cart."
            )

            page.wait_for_timeout(2500)

            # ============================================================
            # CLOSE CART
            # ============================================================

            print()
            print("=" * 70)
            print("CLOSING CART SLIDEOUT")
            print("=" * 70)

            page.keyboard.press("Escape")

            page.wait_for_timeout(1500)

            slideout = page.locator(
                '[data-testid="attach-slideout"]'
            )

            print(
                "Cart visible:",
                (
                    slideout.count() > 0
                    and slideout.first.is_visible()
                )
            )

            # ============================================================
            # LOCATION FIELD
            # ============================================================

            print()
            print("=" * 70)
            print("CLICKING LOCATION SEARCH")
            print("=" * 70)

            location_input = page.locator(
                'input[name="location-search-pdp"]'
            )

            print(
                "Location input count:",
                location_input.count()
            )

            print(
                "Location input visible:",
                location_input.first.is_visible()
            )

            location_input.first.click(
                timeout=10000
            )

            print(
                "✓ Location input clicked."
            )

            # Give the UI time to animate/open
            page.wait_for_timeout(3000)

            # ============================================================
            # SCREENSHOT
            # ============================================================

            page.screenshot(
                path="wairau_stage7_location_ui.png",
                full_page=True
            )

            print(
                "Saved: wairau_stage7_location_ui.png"
            )

            # ============================================================
            # ALL INPUTS
            # ============================================================

            print()
            print("=" * 70)
            print("ALL INPUTS AFTER LOCATION CLICK")
            print("=" * 70)

            inputs = page.locator("input")

            print(
                "Total inputs:",
                inputs.count()
            )

            for i in range(inputs.count()):

                try:

                    inp = inputs.nth(i)

                    print(
                        f"[INPUT {i}] "
                        f"name={inp.get_attribute('name')!r} "
                        f"id={inp.get_attribute('id')!r} "
                        f"type={inp.get_attribute('type')!r} "
                        f"placeholder={inp.get_attribute('placeholder')!r} "
                        f"aria-label={inp.get_attribute('aria-label')!r} "
                        f"role={inp.get_attribute('role')!r} "
                        f"visible={inp.is_visible()} "
                        f"value={inp.input_value()!r}"
                    )

                except Exception:
                    pass

            # ============================================================
            # ALL BUTTONS
            # ============================================================

            print()
            print("=" * 70)
            print("ALL BUTTONS AFTER LOCATION CLICK")
            print("=" * 70)

            buttons = page.get_by_role(
                "button"
            )

            print(
                "Total buttons:",
                buttons.count()
            )

            for i in range(buttons.count()):

                try:

                    button = buttons.nth(i)

                    if not button.is_visible():
                        continue

                    print(
                        f"[BUTTON {i}] "
                        f"text={button.inner_text(
                            timeout=1000
                        )!r} "
                        f"aria-label={button.get_attribute(
                            'aria-label'
                        )!r} "
                        f"title={button.get_attribute(
                            'title'
                        )!r} "
                        f"data-testid={button.get_attribute(
                            'data-testid'
                        )!r}"
                    )

                except Exception:
                    pass

            # ============================================================
            # ALL VISIBLE TEXT AROUND LOCATION
            # ============================================================

            print()
            print("=" * 70)
            print("VISIBLE PAGE TEXT AFTER LOCATION CLICK")
            print("=" * 70)

            text = page.locator(
                "body"
            ).inner_text()

            print(text)

            # ============================================================
            # ELEMENTS WITH LOCATION-RELATED ATTRIBUTES
            # ============================================================

            print()
            print("=" * 70)
            print("LOCATION-RELATED ELEMENTS")
            print("=" * 70)

            elements = page.locator(
                '[id*="location"], '
                '[name*="location"], '
                '[data-testid*="location"], '
                '[class*="location"]'
            )

            print(
                "Location-related elements:",
                elements.count()
            )

            for i in range(
                min(elements.count(), 100)
            ):

                try:

                    element = elements.nth(i)

                    if not element.is_visible():
                        continue

                    print(
                        f"[LOCATION {i}] "
                        f"tag={element.evaluate(
                            '(el) => el.tagName'
                        )} "
                        f"id={element.get_attribute('id')!r} "
                        f"name={element.get_attribute('name')!r} "
                        f"role={element.get_attribute('role')!r} "
                        f"testid={element.get_attribute(
                            'data-testid'
                        )!r} "
                        f"text={element.inner_text(
                            timeout=1000
                        )[:300]!r}"
                    )

                except Exception:
                    pass

            # ============================================================
            # DIALOGS / DRAWERS
            # ============================================================

            print()
            print("=" * 70)
            print("DIALOGS / DRAWERS")
            print("=" * 70)

            dialogs = page.locator(
                '[role="dialog"], '
                '[aria-modal="true"], '
                '[data-testid*="drawer"], '
                '[data-testid*="modal"], '
                '[data-testid*="slideout"]'
            )

            print(
                "Dialogs/drawers found:",
                dialogs.count()
            )

            for i in range(dialogs.count()):

                try:

                    dialog = dialogs.nth(i)

                    if not dialog.is_visible():
                        continue

                    print(
                        f"[DIALOG {i}] "
                        f"role={dialog.get_attribute('role')!r} "
                        f"testid={dialog.get_attribute(
                            'data-testid'
                        )!r}"
                    )

                    try:

                        print(
                            dialog.inner_text(
                                timeout=1000
                            )[:3000]
                        )

                    except Exception:
                        pass

                except Exception:
                    pass

            print()
            print("=" * 70)
            print("STAGE 7 INSPECTION COMPLETE")
            print("=" * 70)

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
                    path="wairau_stage7_error.png",
                    full_page=True
                )

                print(
                    "Saved: wairau_stage7_error.png"
                )

            except Exception:
                pass

        finally:

            browser.close()

            print()
            print("=" * 70)
            print("STAGE 7 FINISHED")
            print("=" * 70)


if __name__ == "__main__":
    main()
