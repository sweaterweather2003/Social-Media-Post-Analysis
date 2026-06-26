import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Import the extractors
from extractors import get_instagram_profile_posts, get_instagram_posts_by_shortcodes

load_dotenv()
backend_dir = Path(__file__).resolve().parent

if not os.getenv("GOOGLE_API_KEY"):
    raise ValueError("CRITICAL ERROR: GOOGLE_API_KEY is missing from your .env file!")

# Fixed models
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.4)
embeddings = GoogleGenerativeAIEmbeddings(model="gemini-embedding-2-preview")

vector_store = Chroma(
    embedding_function=embeddings, 
    persist_directory=str(backend_dir / "chroma_db_gemini")
)

def analyze_profile(profile_handle: str, focus: str = "growth, best posts, trends, suggestions"):
    print(f"🔍 Analyzing profile: {profile_handle}")
    
    try:
        posts = get_instagram_profile_posts(profile_handle, max_posts=12)
        print(f"✅ Fetched {len(posts)} posts from Instagram")
    except Exception as e:
        print(f"⚠️ Failed to fetch posts: {e}")
        posts = []

    search = DuckDuckGoSearchRun()
    search_query = f"{profile_handle} instagram reels best performing content OR trends 2026"
    try:
        search_results = search.run(search_query)
    except Exception as e:
        print(f"⚠️ Search failed: {e}")
        search_results = "No additional search results available."

    posts_summary = "\n".join([
        f"- {p.get('title', 'Untitled')} | Views: {p.get('views', 0)} | Likes: {p.get('likes', 0)} | "
        f"Comments: {p.get('comments', 0)} | Engagement: {p.get('engagement_rate', 0)}% | Date: {p.get('upload_date')}"
        for p in posts[:10]
    ]) if posts else "No posts were fetched."

    prompt = f"""
You are a top social media growth strategist in 2026.

Profile: @{profile_handle}
Focus: {focus}

Recent Posts Data:
{posts_summary}

Additional Web Context:
{search_results}

Provide a clear, structured, and actionable response with these sections:

- Key Insights & Metrics
- Best Performing Content
- Current Trends Relevant to this Profile
- 4-5 Specific Actionable Recommendations

Write naturally like a professional strategist. Do not use technical shortcodes in the final response.
"""

    response = llm.invoke(prompt)
    result = response.content if hasattr(response, 'content') else str(response)
    
    doc = Document(
        page_content=result,
        metadata={"profile": profile_handle, "type": "profile_analysis", "timestamp": datetime.now().isoformat()}
    )
    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
    chunks = splitter.split_documents([doc])
    vector_store.add_documents(chunks)
    
    return result


def analyze_posts(shortcodes: List[str], focus: str = "engagement comparison, best performing, improvement suggestions"):
    print(f"🔍 Analyzing {len(shortcodes)} Instagram posts")
    
    try:
        posts = get_instagram_posts_by_shortcodes(shortcodes)
        print(f"✅ Fetched {len(posts)} posts")
    except Exception as e:
        print(f"⚠️ Failed to fetch posts: {e}")
        posts = []

    posts_summary = "\n".join([
        f"Post {i+1}: {p.get('title')} | Views: {p.get('views')} | Likes: {p.get('likes')} | "
        f"Comments: {p.get('comments')} | Engagement: {p.get('engagement_rate')}%"
        for i, p in enumerate(posts)
    ]) if posts else "No posts were fetched."

    prompt = f"""
You are a friendly, professional social media growth strategist in 2026. Speak naturally and conversationally.

You are analyzing Instagram Reels for the user.

Post Data:
{posts_summary}

Provide a clean, natural response with these sections:

- Overall Performance Summary
- What Stood Out (Best Aspects)
- Areas for Improvement
- Actionable Recommendations

Important Instructions:
- Write like a human expert, not a robot.
- Do NOT mention shortcodes, technical IDs, or internal references.
- Refer to posts as "the first reel", "the second reel", "the food reel", "the storytelling reel", etc.
- Be encouraging but honest.
- Keep the tone professional yet approachable.
"""

    response = llm.invoke(prompt)
    result = response.content if hasattr(response, 'content') else str(response)
    
    doc = Document(
        page_content=result,
        metadata={"type": "posts_analysis", "timestamp": datetime.now().isoformat()}
    )
    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
    chunks = splitter.split_documents([doc])
    vector_store.add_documents(chunks)
    
    return result


__all__ = ["analyze_profile", "analyze_posts", "vector_store", "llm"]
