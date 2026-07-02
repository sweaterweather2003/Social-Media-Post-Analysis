import os
from pathlib import Path
from typing import List, Dict
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Crucial for async in FastAPI
import nest_asyncio
nest_asyncio.apply()

load_dotenv()

# Project imports
from db import init_db, insert_post
from scraper import scrape_posts
from analysis import run_full_analysis, load_dataframe
from rag_engine import analyze_posts, get_chat_context

# LangChain imports for chat
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

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

class ChatPayload(BaseModel):
    question: str
    chat_history: List[Dict[str, str]] = []

@app.post("/api/analyze-posts")
async def analyze_posts_endpoint(payload: PostsPayload):
    try:
        print(f"🔍 Analyzing {len(payload.post_urls)} Instagram posts via Apify...")

        init_db()
        
        # Scrape using Apify
        results = scrape_posts(payload.post_urls, results_limit=50)

        print(f"Fetched {len(results)} item(s). Storing in database...")
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
            insert_post(post_data)

        print("Running statistical analysis and generating charts...")
        run_full_analysis()

        df = load_dataframe()
        
        summary = {
            "total_posts": len(df),
            "avg_likes": round(float(df['likes_count'].mean()), 1) if not df.empty else 0,
            "avg_comments": round(float(df['comments_count'].mean()), 1) if not df.empty else 0,
            "charts": ["engagement_trend.png", "top_posts.png"]
        }

        # Generate AI insights
        ai_analysis = analyze_posts(payload.post_urls)

        return {
            "success": True,
            "analysis": ai_analysis,
            "summary": summary,
            "raw_posts": results[:8]  # Limit for response size
        }
    except Exception as e:
        print(f"Error in analyze_posts: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/chat")
async def chat_endpoint(payload: ChatPayload):
    try:
        question = payload.question
        retriever = get_chat_context()
        
        template = """You are an expert Instagram growth strategist.
        Use the following previous analyses and context to answer the user's question.

        Context:
        {context}

        Question: {question}

        Important: Respond with clean, natural English paragraphs and bullet points only.
        Do NOT output JSON, code blocks, or any technical formatting.
        Just write like a normal helpful AI assistant."""

        prompt = ChatPromptTemplate.from_template(template)

        chain = (
            {"context": retriever, "question": RunnablePassthrough()}
            | prompt
            | llm
            | StrOutputParser()
        )

        response = chain.invoke(question)
        return {"response": response}
        
    except Exception as e:
        return {"response": f"Sorry, I encountered an error: {str(e)}"}

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8001)))
