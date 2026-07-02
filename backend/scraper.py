import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

APIFY_TOKEN = os.getenv("APIFY_TOKEN")
ACTOR_ID = "apify/instagram-scraper"
BASE_URL = "https://api.apify.com/v2"

def start_run(direct_urls: list, results_limit: int = 50) -> str:
    url = f"{BASE_URL}/acts/{ACTOR_ID}/runs?token={APIFY_TOKEN}"
    payload = {
        "directUrls": direct_urls,
        "resultsLimit": results_limit
    }
    response = requests.post(url, json=payload)
    response.raise_for_status()
    run_id = response.json()["data"]["id"]
    return run_id

def wait_for_completion(run_id: str, poll_interval: int = 5, timeout: int = 300) -> str:
    status_url = f"{BASE_URL}/actor-runs/{run_id}?token={APIFY_TOKEN}"
    elapsed = 0
    while elapsed < timeout:
        resp = requests.get(status_url)
        resp.raise_for_status()
        status = resp.json()["data"]["status"]
        if status == "SUCCEEDED":
            return status
        if status in ("FAILED", "ABORTED", "TIMED-OUT"):
            raise RuntimeError(f"Apify run ended with status: {status}")
        time.sleep(poll_interval)
        elapsed += poll_interval
    raise TimeoutError("Apify run did not complete within timeout")

def fetch_results(run_id: str) -> list:
    dataset_url = f"{BASE_URL}/actor-runs/{run_id}/dataset/items?token={APIFY_TOKEN}"
    resp = requests.get(dataset_url)
    resp.raise_for_status()
    return resp.json()

def scrape_posts(direct_urls: list, results_limit: int = 50) -> list:
    run_id = start_run(direct_urls, results_limit)
    print(f"Apify run started: {run_id}")
    wait_for_completion(run_id)
    print("Run completed, fetching results...")
    return fetch_results(run_id)
