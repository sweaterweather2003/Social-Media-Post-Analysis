# backend/scraper.py
import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

APIFY_TOKEN = os.getenv("APIFY_TOKEN")
ACTOR_ID = "apify/instagram-scraper"  # Using the same actor as your working bot
BASE_URL = "https://api.apify.com/v2"


def start_run(direct_urls: list, results_limit: int = 20) -> str:
    """Start Apify run"""
    url = f"{BASE_URL}/acts/{ACTOR_ID}/runs?token={APIFY_TOKEN}"
    payload = {
        "directUrls": direct_urls,
        "resultsLimit": results_limit,
        "resultsType": "posts"
    }
    response = requests.post(url, json=payload)
    response.raise_for_status()
    run_id = response.json()["data"]["id"]
    return run_id


def wait_for_completion(run_id: str, poll_interval: int = 5, timeout: int = 180) -> bool:
    """Wait for run to finish"""
    status_url = f"{BASE_URL}/actor-runs/{run_id}?token={APIFY_TOKEN}"
    elapsed = 0

    while elapsed < timeout:
        resp = requests.get(status_url)
        resp.raise_for_status()
        status = resp.json()["data"]["status"]

        if status == "SUCCEEDED":
            print("✅ Apify run completed successfully")
            return True
        if status in ("FAILED", "ABORTED", "TIMED-OUT"):
            raise RuntimeError(f"Apify run failed with status: {status}")

        print(f"⏳ Apify run status: {status}... waiting")
        time.sleep(poll_interval)
        elapsed += poll_interval

    raise TimeoutError("Apify run timed out")


def fetch_results(run_id: str) -> list:
    """Get results from dataset"""
    dataset_url = f"{BASE_URL}/actor-runs/{run_id}/dataset/items?token={APIFY_TOKEN}"
    resp = requests.get(dataset_url)
    resp.raise_for_status()
    return resp.json()


def scrape_posts(urls_or_shortcodes: list) -> list:
    """Main function - same as your working bot"""
    # Convert shortcodes to full URLs
    direct_urls = []
    for item in urls_or_shortcodes:
        if item.startswith("http"):
            direct_urls.append(item)
        else:
            direct_urls.append(f"https://www.instagram.com/p/{item.strip()}/")

    run_id = start_run(direct_urls, results_limit=30)
    print(f"🚀 Apify run started: {run_id}")

    wait_for_completion(run_id)
    results = fetch_results(run_id)

    print(f"📦 Retrieved {len(results)} items from Apify")
    return results
