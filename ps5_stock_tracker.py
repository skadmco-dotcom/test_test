import os
import json
import requests
from datetime import datetime, timezone
from zoneinfo import ZoneInfo


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

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)

NZ_TIMEZONE = ZoneInfo("Pacific/Auckland")


# ============================================================
# STATE
# ============================================================

def load_state():

    if not os.path.exists(STATE_FILE):
        return {}

    try:

        with open(
            STATE_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            return json.load(f)

    except Exception as e:

        print(
            f"Could not load state: {e}"
        )

        return {}


def save_state(state):

    with open(
        STATE_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            state,
            f,
            indent=2
        )


# ============================================================
# EMAIL
# ============================================================

def send_email(subject, body):

    if not RESEND_API_KEY:

        print(
            "ERROR: RESEND_API_KEY is not configured."
        )

        return False

    url = "https://api.resend.com/emails"

    payload = {

        "from":
            "PS5 Stock Tracker <onboarding@resend.dev>",

        "to":
            [TO_EMAIL],

        "subject":
            subject,

        "text":
            body,
    }

    headers = {

        "Authorization":
            f"Bearer {RESEND_API_KEY}",

        "Content-Type":
            "application/json",
    }

    try:

        response = requests.post(

            url,

            headers=headers,

            json=payload,

            timeout=30,
        )

        print(
            "Email response:",
            response.status_code
        )

        print(
            response.text
        )

        return response.ok

    except Exception as e:

        print(
            "Email error:",
            e
        )

        return False


# ============================================================
# TEST EMAIL
# ============================================================

def send_test_email():

    subject = (
        "PS5 Pro Tracker - Test Email"
    )

    body = """Your PS5 Pro tracker is working.

The tracker is currently monitoring:

JB Hi-Fi NZ
PS5 Pro 2TB Console

It will:

- Check the listing every hour
- Alert you if the listing returns
- Send a nightly update at 7:00 PM Auckland time

Time:
"""

    body += datetime.now(
        NZ_TIMEZONE
    ).strftime(
        "%Y-%m-%d %H:%M:%S NZST/NZDT"
    )

    return send_email(
        subject,
        body
    )


# ============================================================
# JB HI-FI LISTING CHECK
# ============================================================

def check_jbhifi_listing():

    print()
    print("=" * 60)
    print("CHECKING JB HI-FI PS5 PRO LISTING")
    print("=" * 60)

    result = {

        "status":
            "unknown",

        "listing_present":
            False,

        "reason":
            "",
    }

    try:

        response = requests.get(

            JB_HIFI_URL,

            headers={

                "User-Agent":
                    USER_AGENT,

                "Accept-Language":
                    "en-NZ,en;q=0.9",
            },

            timeout=30,
        )

        print(
            "HTTP status:",
            response.status_code
        )

        if response.status_code != 200:

            result["reason"] = (
                f"HTTP {response.status_code}"
            )

            print(
                "RESULT: UNKNOWN"
            )

            return result

        text = response.text.lower()

        print(
            f"Downloaded {len(response.text):,} "
            "characters."
        )

        # ----------------------------------------------------
        # CHECK FOR PS5 PRO
        # ----------------------------------------------------

        product_indicators = [

            "playstation 5 pro",

            "ps5 pro",

            "ps5-playstation-5-pro",
        ]

        product_found = False

        for indicator in product_indicators:

            if indicator in text:

                product_found = True

                print(
                    f"Found product indicator: "
                    f"{indicator}"
                )

                break

        # ----------------------------------------------------
        # CHECK FOR REMOVAL
        # ----------------------------------------------------

        removed_indicators = [

            "page not found",

            "product not found",

            "page you are looking for",

            "sorry, this page",

            "we can't find",

            "couldn't find",

            "does not exist",
        ]

        removed = False

        for indicator in removed_indicators:

            if indicator in text:

                removed = True

                print(
                    f"Found removal indicator: "
                    f"{indicator}"
                )

                break

        # ----------------------------------------------------
        # DETERMINE STATUS
        # ----------------------------------------------------

        if removed or not product_found:

            result["status"] = "gone"

            result["listing_present"] = False

            result["reason"] = (
                "PS5 Pro listing is not currently "
                "detected on JB Hi-Fi"
            )

            print(
                "RESULT: LISTING GONE"
            )

            return result

        # ----------------------------------------------------
        # LISTING FOUND
        # ----------------------------------------------------

        result["status"] = "present"

        result["listing_present"] = True

        result["reason"] = (
            "PS5 Pro product listing detected "
            "on JB Hi-Fi"
        )

        print(
            "RESULT: LISTING IS BACK!"
        )

        return result

    except Exception as e:

        result["status"] = "unknown"

        result["listing_present"] = False

        result["reason"] = (
            f"Error checking JB Hi-Fi: {e}"
        )

        print(
            "RESULT: UNKNOWN"
        )

        print(
            result["reason"]
        )

        return result


# ============================================================
# LISTING RETURN EMAIL
# ============================================================

def send_listing_return_email():

    subject = (
        "🚨 PS5 PRO LISTING IS BACK ON JB HI-FI!"
    )

    body = """🚨 PS5 PRO LISTING IS BACK!

JB Hi-Fi's PS5 Pro listing has returned.

The product page is now detecting the PS5 Pro again.

Product:
PS5 PlayStation 5 Pro 2TB Console

JB Hi-Fi:
https://www.jbhifi.co.nz/products/ps5-playstation-5-pro-2tb-console

IMPORTANT:
This alert means the product listing has returned.
It does NOT necessarily mean Wairau Park has stock.

Check JB Hi-Fi immediately.

The tracker will continue checking every hour.

Time:
"""

    body += datetime.now(
        NZ_TIMEZONE
    ).strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    return send_email(
        subject,
        body
    )


# ============================================================
# NIGHTLY UPDATE EMAIL
# ============================================================

def send_nightly_email():

    subject = (
        "PS5 Pro Daily Update - Still No Stock"
    )

    body = """PS5 Pro Daily Stock Update

There is still no PS5 Pro listing available
on JB Hi-Fi NZ.

The tracker checked JB Hi-Fi today and the
PS5 Pro listing is still unavailable.

The tracker will continue checking every hour.

If the listing returns, you will receive a
separate alert immediately.

JB Hi-Fi:
https://www.jbhifi.co.nz/products/ps5-playstation-5-pro-2tb-console

Checked:
"""

    body += datetime.now(
        NZ_TIMEZONE
    ).strftime(
        "%A, %d %B %Y at %I:%M %p"
    )

    body += " Auckland time."

    return send_email(
        subject,
        body
    )


# ============================================================
# NIGHTLY EMAIL CHECK
# ============================================================

def should_send_nightly_email(
    current_status,
    state
):

    now_nz = datetime.now(
        NZ_TIMEZONE
    )

    print()
    print(
        "Current Auckland time:",
        now_nz.strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    )

    # Only send at 7 PM Auckland time.
    if now_nz.hour != 19:

        return False

    # Only send if the listing is still gone.
    if current_status != "gone":

        print(
            "It is 7 PM, but the listing is "
            "already back."
        )

        return False

    today = now_nz.strftime(
        "%Y-%m-%d"
    )

    last_nightly_email = state.get(
        "last_nightly_email",
        ""
    )

    # Prevent duplicate emails on the same day.
    if last_nightly_email == today:

        print(
            "Nightly email already sent today."
        )

        return False

    return True


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)

    print(
        "PS5 PRO JB HI-FI LISTING TRACKER"
    )

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
        print(
            "TEST MODE ENABLED"
        )

        print(
            "Sending test email..."
        )

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
    # LOAD STATE
    # ========================================================

    previous_state = load_state()

    previous_jb = previous_state.get(
        "JB Hi-Fi",
        {}
    )

    previous_status = previous_jb.get(
        "status",
        "gone"
    )

    print()
    print(
        "Previous JB Hi-Fi status:",
        previous_status
    )

    # ========================================================
    # CHECK CURRENT LISTING
    # ========================================================

    current_result = (
        check_jbhifi_listing()
    )

    current_status = (
        current_result["status"]
    )

    print()
    print("=" * 60)
    print("LISTING STATUS")
    print("=" * 60)

    print(
        "Previous:",
        previous_status
    )

    print(
        "Current:",
        current_status
    )

    print(
        "Reason:",
        current_result["reason"]
    )

    # ========================================================
    # LISTING RETURNED
    # ========================================================

    listing_returned = (

        current_status == "present"

        and

        previous_status == "gone"
    )

    if listing_returned:

        print()
        print(
            "🚨 PS5 PRO LISTING HAS RETURNED!"
        )

        print(
            "Sending alert email..."
        )

        if send_listing_return_email():

            print(
                "Listing return email sent."
            )

        else:

            print(
                "Listing return email failed."
            )

    # ========================================================
    # NIGHTLY 7 PM EMAIL
    # ========================================================

    if should_send_nightly_email(
        current_status,
        previous_state
    ):

        print()
        print(
            "🌙 7 PM NIGHTLY UPDATE"
        )

        print(
            "Sending nightly no-stock email..."
        )

        if send_nightly_email():

            print(
                "Nightly email sent successfully."
            )

            # Record that today's email was sent.
            now_nz = datetime.now(
                NZ_TIMEZONE
            )

            previous_state[
                "last_nightly_email"
            ] = now_nz.strftime(
                "%Y-%m-%d"
            )

        else:

            print(
                "Nightly email failed."
            )

    # ========================================================
    # SAVE STATE
    # ========================================================

    if current_status == "unknown":

        print()
        print(
            "Current result is UNKNOWN."
        )

        print(
            "Keeping previous listing state."
        )

        new_state = previous_state

    else:

        new_state = {

            "JB Hi-Fi": {

                "status":
                    current_result["status"],

                "listing_present":
                    current_result[
                        "listing_present"
                    ],

                "reason":
                    current_result["reason"],
            },

            "last_nightly_email":
                previous_state.get(
                    "last_nightly_email",
                    ""
                ),
        }

    save_state(
        new_state
    )

    print()
    print(
        "State saved."
    )

    print()
    print("=" * 60)

    print(
        "TRACKER FINISHED"
    )

    print("=" * 60)


if __name__ == "__main__":

    main()
