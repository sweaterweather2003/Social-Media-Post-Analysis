import os
from pathlib import Path
from typing import List
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

# Project imports
from db import init_db
from scraper import scrape_posts
from analysis import run_full_analysis, load_dataframe

app = FastAPI(title="Instagram Growth OS")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PostsPayload(BaseModel):
    post_urls: List[str]
    focus: str = "engagement comparison, best performing, improvement suggestions"

@app.post("/api/analyze-posts")
async def analyze_posts(payload: PostsPayload):
    try:
        print(f"🔍 Analyzing {len(payload.post_urls)} Instagram posts via Apify...")

        init_db()
        results = scrape_posts(payload.post_urls, results_limit=50)

        print(f"Fetched {len(results)} items. Storing in database...")
        for item in results:
            post_data = {
                "post_url": item.get("url"),
                "shortcode": item.get("shortCode"),
                "username": item.get("ownerUsername"),
                "caption": item.get("caption"),
                "likes_count": item.get("likesCount", 0),
                "comments_count": item.get("commentsCount", 0),
                "timestamp": item.get("timestamp"),
            }
            # Reuse your existing insert_post
            from db import insert_post
            insert_post(post_data)

        print("Running analysis...")
        run_full_analysis()

        df = load_dataframe()
        
        summary = {
            "total_posts": len(df),
            "avg_likes": round(float(df['likes_count'].mean()), 1) if not df.empty else 0,
            "avg_comments": round(float(df['comments_count'].mean()), 1) if not df.empty else 0,
            "charts": ["engagement_trend.png", "top_posts.png"]
        }

        return {
            "success": True,
            "analysis": f"Analyzed {len(results)} posts successfully.",
            "summary": summary,
            "raw_posts": results[:10]  # limit for frontend
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8001)))
