import datetime
import time
from typing import Dict, List

def calculate_engagement(likes: int, comments: int, views: int = 0) -> float:
    total = likes + comments
    if views > 0:
        return round((total / views) * 100, 2)
    return round((total / max(total, 1)) * 100, 2) if total > 0 else 0.0


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
            if not getattr(post, 'is_video', False):
                continue
                
            data = {
                "post_id": post.shortcode,
                "platform": "Instagram",
                "creator": username,
                "title": (post.caption or "Reel").split('\n')[0][:100],
                "followers": follower_count,
                "views": getattr(post, 'video_view_count', 0) or 0,
                "likes": post.likes or 0,
                "comments": post.comments or 0,
                "engagement_rate": calculate_engagement(post.likes or 0, post.comments or 0, getattr(post, 'video_view_count', 0)),
                "transcript": post.caption or "No caption available.",
                "url": f"https://www.instagram.com/reel/{post.shortcode}/",
                "hashtags": [f"#{tag}" for tag in getattr(post, 'caption_hashtags', [])],
                "upload_date": post.date_utc.strftime("%Y-%m-%d"),
                "duration": int(getattr(post, 'video_duration', 0)),
                "post_type": "reel"
            }
            posts.append(data)
            count += 1
            time.sleep(1)
    except Exception as e:
        print(f"⚠️ Instagram error: {e}")
        posts = [{
            "post_id": "demo",
            "platform": "Instagram",
            "creator": username,
            "title": "Demo Post (Scraping limited)",
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
            "post_type": "reel"
        }]
    
    return posts


# Placeholder functions (you can implement later)
def get_twitter_profile_posts(username: str, max_posts: int = 10) -> List[Dict]:
    return []  # TODO: Implement with snscrape or Twitter API

def get_facebook_page_posts(page: str, max_posts: int = 10) -> List[Dict]:
    return []  # TODO: Implement


def get_all_platform_posts(instagram_username: str, twitter_username: str = "", facebook_page: str = ""):
    return {
        "Instagram": get_instagram_profile_posts(instagram_username),
        "Twitter": get_twitter_profile_posts(twitter_username),
        "Facebook": get_facebook_page_posts(facebook_page)
    }
