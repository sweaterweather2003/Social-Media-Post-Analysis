def get_instagram_post(shortcode: str) -> Dict:
    import instaloader
    L = instaloader.Instaloader()
    L.context._session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    })
    
    try:
        post = instaloader.Post.from_shortcode(L.context, shortcode)
        
        data = {
            "post_id": post.shortcode,
            "platform": "Instagram",
            "creator": post.owner_username,
            "title": (post.caption or "Reel").split('\n')[0][:100],
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
        return data
    except Exception as e:
        print(f"⚠️ Error fetching post {shortcode}: {e}")
        return {
            "post_id": shortcode,
            "platform": "Instagram",
            "creator": "Unknown",
            "title": f"Post {shortcode} (Error)",
            "views": 0,
            "likes": 0,
            "comments": 0,
            "engagement_rate": 0.0,
            "transcript": "Could not fetch post details.",
            "url": f"https://www.instagram.com/reel/{shortcode}/",
            "hashtags": [],
            "upload_date": datetime.datetime.now().strftime("%Y-%m-%d"),
            "duration": 0,
            "post_type": "reel"
        }


def get_instagram_posts_by_shortcodes(shortcodes: List[str]) -> List[Dict]:
    return [get_instagram_post(code.strip()) for code in shortcodes if code.strip()]
