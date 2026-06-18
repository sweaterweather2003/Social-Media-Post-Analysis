import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv()
backend_dir = Path(__file__).resolve().parent

if not os.getenv("GOOGLE_API_KEY"):
    raise ValueError("CRITICAL ERROR: GOOGLE_API_KEY is missing from your .env file!")

# Fixed models
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.3)
embeddings = GoogleGenerativeAIEmbeddings(model="gemini-embedding-2-preview")   # ← Fixed

vector_store = Chroma(
    embedding_function=embeddings, 
    persist_directory=str(backend_dir / "chroma_db_gemini")
)

def analyze_profile(profile_handle: str, focus: str = "growth, best posts, trends, suggestions"):
    search = DuckDuckGoSearchRun()
    
    search_query = f"{profile_handle} instagram OR tiktok OR x OR youtube best reels OR posts OR growth OR trends OR engagement 2026"
    search_results = search.run(search_query)
    
    prompt = f"""
    You are a top social media growth strategist in 2026.

    Profile: {profile_handle}
    Focus: {focus}

    Recent search results:
    {search_results}

    Provide a clear structured response:
    - Key Insights & Metrics
    - Best Performing Content
    - Current Trends
    - 4-5 Actionable Recommendations
    """

    response = llm.invoke(prompt)
    result = response.content if hasattr(response, 'content') else str(response)
    
    # Store
    doc = Document(
        page_content=result,
        metadata={"profile": profile_handle, "type": "profile_analysis", "timestamp": datetime.now().isoformat()}
    )
    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
    chunks = splitter.split_documents([doc])
    vector_store.add_documents(chunks)
    
    return result