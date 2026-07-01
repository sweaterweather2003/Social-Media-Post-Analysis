# backend/extractors.py
import datetime
import time
import asyncio
import random
from typing import Dict, List
import os

from dotenv import load_dotenv

load_dotenv()

# Apify Client
try:
    from apify_client import ApifyClient
    client = ApifyClient(os.getenv("APIFY_TOKEN"))
    APIFY_AVAILABLE = True
except ImportError:
    print("⚠️ Apify client not installed. Install with: pip install apify-client")
    APIFY_AVAILABLE = False
    client = None


def calculate_engagement(likes: int, comments: int, views: int = 0) -> float:
    total = likes + comments
    if views > 0:
        return round((total / views) * 100, 2)
    return round((total / max(total, 1)) * 100, 2) if total > 0 else 0.0


def apify_get_post(shortcode: str) -> Dict:
    """Primary scraper using Apify Instagram Post Scraper"""
    if not APIFY_AVAILABLE or not client:
        return None

    try:
        run_input = {
            "postUrls": [f"https://www.instagram.com/p/{shortcode}/"],
            "resultsLimit": 1,
            "includeComments": False,  # Set True if you need comments
        }

        run = client.actor("apify/instagram-post-scraper").call(run_input=run_input)
        
        dataset = client.dataset(run["defaultDatasetId"])
        items = dataset.list_items().items

        if not items:
            return None

        post = items[0]

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
        print(f"❌ Apify error for {shortcode}: {e}")
        return None


async def scrape_with_playwright(shortcode: str) -> Dict:
    """Fallback scraper (your original code)"""
    try:
        from playwright.async_api import async_playwright
        from playwright_stealth import stealth_async
    except ImportError:
        print("❌ Playwright not installed. Run: pip install playwright playwright-stealth")
        return create_fallback(shortcode)

    async with async_playwright() as p:
        session_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "instagram_session")
        
        context = await p.chromium.launch_persistent_context(
            user_data_dir=session_dir,
            headless=True,
            viewport={"width": 1366, "height": 768},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            locale="en-US",
            timezone_id="America/New_York"
        )
        
        page = await context.new_page()
        await stealth_async(page)

        try:
            url = f"https://www.instagram.com/p/{shortcode}/"
            await asyncio.sleep(random.uniform(1.0, 3.0))
            await page.goto(url, wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(random.randint(3000, 6000))
            
            await page.evaluate("window.scrollTo({top: random = Math.floor(Math.random() * 200) + 100, behavior: 'smooth'});")
            await page.wait_for_timeout(random.randint(1500, 3000))

            caption = await page.evaluate('''() => {
                const el = document.querySelector('span[data-testid="post-comment-text"]') || 
                          document.querySelector('div[data-testid="post-comment-text"]') ||
                          document.querySelector('h1._ap3a');
                return el ? el.innerText : "No caption available.";
            }''')

            if "login" in page.url or caption == "No caption available.":
                body_text = await page.inner_text("body")
                if "Login" in body_text and "Sign Up" in body_text:
                    raise Exception("Encountered Instagram Login Wall.")

            data = {
                "post_id": shortcode,
                "platform": "Instagram",
                "creator": "Unknown",
                "title": caption.split('\n')[0][:100] if caption else "Instagram Post",
                "views": 0,
                "likes": 0,
                "comments": 0,
                "engagement_rate": 0.0,
                "transcript": caption,
                "url": f"https://www.instagram.com/p/{shortcode}/",
                "hashtags": [],
                "upload_date": datetime.datetime.now().strftime("%Y-%m-%d"),
                "duration": 0,
                "post_type": "post"
            }
            
            print(f"✅ Playwright fallback succeeded for {shortcode}")
            await context.close()
            return data

        except Exception as e:
            print(f"❌ Playwright error for {shortcode}: {e}")
            await context.close()
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
        "transcript": f"Could not fetch data for this post.\n\nTry these:\n1. Make sure the post is public\n2. Try again later",
        "url": f"https://www.instagram.com/p/{shortcode}/",
        "hashtags": [],
        "upload_date": datetime.datetime.now().strftime("%Y-%m-%d"),
        "duration": 0,
        "post_type": "post"
    }


def get_instagram_post(shortcode: str) -> Dict:
    """Main function - tries Apify first, then Playwright fallback"""
    # Try Apify first
    if APIFY_AVAILABLE:
        data = apify_get_post(shortcode)
        if data:
            print(f"✅ Apify successfully scraped post {shortcode}")
            return data

    # Fallback to Playwright
    try:
        import asyncio
        return asyncio.run(scrape_with_playwright(shortcode))
    except Exception as e:
        print(f"Playwright failed: {e}")
        return create_fallback(shortcode)


def get_instagram_posts_by_shortcodes(shortcodes: List[str]) -> List[Dict]:
    print(f"Fetching {len(shortcodes)} Instagram posts using Apify + fallback...")
    return [get_instagram_post(code.strip()) for code in shortcodes if code.strip()]


def get_instagram_profile_posts(username: str, max_posts: int = 12) -> List[Dict]:
    """Profile scraper - still using Instaloader for now (can be upgraded to Apify later)"""
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
            time.sleep(random.uniform(1.5, 3.5))
    except Exception as e:
        print(f"Profile scraping error: {e}")
    return posts or [{"post_id": "demo", "platform": "Instagram", "creator": username, "title": "Demo Post", "transcript": "Demo content"}]
