import time
from playwright.sync_api import sync_playwright

PRODUCT_URL = (
    "https://www.jbhifi.co.nz/products/"
    "ps5-playstation-5-pro-2tb-console"
)


def main():

    print("=" * 70)
    print("JB HI-FI WAIRAU PS5 PRO TRACKER")
    print("STAGE 2 - CART / STORE INVESTIGATION")
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

            print()
            print("=" * 70)
            print("OPENING PRODUCT PAGE")
            print("=" * 70)

            response = page.goto(
                PRODUCT_URL,
                wait_until="domcontentloaded",
                timeout=60000
            )

            if response:
                print("HTTP status:", response.status)

            page.wait_for_timeout(5000)

            print("Page title:", page.title())
            print("URL:", page.url)

            print()
            print("=" * 70)
            print("CLICKING ADD TO CART")
            print("=" * 70)

            add_to_cart = page.get_by_role(
                "button",
                name="Add to cart",
                exact=False
            )

            count = add_to_cart.count()

            print("Add to cart buttons found:", count)

            if count == 0:

                print("NO ADD TO CART BUTTON FOUND.")

            else:

                print("Add to cart found.")

                if add_to_cart.first.is_visible():

                    print("Button is visible.")
                    print("Clicking...")

                    add_to_cart.first.click(
                        timeout=10000
                    )

                    print("Add to cart clicked.")

                    page.wait_for_timeout(5000)

                else:

                    print(
                        "Add to cart exists "
                        "but is not visible."
                    )

            print()
            print("=" * 70)
            print("CURRENT PAGE")
            print("=" * 70)

            print("URL:", page.url)
            print("TITLE:", page.title())

            print()
            print("=" * 70)
            print("FULL VISIBLE PAGE TEXT")
            print("=" * 70)

            text = page.locator(
                "body"
            ).inner_text()

            print(text)

            print()
            print("=" * 70)
            print("RELEVANT TEXT SEARCH")
            print("=" * 70)

            keywords = [
                "Wairau",
                "Wairau Park",
                "Getting your item",
                "pickup",
                "pick up",
                "click",
                "collect",
                "collection",
                "delivery",
                "cart",
                "review cart",
                "checkout",
                "available",
                "unavailable",
                "store"
            ]

            lower_text = text.lower()

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

            print()
            print("=" * 70)
            print("ALL BUTTONS")
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

            print()
            print("=" * 70)
            print("RELEVANT LINKS")
            print("=" * 70)

            links = page.get_by_role(
                "link"
            )

            link_count = links.count()

            print(
                "Number of links:",
                link_count
            )

            relevant_words = [
                "cart",
                "checkout",
                "store",
                "pickup",
                "collect",
                "wairau"
            ]

            for i in range(link_count):

                try:

                    link = links.nth(i)

                    name = link.inner_text(
                        timeout=1000
                    ).strip()

                    href = link.get_attribute(
                        "href"
                    )

                    combined = (
                        str(name)
                        + " "
                        + str(href)
                    ).lower()

                    if any(
                        word in combined
                        for word in relevant_words
                    ):

                        print(
                            f"[LINK {i}] "
                            f"{name} "
                            f"-> {href}"
                        )

                except Exception:

                    pass

            print()
            print("=" * 70)
            print("SCREENSHOT")
            print("=" * 70)

            page.screenshot(
                path="wairau_stage2.png",
                full_page=True
            )

            print(
                "Saved: wairau_stage2.png"
            )

            print()
            print("=" * 70)
            print("WAITING")
            print("=" * 70)

            time.sleep(3)

        except Exception as e:

            print()
            print("=" * 70)
            print("ERROR")
            print("=" * 70)

            print(repr(e))

            try:

                page.screenshot(
                    path="wairau_stage2_error.png",
                    full_page=True
                )

                print(
                    "Saved error screenshot."
                )

            except Exception:

                pass

        finally:

            browser.close()

            print()
            print("=" * 70)
            print("STAGE 2 FINISHED")
            print("=" * 70)


if __name__ == "__main__":
    main()
