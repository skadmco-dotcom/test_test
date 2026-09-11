import os
import requests

print("Python script started")

api_key = os.getenv("RESEND_API_KEY")

print("RESEND_API_KEY exists:", bool(api_key))

if not api_key:
    raise RuntimeError("RESEND_API_KEY is missing!")

print("Sending test email...")

response = requests.post(
    "https://api.resend.com/emails",
    headers={
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    },
    json={
        "from": "onboarding@resend.dev",
        "to": ["skadmco@gmail.com"],
        "subject": "PS5 Tracker Test",
        "html": "<h1>PS5 tracker test successful!</h1><p>Your GitHub Actions email system is working.</p>",
    },
)

print("Resend status:", response.status_code)
print("Resend response:", response.text)

response.raise_for_status()

print("EMAIL SENT SUCCESSFULLY")
