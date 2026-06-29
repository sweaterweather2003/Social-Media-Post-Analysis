# backend/extractors.py
import datetime
import time
from typing import Dict, List

def calculate_engagement(likes: int, comments: int, views: int = 0) -> float:
    total = likes + comments
    if views > 0:
        return round((total / views) * 100, 2)
    return round((total / max(total, 1)) * 100, 2) if total > 0 else 0.0


def get_instagram_post(shortcode: str) -> Dict:
    import instaloader
    L = instaloader.Instaloader()
    
    # Improved headers
    L.context._session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.instagram.com/",
    })
    
    try:
        post = instaloader.Post.from_shortcode(L.context, shortcode)
        full_caption = post.caption or "No caption available."
        
        data = {
            "post_id": post.shortcode,
            "platform": "Instagram",
            "creator": getattr(post, 'owner_username', 'Unknown'),
            "title": (full_caption or "Instagram Post").split('\n')[0][:100],
            "views": getattr(post, 'video_view_count', 0) or getattr(post, 'view_count', 0) or 0,
            "likes": getattr(post, 'likes', 0) or 0,
            "comments": getattr(post, 'comments', 0) or 0,
            "engagement_rate": calculate_engagement(
                getattr(post, 'likes', 0) or 0, 
                getattr(post, 'comments', 0) or 0, 
                getattr(post, 'video_view_count', 0) or getattr(post, 'view_count', 0) or 0
            ),
            "transcript": full_caption,
            "url": f"https://www.instagram.com/p/{post.shortcode}/",
            "hashtags": [f"#{tag}" for tag in getattr(post, 'caption_hashtags', [])],
            "upload_date": post.date_utc.strftime("%Y-%m-%d") if hasattr(post, 'date_utc') else datetime.datetime.now().strftime("%Y-%m-%d"),
            "duration": int(getattr(post, 'video_duration', 0) or 0),
            "post_type": "reel" if getattr(post, 'is_video', False) else "post"
        }
        print(f"✅ Successfully fetched post {shortcode}")
        return data
    except Exception as e:
        print(f"⚠️ Failed to fetch post {shortcode}: {e}")
        return {
            "post_id": shortcode,
            "platform": "Instagram",
            "creator": "Unknown",
            "title": f"Post {shortcode}",
            "views": 0,
            "likes": 0,
            "comments": 0,
            "engagement_rate": 0.0,
            "transcript": f"⚠️ Could not fetch full data for this post.\n\nReason: Instagram is currently blocking automated access.\n\nTry these solutions:\n1. Make sure the post is public\n2. Wait 10-15 minutes and try again\n3. Use a different shortcode",
            "url": f"https://www.instagram.com/p/{shortcode}/",
            "hashtags": [],
            "upload_date": datetime.datetime.now().strftime("%Y-%m-%d"),
            "duration": 0,
            "post_type": "post"
        }


def get_instagram_posts_by_shortcodes(shortcodes: List[str]) -> List[Dict]:
    print(f"Fetching {len(shortcodes)} Instagram posts...")
    return [get_instagram_post(code.strip()) for code in shortcodes if code.strip()]


def get_instagram_profile_posts(username: str, max_posts: int = 12) -> List[Dict]:
    import instaloader
    L = instaloader.Instaloader()
    L.context._session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    })
    
    posts = []
    try:
        profile = instaloader.Profile.from_username(L.context, username)
        follower_count = profile.followers
        count = 0
        for post in profile.get_posts():
            if count >= max_posts:
                break
            full_caption = post.caption or "No caption available."
            data = {
                "post_id": post.shortcode,
                "platform": "Instagram",
                "creator": username,
                "title": full_caption.split('\n')[0][:100],
                "followers": follower_count,
                "views": getattr(post, 'video_view_count', 0) or getattr(post, 'view_count', 0) or 0,
                "likes": post.likes or 0,
                "comments": post.comments or 0,
                "engagement_rate": calculate_engagement(post.likes or 0, post.comments or 0, getattr(post, 'video_view_count', 0) or getattr(post, 'view_count', 0)),
                "transcript": full_caption,
                "url": f"https://www.instagram.com/p/{post.shortcode}/",
                "hashtags": [f"#{tag}" for tag in getattr(post, 'caption_hashtags', [])],
                "upload_date": post.date_utc.strftime("%Y-%m-%d"),
                "duration": int(getattr(post, 'video_duration', 0) or 0),
                "post_type": "reel" if getattr(post, 'is_video', False) else "post"
            }
            posts.append(data)
            count += 1
            time.sleep(1)
    except Exception as e:
        print(f"⚠️ Instagram profile error: {e}")
        posts = [{
            "post_id": "demo",
            "platform": "Instagram",
            "creator": username,
            "title": "Demo Post",
            "followers": 0,
            "views": 0,
            "likes": 0,
            "comments": 0,
            "engagement_rate": 0.0,
            "transcript": "Demo content - Instagram scraping may be restricted.",
            "url": "#",
            "hashtags": [],
            "upload_date": datetime.datetime.now().strftime("%Y-%m-%d"),
            "duration": 0,
            "post_type": "post"
        }]
    return posts
