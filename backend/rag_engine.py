import os
from pathlib import Path
from datetime import datetime
from typing import List

from dotenv import load_dotenv

# LangChain imports
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv()

backend_dir = Path(__file__).resolve().parent

# Check for Google API Key
if not os.getenv("GOOGLE_API_KEY"):
    print("⚠️  GOOGLE_API_KEY is missing from .env file! Chat features will be limited.")

# Initialize LLM and Embeddings
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    temperature=0.4,
    convert_system_message_to_human=True
)

embeddings = GoogleGenerativeAIEmbeddings(model="embedding-001")

# Vector Store
vector_store = Chroma(
    embedding_function=embeddings,
    persist_directory=str(backend_dir / "chroma_db")
)

def analyze_posts(shortcodes_or_urls: List[str], focus: str = "engagement comparison, best performing, improvement suggestions"):
    """This function is called from main.py after scraping"""
    print(f"🔍 Generating AI insights for {len(shortcodes_or_urls)} posts...")

    # Load data from database
    from db import get_all_posts
    posts = get_all_posts()

    if not posts:
        return "No posts found in database."

    posts_details = []
    for i, p in enumerate(posts):
        posts_details.append(f"""
Post {i+1}:
URL: {p.get('post_url')}
Shortcode: {p.get('shortcode')}
Likes: {p.get('likes_count')} | Comments: {p.get('comments_count')}
Caption: {p.get('caption', 'No caption')[:500]}...
""")

    posts_summary = "\n".join(posts_details)

    prompt = f"""
You are a professional Instagram growth strategist in 2026.

Here is the data from the analyzed posts:

{posts_summary}

Focus: {focus}

Respond in this exact format:

**1. Performance Summary**
- Overall engagement level
- Best performing post and why
- Key insights

**2. What Worked Well**
- List 3-4 strengths

**3. Areas for Improvement**
- List 3-4 weaknesses

**4. Actionable Recommendations**
- Give 5 specific, practical tips for next posts

Be honest and data-driven.
"""

    try:
        response = llm.invoke(prompt)
        result = response.content if hasattr(response, 'content') else str(response)
    except Exception as e:
        result = f"AI Analysis unavailable: {str(e)}\n\nPlease check your GOOGLE_API_KEY."

    # Save to vector store for chat memory
    doc = Document(
        page_content=result,
        metadata={
            "type": "posts_analysis",
            "timestamp": datetime.now().isoformat()
        }
    )
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    chunks = splitter.split_documents([doc])
    vector_store.add_documents(chunks)

    return result


def get_chat_context():
    """Helper for chat endpoint"""
    retriever = vector_store.as_retriever(search_kwargs={"k": 4})
    return retriever


__all__ = ["analyze_posts", "get_chat_context", "llm", "vector_store"]
