# backend/extractors.py
import datetime
from typing import Dict, List

from scraper import scrape_posts   # Import the new scraper


def calculate_engagement(likes: int, comments: int, views: int = 0) -> float:
    total = likes + comments
    if views > 0:
        return round((total / views) * 100, 2)
    return round((total / max(total, 1)) * 100, 2) if total > 0 else 0.0


def get_instagram_posts_by_shortcodes(shortcodes: List[str]) -> List[Dict]:
    """Main function used by your app"""
    print(f"Fetching {len(shortcodes)} Instagram posts using Apify...")

    raw_results = scrape_posts(shortcodes)

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

    return processed


# Keep profile function simple for now
def get_instagram_profile_posts(username: str, max_posts: int = 12) -> List[Dict]:
    return scrape_posts([f"https://www.instagram.com/{username}/"])[:max_posts]
