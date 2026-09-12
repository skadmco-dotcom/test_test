import time
from playwright.sync_api import sync_playwright

PRODUCT_URL = (
    "https://www.jbhifi.co.nz/products/"
    "ps5-playstation-5-pro-2tb-console"
)


def main():

    print("=" * 70)
    print("JB HI-FI WAIRAU PS5 PRO TRACKER")
    print("STAGE 8 - TYPE WAIRAU PARK")
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

            # --------------------------------------------------
            # OPEN PRODUCT
            # --------------------------------------------------

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

            # --------------------------------------------------
            # ADD TO CART
            # --------------------------------------------------

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

            # --------------------------------------------------
            # CLOSE CART
            # --------------------------------------------------

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

            # --------------------------------------------------
            # LOCATION FIELD
            # --------------------------------------------------

            print()
            print("=" * 70)
            print("ENTERING WAIRAU PARK")
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

            # Type the location slowly so the website's
            # autocomplete has time to react.
            location_input.first.fill(
                "Wairau Park"
            )

            print(
                "✓ Typed: Wairau Park"
            )

            page.wait_for_timeout(4000)

            # --------------------------------------------------
            # SCREENSHOT
            # --------------------------------------------------

            page.screenshot(
                path="wairau_stage8_suggestions.png",
                full_page=True
            )

            print(
                "Saved: wairau_stage8_suggestions.png"
            )

            # --------------------------------------------------
            # INPUTS
            # --------------------------------------------------

            print()
            print("=" * 70)
            print("INPUTS AFTER TYPING WAIRAU PARK")
            print("=" * 70)

            inputs = page.locator("input")

            print(
                "Total inputs:",
                inputs.count()
            )

            for i in range(inputs.count()):

                try:

                    inp = inputs.nth(i)

                    if not inp.is_visible():
                        continue

                    print(
                        f"[INPUT {i}] "
                        f"name={inp.get_attribute('name')!r} "
                        f"id={inp.get_attribute('id')!r} "
                        f"type={inp.get_attribute('type')!r} "
                        f"placeholder={inp.get_attribute('placeholder')!r} "
                        f"role={inp.get_attribute('role')!r} "
                        f"value={inp.input_value()!r}"
                    )

                except Exception:
                    pass

            # --------------------------------------------------
            # VISIBLE BUTTONS
            # --------------------------------------------------

            print()
            print("=" * 70)
            print("VISIBLE BUTTONS")
            print("=" * 70)

            buttons = page.get_by_role(
                "button"
            )

            for i in range(buttons.count()):

                try:

                    button = buttons.nth(i)

                    if not button.is_visible():
                        continue

                    text = button.inner_text(
                        timeout=1000
                    ).strip()

                    aria = button.get_attribute(
                        "aria-label"
                    )

                    testid = button.get_attribute(
                        "data-testid"
                    )

                    # Only print potentially useful buttons.
                    if (
                        text
                        or aria
                        or testid
                    ):
                        print(
                            f"[BUTTON {i}] "
                            f"text={text!r} "
                            f"aria-label={aria!r} "
                            f"data-testid={testid!r}"
                        )

                except Exception:
                    pass

            # --------------------------------------------------
            # VISIBLE LISTS / OPTIONS
            # --------------------------------------------------

            print()
            print("=" * 70)
            print("VISIBLE OPTIONS / SUGGESTIONS")
            print("=" * 70)

            option_selectors = [
                '[role="option"]',
                '[role="listbox"]',
                '[role="menu"]',
                'li',
                '[data-testid*="suggest"]',
                '[data-testid*="location"]'
            ]

            seen = set()

            for selector in option_selectors:

                elements = page.locator(
                    selector
                )

                for i in range(
                    min(elements.count(), 100)
                ):

                    try:

                        element = elements.nth(i)

                        if not element.is_visible():
                            continue

                        text = element.inner_text(
                            timeout=1000
                        ).strip()

                        if not text:
                            continue

                        key = (
                            selector,
                            text[:500]
                        )

                        if key in seen:
                            continue

                        seen.add(key)

                        print(
                            f"[{selector}] "
                            f"{text[:500]!r}"
                        )

                    except Exception:
                        pass

            # --------------------------------------------------
            # PAGE TEXT
            # --------------------------------------------------

            print()
            print("=" * 70)
            print("PAGE TEXT AROUND LOCATION")
            print("=" * 70)

            body_text = page.locator(
                "body"
            ).inner_text()

            lines = body_text.splitlines()

            for i, line in enumerate(lines):

                if "wairau" in line.lower():
                    start = max(0, i - 5)
                    end = min(
                        len(lines),
                        i + 10
                    )

                    print(
                        "\n".join(
                            lines[start:end]
                        )
                    )

            print()
            print("=" * 70)
            print("STAGE 8 COMPLETE")
            print("=" * 70)

            time.sleep(3)

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
                    path="wairau_stage8_error.png",
                    full_page=True
                )

                print(
                    "Saved: wairau_stage8_error.png"
                )

            except Exception:
                pass

        finally:

            browser.close()

            print()
            print("=" * 70)
            print("STAGE 8 FINISHED")
            print("=" * 70)


if __name__ == "__main__":
    main()
