#!/usr/bin/env python3
"""
track_bsr.py

Tracks Amazon Best Sellers Rank (BSR) for one or more ASINs on amazon.co.uk
and appends the result to a CSV history file.

Usage:
    python3 track_bsr.py

Configure the ASINs to track in the ASINS list below.
"""

import csv
import os
import re
import sys
import time
import random
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

ASINS = [
    "B0DPVRRK77",
]

MARKETPLACE = "amazon.co.uk"
BASE_URL = f"https://www.{MARKETPLACE}/dp/{{asin}}"

HISTORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bsr_history.csv")

# Rotate a couple of realistic desktop user agents to look less bot-like.
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
]

REQUEST_TIMEOUT = 15  # seconds
MIN_DELAY_BETWEEN_REQUESTS = 3  # seconds, only matters if tracking multiple ASINs


# ---------------------------------------------------------------------------
# Scraping logic
# ---------------------------------------------------------------------------

def fetch_product_page(asin: str) -> str:
    """Fetch the raw HTML for a product page."""
    url = BASE_URL.format(asin=asin)
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept-Language": "en-GB,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    }
    response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    return response.text


def parse_bsr(html: str):
    """
    Extract Best Sellers Rank entries from product page HTML.

    Returns a list of dicts like:
        [{"category": "Pet Supplies", "rank": 1234},
         {"category": "Dog Waste Bags", "rank": 3}]

    Amazon usually lists an overall rank plus one or more sub-category ranks,
    e.g. "#1,234 in Pet Supplies (See Top 100) #3 in Dog Waste Bags"
    """
    soup = BeautifulSoup(html, "html.parser")

    # BSR usually lives in the product details / additional information
    # section. Amazon's markup changes fairly often, so we search broadly
    # for any text block containing "Best Sellers Rank".
    candidates = soup.find_all(string=re.compile(r"Best Sellers Rank", re.I))

    ranks = []
    seen = set()

    for node in candidates:
        # Look at the parent container's full text, which usually includes
        # the rank numbers and category names right after the label.
        container = node.find_parent(["tr", "li", "div", "span"]) or node.parent
        text = container.get_text(" ", strip=True) if container else str(node)

        # Matches things like "#1,234 in Pet Supplies" or "#3 in Dog Waste Bags"
        for match in re.finditer(r"#([\d,]+)\s+in\s+([A-Za-z0-9 &\-']+?)(?=(?:\s*\(|\s*#|$))", text):
            rank = int(match.group(1).replace(",", ""))
            category = match.group(2).strip()
            key = (rank, category.lower())
            if key not in seen:
                seen.add(key)
                ranks.append({"category": category, "rank": rank})

    return ranks


def append_to_history(asin: str, ranks, error: str = None):
    file_exists = os.path.isfile(HISTORY_FILE)
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")

    with open(HISTORY_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["timestamp_utc", "asin", "category", "rank", "error"])

        if error:
            writer.writerow([timestamp, asin, "", "", error])
        elif ranks:
            for r in ranks:
                writer.writerow([timestamp, asin, r["category"], r["rank"], ""])
        else:
            writer.writerow([timestamp, asin, "", "", "No BSR found (page structure may have changed)"])


def track_all():
    for i, asin in enumerate(ASINS):
        if i > 0:
            time.sleep(MIN_DELAY_BETWEEN_REQUESTS)

        print(f"Checking {asin}...")
        try:
            html = fetch_product_page(asin)
            ranks = parse_bsr(html)
            if ranks:
                for r in ranks:
                    print(f"  #{r['rank']:,} in {r['category']}")
            else:
                print("  No BSR found — Amazon may have changed its page layout, "
                      "or the request may have been blocked/CAPTCHA'd.")
            append_to_history(asin, ranks)
        except requests.RequestException as e:
            print(f"  Request failed: {e}")
            append_to_history(asin, [], error=str(e))


if __name__ == "__main__":
    track_all()
    print(f"\nHistory saved to: {HISTORY_FILE}")
