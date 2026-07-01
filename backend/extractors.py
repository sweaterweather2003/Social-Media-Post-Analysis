# backend/extractors.py
import datetime
import time
import requests
import os
from typing import Dict, List

from dotenv import load_dotenv

load_dotenv()

APIFY_TOKEN = os.getenv("APIFY_TOKEN")
BASE_URL = "https://api.apify.com/v2"


def calculate_engagement(likes: int, comments: int, views: int = 0) -> float:
    total = likes + comments
    if views > 0:
        return round((total / views) * 100, 2)
    return round((total / max(total, 1)) * 100, 2) if total > 0 else 0.0


def scrape_posts(direct_urls: List[str]) -> List[Dict]:
    if not APIFY_TOKEN:
        print("❌ APIFY_TOKEN missing!")
        return []

    print(f"🔄 Scraping {len(direct_urls)} posts via Apify...")

    try:
        url = f"{BASE_URL}/acts/apify/instagram-scraper/runs?token={APIFY_TOKEN}"
        payload = {
            "directUrls": direct_urls,
            "resultsLimit": 50
        }
        resp = requests.post(url, json=payload)
        resp.raise_for_status()
        run_id = resp.json()["data"]["id"]

        # Wait for run
        status_url = f"{BASE_URL}/actor-runs/{run_id}?token={APIFY_TOKEN}"
        for _ in range(36):
            time.sleep(5)
            status = requests.get(status_url).json()["data"]["status"]
            if status == "SUCCEEDED":
                break
            if status in ["FAILED", "ABORTED"]:
                raise Exception(f"Run failed: {status}")

        # Get results
        dataset_url = f"{BASE_URL}/actor-runs/{run_id}/dataset/items?token={APIFY_TOKEN}"
        raw_results = requests.get(dataset_url).json()

        processed = []
        for post in raw_results:
            shortcode = post.get("shortCode")
            if not shortcode:
                continue
            data = {
                "post_id": shortcode,
                "platform": "Instagram",
                "creator": post.get("ownerUsername", "Unknown"),
                "title": (post.get("caption") or "No title")[:100],
                "views": post.get("videoViewCount") or post.get("viewsCount") or 0,
                "likes": post.get("likesCount") or 0,
                "comments": post.get("commentsCount") or 0,
                "engagement_rate": calculate_engagement(
                    post.get("likesCount", 0),
                    post.get("commentsCount", 0),
                    post.get("videoViewCount") or post.get("viewsCount") or 0
                ),
                "transcript": post.get("caption") or "No caption available.",
                "url": post.get("url"),
                "hashtags": [f"#{h}" for h in post.get("hashtags", [])],
                "upload_date": (post.get("timestamp") or "").split("T")[0],
                "duration": int(post.get("videoDuration") or 0),
                "post_type": "reel" if post.get("isVideo") else "post"
            }
            processed.append(data)

        return processed

    except Exception as e:
        print(f"❌ Error: {e}")
        return []


def get_instagram_posts_by_shortcodes(shortcodes: List[str]) -> List[Dict]:
    """This function is called from your frontend"""
    direct_urls = []
    for item in shortcodes:
        item = item.strip()
        if item.startswith("http"):
            direct_urls.append(item)
        else:
            direct_urls.append(f"https://www.instagram.com/p/{item}/")
    return scrape_posts(direct_urls)
