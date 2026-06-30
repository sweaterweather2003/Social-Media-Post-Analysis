# backend/extractors.py
import datetime
import time
import asyncio
from typing import Dict, List
import os

from dotenv import load_dotenv

load_dotenv()

def calculate_engagement(likes: int, comments: int, views: int = 0) -> float:
    total = likes + comments
    if views > 0:
        return round((total / views) * 100, 2)
    return round((total / max(total, 1)) * 100, 2) if total > 0 else 0.0


async def scrape_with_playwright(shortcode: str) -> Dict:
    """Advanced scraping using Playwright + Stealth"""
    try:
        from playwright.async_api import async_playwright
        from playwright_stealth import stealth_async
    except ImportError:
        print("❌ Playwright not installed. Run: pip install playwright playwright-stealth")
        return create_fallback(shortcode)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
        )
        
        page = await context.new_page()
        await stealth_async(page)

        try:
            url = f"https://www.instagram.com/p/{shortcode}/"
            await page.goto(url, wait_until="networkidle", timeout=30000)
            
            # Wait for content to load
            await page.wait_for_timeout(5000)
            
            # Try to extract data
            caption = await page.evaluate('''() => {
                const el = document.querySelector('span[data-testid="post-comment-text"]') || 
                          document.querySelector('div[data-testid="post-comment-text"]');
                return el ? el.innerText : "No caption available.";
            }''')

            # Get basic stats (often hidden, but we try)
            likes = 0
            comments = 0
            views = 0

            data = {
                "post_id": shortcode,
                "platform": "Instagram",
                "creator": "Unknown",
                "title": caption.split('\n')[0][:100] if caption else "Instagram Post",
                "views": views,
                "likes": likes,
                "comments": comments,
                "engagement_rate": calculate_engagement(likes, comments, views),
                "transcript": caption,
                "url": f"https://www.instagram.com/p/{shortcode}/",
                "hashtags": [],
                "upload_date": datetime.datetime.now().strftime("%Y-%m-%d"),
                "duration": 0,
                "post_type": "post"
            }
            
            print(f"✅ Playwright successfully scraped post {shortcode}")
            await browser.close()
            return data

        except Exception as e:
            print(f"❌ Playwright error for {shortcode}: {e}")
            await browser.close()
            return create_fallback(shortcode)


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
        "transcript": f"Could not fetch data for this post.\n\nInstagram is actively blocking automated tools.\n\nTry these:\n1. Make sure the post is public\n2. Try again later\n3. Use manual input mode (coming soon)",
        "url": f"https://www.instagram.com/p/{shortcode}/",
        "hashtags": [],
        "upload_date": datetime.datetime.now().strftime("%Y-%m-%d"),
        "duration": 0,
        "post_type": "post"
    }


def get_instagram_post(shortcode: str) -> Dict:
    """Main function - tries Playwright first"""
    try:
        # Run async function
        import asyncio
        return asyncio.run(scrape_with_playwright(shortcode))
    except Exception as e:
        print(f"Playwright failed: {e}")
        return create_fallback(shortcode)


def get_instagram_posts_by_shortcodes(shortcodes: List[str]) -> List[Dict]:
    print(f"Fetching {len(shortcodes)} Instagram posts using Playwright...")
    return [get_instagram_post(code.strip()) for code in shortcodes if code.strip()]


# Keep profile function simple
def get_instagram_profile_posts(username: str, max_posts: int = 12) -> List[Dict]:
    # Fallback to old method for profiles
    import instaloader
    L = instaloader.Instaloader()
    posts = []
    try:
        profile = instaloader.Profile.from_username(L.context, username)
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
                "followers": profile.followers,
                "views": getattr(post, 'video_view_count', 0) or 0,
                "likes": post.likes or 0,
                "comments": post.comments or 0,
                "engagement_rate": calculate_engagement(post.likes or 0, post.comments or 0, getattr(post, 'video_view_count', 0) or 0),
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
        print(f"Profile scraping error: {e}")
    return posts or [{"post_id": "demo", "platform": "Instagram", "creator": username, "title": "Demo Post", "transcript": "Demo content"}]
