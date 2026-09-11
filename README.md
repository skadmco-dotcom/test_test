# PS5 Pro Stock Tracker — NZ

Checks these four stores once per hour:

- JB Hi-Fi NZ
- Noel Leeming
- Harvey Norman NZ
- The Warehouse

Sends an email to `skadmco@gmail.com` when PS5 Pro stock is detected.

## Free cloud setup

This version uses GitHub Actions. A public GitHub repository can run standard GitHub-hosted Actions runners for free.

### 1. Create a GitHub repository

Create a new **public** repository, for example:

`ps5-pro-stock-tracker`

Do not put your Resend API key in the code.

### 2. Upload these files

Upload:

- `ps5_stock_tracker.py`
- `.github/workflows/stock-check.yml`

### 3. Create a free Resend account

Create an account at https://resend.com/ using `skadmco@gmail.com`.

Resend currently has a free transactional-email tier. For this setup, the account email should be the same address receiving the alerts.

Create an API key.

### 4. Add the API key to GitHub

Go to:

Repository → Settings → Secrets and variables → Actions → New repository secret

Name:

`RESEND_API_KEY`

Value:

your Resend API key.

### 5. TEST IT BEFORE WAITING FOR STOCK

Go to:

Actions → PS5 Pro Stock Checker → Run workflow

Leave `test_email` set to `true`.

The workflow should run immediately and send:

`🧪 PS5 Pro Stock Tracker — TEST EMAIL`

to:

`skadmco@gmail.com`

Check your Inbox and Spam/Junk folder.

### 6. Turn normal monitoring on

The scheduled workflow automatically runs once every hour.

You don't need to leave your Mac or PC switched on.

## Important

Retail websites sometimes change their page structure or use JavaScript/anti-bot protection. If one store starts reporting `Check failed`, the store-specific detector may need updating.

The tracker deliberately does NOT buy anything automatically. It only emails you so you can decide whether to purchase.

GitHub Actions schedules run in UTC unless a timezone is specified. This workflow uses `10 * * * *`, so it runs at 10 minutes past every UTC hour. This is still hourly; the exact NZ clock time shifts with daylight saving. 
