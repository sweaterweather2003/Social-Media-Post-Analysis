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
    """Scrape posts using Apify API - exact logic from your working bot"""
    if not APIFY_TOKEN:
        print("❌ APIFY_TOKEN is missing in environment variables!")
        return []

    print(f"🔄 Scraping {len(direct_urls)} URLs via Apify...")

    try:
        # Start the Apify run
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
        for _ in range(36):  # Max ~3 minutes
            time.sleep(5)
            status_resp = requests.get(status_url)
            status_resp.raise_for_status()
            status = status_resp.json()["data"]["status"]
            
            if status == "SUCCEEDED":
                print("✅ Apify run completed successfully")
                break
            if status in ["FAILED", "ABORTED", "TIMED-OUT"]:
                raise Exception(f"Apify run failed with status: {status}")
            print(f"⏳ Status: {status}...")

        # Fetch results
        dataset_url = f"{BASE_URL}/actor-runs/{run_id}/dataset/items?token={APIFY_TOKEN}"
        data_resp = requests.get(dataset_url)
        data_resp.raise_for_status()
        raw_results = data_resp.json()

        # Process into our format
        processed = []
        for post in raw_results:
            shortcode = post.get("shortCode") or post.get("id")
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
                "transcript": post.get("caption") or "No caption available.",
                "url": post.get("url"),
                "hashtags": [f"#{tag}" for tag in post.get("hashtags", [])],
                "upload_date": (post.get("timestamp") or "").split("T")[0] if post.get("timestamp") else datetime.datetime.now().strftime("%Y-%m-%d"),
                "duration": int(post.get("videoDuration") or 0),
                "post_type": "reel" if post.get("isVideo", False) else "post"
            }
            processed.append(data)

        print(f"✅ Successfully processed {len(processed)} posts")
        return processed

    except Exception as e:
        print(f"❌ Apify scraping error: {e}")
        return []


def get_instagram_posts_by_shortcodes(shortcodes: List[str]) -> List[Dict]:
    """Called by rag_engine.py - converts input and scrapes"""
    print(f"Fetching {len(shortcodes)} Instagram posts...")
    
    # Convert shortcodes or URLs
    direct_urls = []
    for item in shortcodes:
        item = item.strip()
        if item.startswith("http"):
            direct_urls.append(item)
        else:
            # Handle both post and reel shortcodes
            if "reel" in item.lower():
                direct_urls.append(f"https://www.instagram.com/reel/{item}/")
            else:
                direct_urls.append(f"https://www.instagram.com/p/{item}/")
    
    return scrape_posts(direct_urls)


def get_instagram_profile_posts(username: str, max_posts: int = 12) -> List[Dict]:
    """Profile analysis using Apify"""
    try:
        return scrape_posts([f"https://www.instagram.com/{username}/"])[:max_posts]
    except:
        return [{"post_id": "demo", "platform": "Instagram", "creator": username, "title": "Demo Post", "transcript": "Profile fetch failed"}]
