# backend/extractors.py
import datetime
import random
from typing import Dict, List
import os

from dotenv import load_dotenv

load_dotenv()

# ====================== APIFY SETUP ======================
try:
    from apify_client import ApifyClient
    client = ApifyClient(os.getenv("APIFY_TOKEN"))
    APIFY_AVAILABLE = bool(os.getenv("APIFY_TOKEN"))
    print("✅ Apify client initialized successfully")
except ImportError:
    print("❌ Apify client not installed. Run: pip install apify-client")
    APIFY_AVAILABLE = False
    client = None
except Exception as e:
    print(f"❌ Apify initialization failed: {e}")
    APIFY_AVAILABLE = False
    client = None


def calculate_engagement(likes: int, comments: int, views: int = 0) -> float:
    total = likes + comments
    if views > 0:
        return round((total / views) * 100, 2)
    return round((total / max(total, 1)) * 100, 2) if total > 0 else 0.0


def apify_get_post(shortcode: str) -> Dict:
    """Scrape single post using Apify"""
    if not APIFY_AVAILABLE or not client:
        print("⚠️ Apify not available")
        return create_fallback(shortcode)

    try:
        print(f"🔄 Calling Apify for post: {shortcode}")
        
        run_input = {
            "postUrls": [f"https://www.instagram.com/p/{shortcode}/"],
            "resultsLimit": 1,
        }

        run = client.actor("apify/instagram-post-scraper").call(run_input=run_input)
        dataset = client.dataset(run["defaultDatasetId"])
        items = dataset.list_items().items

        if not items:
            print(f"⚠️ Apify returned no data for {shortcode}")
            return create_fallback(shortcode)

        post = items[0]
        print(f"✅ Apify SUCCESS for post {shortcode}")

        return {
            "post_id": shortcode,
            "platform": "Instagram",
            "creator": post.get("ownerUsername", "Unknown"),
            "title": (post.get("caption") or "").split('\n')[0][:100] if post.get("caption") else "Instagram Post",
            "views": post.get("videoViewCount") or post.get("viewsCount") or 0,
            "likes": post.get("likesCount") or 0,
            "comments": post.get("commentsCount") or 0,
            "engagement_rate": calculate_engagement(
                post.get("likesCount", 0),
                post.get("commentsCount", 0),
                post.get("videoViewCount") or post.get("viewsCount") or 0
            ),
            "transcript": post.get("caption") or "No caption available.",
            "url": f"https://www.instagram.com/p/{shortcode}/",
            "hashtags": [f"#{tag}" for tag in post.get("hashtags", [])],
            "upload_date": post.get("timestamp", "").split("T")[0] if post.get("timestamp") else datetime.datetime.now().strftime("%Y-%m-%d"),
            "duration": int(post.get("videoDuration") or 0),
            "post_type": "reel" if post.get("isVideo", False) or post.get("videoUrl") else "post"
        }

    except Exception as e:
        print(f"❌ Apify ERROR for {shortcode}: {type(e).__name__} - {e}")
        return create_fallback(shortcode)


def apify_get_profile_posts(username: str, max_posts: int = 12) -> List[Dict]:
    """Scrape profile posts using Apify"""
    if not APIFY_AVAILABLE or not client:
        print("⚠️ Apify not available for profile")
        return [{"post_id": "demo", "platform": "Instagram", "creator": username, "title": "Demo Post", "transcript": "Apify not available"}]

    try:
        print(f"🔄 Calling Apify for profile: @{username}")
        
        run_input = {
            "directUrls": [f"https://www.instagram.com/{username}/"],
            "resultsLimit": max_posts,
            "resultsType": "posts",   # You can change to "reels" if preferred
        }

        run = client.actor("apify/instagram-scraper").call(run_input=run_input)
        dataset = client.dataset(run["defaultDatasetId"])
        items = dataset.list_items().items

        posts = []
        for post in items[:max_posts]:
            shortcode = post.get("shortCode") or post.get("id")
            if not shortcode:
                continue
                
            data = {
                "post_id": shortcode,
                "platform": "Instagram",
                "creator": username,
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
                "url": f"https://www.instagram.com/p/{shortcode}/",
                "hashtags": [f"#{tag}" for tag in post.get("hashtags", [])],
                "upload_date": post.get("timestamp", "").split("T")[0] if post.get("timestamp") else datetime.datetime.now().strftime("%Y-%m-%d"),
                "duration": int(post.get("videoDuration") or 0),
                "post_type": "reel" if post.get("isVideo", False) or post.get("videoUrl") else "post"
            }
            posts.append(data)

        print(f"✅ Apify fetched {len(posts)} posts from @{username}")
        return posts

    except Exception as e:
        print(f"❌ Apify Profile ERROR for @{username}: {e}")
        return [{"post_id": "demo", "platform": "Instagram", "creator": username, "title": "Demo Post", "transcript": "Failed to fetch profile"}]


def create_fallback(shortcode: str) -> Dict:
    return {
        "post_id": shortcode,
        "platform": "Instagram",
        "creator": "Unknown",
        "title": f"Post {shortcode}",
        "views": 0,
        "likes": 0,
        "comments": 0,
        "engagement_rate": 0.0,
        "transcript": f"Could not fetch data for this post.\n\n1. Make sure the post is public\n2. Check your APIFY_TOKEN\n3. Try again later",
        "url": f"https://www.instagram.com/p/{shortcode}/",
        "hashtags": [],
        "upload_date": datetime.datetime.now().strftime("%Y-%m-%d"),
        "duration": 0,
        "post_type": "post"
    }


def get_instagram_post(shortcode: str) -> Dict:
    return apify_get_post(shortcode)


def get_instagram_posts_by_shortcodes(shortcodes: List[str]) -> List[Dict]:
    print(f"Fetching {len(shortcodes)} Instagram posts using Apify...")
    return [get_instagram_post(code.strip()) for code in shortcodes if code.strip()]


def get_instagram_profile_posts(username: str, max_posts: int = 12) -> List[Dict]:
    """Now using Apify for profiles too"""
    return apify_get_profile_posts(username, max_posts)


__all__ = ["get_instagram_post", "get_instagram_posts_by_shortcodes", "get_instagram_profile_posts", "calculate_engagement"]
