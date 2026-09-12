import time
from playwright.sync_api import sync_playwright

PRODUCT_URL = (
    "https://www.jbhifi.co.nz/products/"
    "ps5-playstation-5-pro-2tb-console"
)


def main():

    print("=" * 60)
    print("JB HI-FI WAIRAU PS5 PRO TRACKER")
    print("STAGE 1 - PRODUCT PAGE / ADD TO CART")
    print("=" * 60)

    with sync_playwright() as p:

        print()
        print("Launching Chromium...")

        browser = p.chromium.launch(
            headless=True
        )

        page = browser.new_page(
            viewport={
                "width": 1440,
                "height": 1000
            },
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            )
        )

        try:

            print()
            print("=" * 60)
            print("OPENING JB HI-FI PS5 PRO PAGE")
            print("=" * 60)

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
            else:
                print(
                    "HTTP status: unknown"
                )

            # Give the page time to finish loading
            page.wait_for_timeout(5000)

            print(
                "Page title:",
                page.title()
            )

            print(
                "Current URL:",
                page.url
            )

            print()
            print(
                "Taking initial screenshot..."
            )

            page.screenshot(
                path="wairau_stage1.png",
                full_page=True
            )

            print(
                "Screenshot saved:"
            )

            print(
                "wairau_stage1.png"
            )

            print()
            print("=" * 60)
            print("CHECKING PAGE CONTENT")
            print("=" * 60)

            text = page.locator(
                "body"
            ).inner_text()

            print(
                f"Downloaded page text: "
                f"{len(text):,} characters"
            )

            if "PS5 Pro" in text:
                print(
                    "✓ PS5 Pro text found"
                )

            elif "PS5 PRO" in text:
                print(
                    "✓ PS5 PRO text found"
                )

            else:
                print(
                    "✗ PS5 Pro text NOT found"
                )

            if "Getting your item" in text:
                print(
                    "✓ 'Getting your item' found"
                )

            else:
                print(
                    "✗ 'Getting your item' "
                    "not currently visible"
                )

            print()
            print("=" * 60)
            print("BUTTONS FOUND ON PAGE")
            print("=" * 60)

            buttons = page.get_by_role(
                "button"
            )

            button_count = buttons.count()

            print(
                f"Found {button_count} buttons."
            )

            for i in range(button_count):

                try:

                    button = buttons.nth(i)

                    name = button.inner_text(
                        timeout=1000
                    ).strip()

                    if name:

                        print(
                            f"Button {i}: "
                            f"{name}"
                        )

                except Exception:

                    pass

            print()
            print("=" * 60)
            print("LOOKING FOR ADD TO CART")
            print("=" * 60)

            add_to_cart = page.get_by_role(
                "button",
                name="Add to cart",
                exact=False
            )

            add_count = add_to_cart.count()

            print(
                f"Add to cart matches: "
                f"{add_count}"
            )

            if add_count > 0:

                print()
                print(
                    "✓ Add to cart button found."
                )

                try:

                    visible = (
                        add_to_cart.first.is_visible()
                    )

                except Exception:

                    visible = False

                print(
                    "Visible:",
                    visible
                )

                if visible:

                    print()
                    print(
                        "Clicking Add to cart..."
                    )

                    add_to_cart.first.click(
                        timeout=10000
                    )

                    print(
                        "✓ Add to cart clicked."
                    )

                    page.wait_for_timeout(
                        5000
                    )

                    print(
                        "Current URL after click:"
                    )

                    print(
                        page.url
                    )

                else:

                    print(
                        "✗ Add to cart exists "
                        "but is not visible."
                    )

            else:

                print()
                print(
                    "✗ Add to cart button "
                    "was not found."
                )

            print()
            print("=" * 60)
            print("TAKING POST-CLICK SCREENSHOT")
            print("=" * 60)

            page.screenshot(
                path="wairau_stage1_after.png",
                full_page=True
            )

            print(
                "Screenshot saved:"
            )

            print(
                "wairau_stage1_after.png"
            )

            print()
            print("=" * 60)
            print("CHECKING PAGE AFTER CART ACTION")
            print("=" * 60)

            after_text = page.locator(
                "body"
            ).inner_text()

            if "Getting your item" in after_text:

                print(
                    "✓ 'Getting your item' "
                    "is visible after cart action."
                )

            else:

                print(
                    "'Getting your item' "
                    "is not visible after cart action."
                )

            print()
            print(
                "Looking for cart links/buttons..."
            )

            links = page.get_by_role(
                "link"
            )

            link_count = links.count()

            print(
                f"Found {link_count} links."
            )

            for i in range(
                min(link_count, 100)
            ):

                try:

                    link = links.nth(i)

                    name = link.inner_text(
                        timeout=1000
                    ).strip()

                    href = link.get_attribute(
                        "href"
                    )

                    if (
                        name
                        and (
                            "cart" in name.lower()
                            or "cart" in str(href).lower()
                        )
                    ):

                        print(
                            f"Cart link {i}: "
                            f"{name} "
                            f"-> {href}"
                        )

                except Exception:

                    pass

            print()
            print(
                "Waiting briefly before closing..."
            )

            time.sleep(3)

        except Exception as e:

            print()
            print("=" * 60)
            print("ERROR")
            print("=" * 60)

            print(
                repr(e)
            )

            try:

                page.screenshot(
                    path="wairau_stage1_error.png",
                    full_page=True
                )

                print(
                    "Error screenshot saved:"
                )

                print(
                    "wairau_stage1_error.png"
                )

            except Exception:

                print(
                    "Could not save error screenshot."
                )

        finally:

            browser.close()

            print()
            print("=" * 60)
            print("BROWSER CLOSED")
            print("=" * 60)

            print(
                "STAGE 1 FINISHED"
            )

            print("=" * 60)


if __name__ == "__main__":
    main()
