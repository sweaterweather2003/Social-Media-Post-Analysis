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
    """Core Apify scraping function"""
    if not APIFY_TOKEN:
        print("❌ APIFY_TOKEN is missing!")
        return []

    print(f"🔄 Scraping {len(direct_urls)} items via Apify...")

    try:
        url = f"{BASE_URL}/acts/apify/instagram-scraper/runs?token={APIFY_TOKEN}"
        payload = {
            "directUrls": direct_urls,
            "resultsLimit": 50
        }
        resp = requests.post(url, json=payload)
        resp.raise_for_status()
        run_id = resp.json()["data"]["id"]
        print(f"🚀 Apify run started: {run_id}")

        # Wait for completion
        status_url = f"{BASE_URL}/actor-runs/{run_id}?token={APIFY_TOKEN}"
        for _ in range(36):  # ~3 minutes max
            time.sleep(5)
            status_resp = requests.get(status_url)
            status_resp.raise_for_status()
            status = status_resp.json()["data"]["status"]
            if status == "SUCCEEDED":
                print("✅ Apify run completed")
                break
            if status in ["FAILED", "ABORTED"]:
                raise Exception(f"Run failed: {status}")

        # Fetch results
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
                "post_type": "reel" if post.get("isVideo", False) else "post"
            }
            processed.append(data)

        print(f"✅ Successfully fetched {len(processed)} posts")
        return processed

    except Exception as e:
        print(f"❌ Apify error: {e}")
        return []


def get_instagram_posts_by_shortcodes(shortcodes: List[str]) -> List[Dict]:
    """Used by analyze_posts"""
    direct_urls = []
    for item in shortcodes:
        item = item.strip()
        if item.startswith("http"):
            direct_urls.append(item)
        else:
            direct_urls.append(f"https://www.instagram.com/p/{item}/")
    return scrape_posts(direct_urls)


def get_instagram_profile_posts(username: str, max_posts: int = 12) -> List[Dict]:
    """Used by analyze_profile"""
    try:
        direct_urls = [f"https://www.instagram.com/{username}/"]
        return scrape_posts(direct_urls)[:max_posts]
    except:
        return [{"post_id": "demo", "platform": "Instagram", "creator": username, "title": "Demo Post", "transcript": "Profile fetch failed"}]


__all__ = ["get_instagram_posts_by_shortcodes", "get_instagram_profile_posts", "calculate_engagement"]
