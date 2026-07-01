# backend/extractors.py
import datetime
from typing import Dict, List
import os
import requests
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
    """Exact same logic as your working bot"""
    if not APIFY_TOKEN:
        print("❌ APIFY_TOKEN is missing!")
        return []

    print(f"🔄 Scraping {len(direct_urls)} URLs via Apify...")

    try:
        # Start run
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
        for _ in range(36):  # max 3 minutes
            time.sleep(5)
            status_resp = requests.get(status_url)
            status = status_resp.json()["data"]["status"]
            if status == "SUCCEEDED":
                break
            if status in ["FAILED", "ABORTED"]:
                raise Exception(f"Run failed: {status}")

        # Fetch results
        dataset_url = f"{BASE_URL}/actor-runs/{run_id}/dataset/items?token={APIFY_TOKEN}"
        data_resp = requests.get(dataset_url)
        raw_results = data_resp.json()

        # Process results
        processed = []
        for post in raw_results:
            shortcode = post.get("shortCode")
            if not shortcode:
                continue
            data = {
                "post_id": shortcode,
                "platform": "Instagram",
                "creator": post.get("ownerUsername", "Unknown"),
                "title": (post.get("caption") or "").split('\n')[0][:100],
                "views": post.get("videoViewCount") or post.get("viewsCount") or 0,
                "likes": post.get("likesCount") or 0,
                "comments": post.get("commentsCount") or 0,
                "engagement_rate": calculate_engagement(
                    post.get("likesCount", 0), 
                    post.get("commentsCount", 0),
                    post.get("videoViewCount") or post.get("viewsCount") or 0
                ),
                "transcript": post.get("caption") or "No caption",
                "url": post.get("url"),
                "hashtags": [f"#{h}" for h in post.get("hashtags", [])],
                "upload_date": (post.get("timestamp") or "").split("T")[0],
                "duration": int(post.get("videoDuration") or 0),
                "post_type": "reel" if post.get("isVideo") else "post"
            }
            processed.append(data)

        print(f"✅ Successfully analyzed {len(processed)} posts")
        return processed

    except Exception as e:
        print(f"❌ Scraping error: {e}")
        return []


def get_instagram_posts_by_shortcodes(shortcodes: List[str]) -> List[Dict]:
    """This is called from rag_engine"""
    # Convert to full URLs
    urls = []
    for s in shortcodes:
        s = s.strip()
        if s.startswith("http"):
            urls.append(s)
        else:
            urls.append(f"https://www.instagram.com/p/{s}/" if not s.startswith("reel") else f"https://www.instagram.com/reel/{s}/")
    return scrape_posts(urls)
