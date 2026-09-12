import time
from playwright.sync_api import sync_playwright

PRODUCT_URL = (
    "https://www.jbhifi.co.nz/products/"
    "ps5-playstation-5-pro-2tb-console"
)

Wairau_SEARCH = "Wairau Park"


def main():

    print("=" * 70)
    print("JB HI-FI WAIRAU PS5 PRO TRACKER")
    print("STAGE 3 - FIND WAIRAU PARK")
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

            print(
                "Page title:",
                page.title()
            )

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

            if add_buttons.count() == 0:
                print(
                    "ERROR: Add to cart not found."
                )
                return

            add_buttons.first.click(
                timeout=10000
            )

            print(
                "✓ PS5 Pro added to cart."
            )

            # Wait for cart drawer / modal
            page.wait_for_timeout(3000)

            # --------------------------------------------------
            # FIND POSTCODE / SUBURB FIELD
            # --------------------------------------------------

            print()
            print("=" * 70)
            print("LOOKING FOR POSTCODE / SUBURB FIELD")
            print("=" * 70)

            inputs = page.locator(
                "input"
            )

            input_count = inputs.count()

            print(
                "Inputs found:",
                input_count
            )

            for i in range(input_count):

                try:

                    inp = inputs.nth(i)

                    placeholder = (
                        inp.get_attribute(
                            "placeholder"
                        )
                    )

                    aria = (
                        inp.get_attribute(
                            "aria-label"
                        )
                    )

                    name = (
                        inp.get_attribute(
                            "name"
                        )
                    )

                    value = (
                        inp.get_attribute(
                            "value"
                        )
                    )

                    print(
                        f"INPUT {i}: "
                        f"placeholder={placeholder!r} "
                        f"aria={aria!r} "
                        f"name={name!r} "
                        f"value={value!r}"
                    )

                except Exception:

                    pass

            # --------------------------------------------------
            # FIND SEARCH FIELD
            # --------------------------------------------------

            search_input = None

            for i in range(input_count):

                try:

                    inp = inputs.nth(i)

                    placeholder = (
                        inp.get_attribute(
                            "placeholder"
                        )
                        or ""
                    ).lower()

                    aria = (
                        inp.get_attribute(
                            "aria-label"
                        )
                        or ""
                    ).lower()

                    name = (
                        inp.get_attribute(
                            "name"
                        )
                        or ""
                    ).lower()

                    combined = (
                        placeholder
                        + " "
                        + aria
                        + " "
                        + name
                    )

                    if (
                        "postcode" in combined
                        or "suburb" in combined
                    ):

                        search_input = inp

                        print(
                            "✓ Found location input:"
                        )

                        print(
                            "placeholder:",
                            placeholder
                        )

                        print(
                            "aria-label:",
                            aria
                        )

                        break

                except Exception:

                    pass

            if search_input is None:

                print()
                print(
                    "✗ Could not automatically "
                    "identify the location field."
                )

            else:

                # --------------------------------------------------
                # ENTER WAIRAU PARK
                # --------------------------------------------------

                print()
                print("=" * 70)
                print("ENTERING WAIRAU PARK")
                print("=" * 70)

                search_input.fill(
                    Wairau_SEARCH
                )

                print(
                    "Entered:",
                    Wairau_SEARCH
                )

                page.wait_for_timeout(
                    3000
                )

                # --------------------------------------------------
                # PRINT AUTOCOMPLETE OPTIONS
                # --------------------------------------------------

                print()
                print("=" * 70)
                print("CHECKING LOCATION OPTIONS")
                print("=" * 70)

                body_text = page.locator(
                    "body"
                ).inner_text()

                print(
                    body_text
                )

                # --------------------------------------------------
                # LOOK FOR WAIRAU PARK
                # --------------------------------------------------

                if "Wairau Park" in body_text:

                    print()
                    print(
                        "✓ WAIRAU PARK FOUND "
                        "IN PAGE CONTENT."
                    )

                    print()
                    print(
                        "Looking for clickable "
                        "Wairau Park option..."
                    )

                    candidates = page.get_by_text(
                        "Wairau Park",
                        exact=False
                    )

                    candidate_count = (
                        candidates.count()
                    )

                    print(
                        "Wairau candidates:",
                        candidate_count
                    )

                    for i in range(
                        candidate_count
                    ):

                        try:

                            candidate = (
                                candidates.nth(i)
                            )

                            print(
                                f"Candidate {i}:",
                                candidate.inner_text(
                                    timeout=1000
                                )
                            )

                            print(
                                "Visible:",
                                candidate.is_visible()
                            )

                        except Exception:

                            pass

                else:

                    print()
                    print(
                        "✗ Wairau Park was "
                        "not found in page content."
                    )

            # --------------------------------------------------
            # SCREENSHOT
            # --------------------------------------------------

            print()
            print("=" * 70)
            print("SAVING STAGE 3 SCREENSHOT")
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
                "Keeping browser open briefly..."
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
                    "Saved: "
                    "wairau_stage3_error.png"
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
