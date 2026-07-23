# Petina BSR Tracker

Tracks Amazon Best Sellers Rank for ASIN `B0DPVRRK77` on amazon.co.uk and
logs it to `bsr_history.csv` each time it runs.

## 1. Setup (one-time)

```bash
pip install requests beautifulsoup4
```

## 2. Test it manually

```bash
python3 track_bsr.py
```

You should see output like:

```
Checking B0DPVRRK77...
  #1,234 in Pet Supplies
  #3 in Dog Waste Bags

History saved to: /path/to/petina-bsr-tracker/bsr_history.csv
```

If it prints "No BSR found", Amazon has either changed its page layout
(the parsing regex will need a tweak) or blocked/CAPTCHA'd the request —
see **Notes** below.

## 3. Schedule it to run daily

### Option A: GitHub Actions (recommended if hosting on GitHub)

This repo includes `.github/workflows/track-bsr.yml`, which:

- Runs once a day at 09:00 UTC (edit the `cron:` line to change the time)
- Can also be triggered manually from the **Actions** tab → "Track Amazon BSR" → **Run workflow**
- Installs dependencies, runs `track_bsr.py`, then commits the updated `bsr_history.csv` back to the repo

To use it:

1. Push this folder to a new GitHub repo (see below)
2. Go to the repo's **Settings → Actions → General → Workflow permissions**
   and make sure "Read and write permissions" is selected (needed so the
   workflow can commit the CSV back)
3. That's it — it'll run on schedule, and each run's commit gives you a
   visible history of when checks happened alongside the CSV data itself

```bash
cd petina-bsr-tracker
git init
git add .
git commit -m "Initial BSR tracker"
git branch -M main
git remote add origin https://github.com/<your-username>/<repo-name>.git
git push -u origin main
```

**A caution specific to GitHub Actions:** runs execute from GitHub's shared
runner IP ranges, which Amazon is more likely to flag/rate-limit than a
residential IP, since many unrelated jobs share those ranges. If you start
seeing "No BSR found" consistently once it's on Actions but it worked fine
locally, that's the likely cause — the options below (cron/Task Scheduler)
run from your own machine's IP instead.

### Option B: Run it yourself locally

**Mac/Linux (cron):**

```bash
crontab -e
```

Add a line to run it once a day at 9am:

```
0 9 * * * cd /full/path/to/petina-bsr-tracker && /usr/bin/python3 track_bsr.py >> run.log 2>&1
```

**Windows (Task Scheduler):**

1. Open Task Scheduler → Create Basic Task
2. Trigger: Daily, pick a time
3. Action: Start a program
   - Program: `python`
   - Arguments: `track_bsr.py`
   - Start in: the full path to the `petina-bsr-tracker` folder

## 4. Adding more products later

Edit the `ASINS` list at the top of `track_bsr.py`:

```python
ASINS = [
    "B0DPVRRK77",
    "ANOTHER_ASIN_HERE",
]
```

## Notes / limitations

- **Amazon's Terms of Service prohibit automated scraping.** This script
  is intended for low-frequency (e.g. once daily), personal tracking of
  your own listing. Running it more often, or at scale, increases the
  chance Amazon blocks your IP or serves a CAPTCHA.
- **Page structure changes.** Amazon periodically changes its HTML, which
  can break the BSR-parsing regex. If the script starts returning "No BSR
  found," check the saved page HTML against the current parsing logic in
  `parse_bsr()`.
- **No JavaScript rendering.** The script only fetches raw HTML — if
  Amazon starts loading the BSR section via JavaScript, this approach
  would need Selenium/Playwright instead of `requests`.
- **A more robust alternative**: if you have Amazon Seller Central access,
  the official **Selling Partner API (SP-API)** exposes sales rank and
  other listing data without scraping risk. Worth considering if you want
  something more durable long-term.
- I wasn't able to test this against the live Amazon page from this
  environment (network access here is restricted), so please run the
  manual test in step 2 before relying on the scheduled version — the
  regex may need a small adjustment based on what Amazon actually returns
  for this listing.
