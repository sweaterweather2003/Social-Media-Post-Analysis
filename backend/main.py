from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
from rag_engine import analyze_profile, vector_store, llm
import uvicorn
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from extractors import get_instagram_profile_posts

load_dotenv()

app = FastAPI(title="Social Growth OS")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ProfilePayload(BaseModel):
    profile: str
    focus: str = "growth, best performing posts, current trends, improvement suggestions"

class PostsPayload(BaseModel):
    username: str
    platform: str = "Instagram"
    max_posts: int = 12

class ChatPayload(BaseModel):
    question: str
    chat_history: List[Dict[str, str]] = []

@app.post("/api/analyze-profile")
async def analyze(payload: ProfilePayload):
    try:
        result = analyze_profile(payload.profile, payload.focus)
        return {
            "success": True,
            "analysis": result,
            "profile": payload.profile,
            "mode": "profile"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/analyze-posts")
async def analyze_posts(payload: PostsPayload):
    try:
        if payload.platform.lower() == "instagram":
            posts = get_instagram_profile_posts(payload.username, payload.max_posts)
            
            # Enhanced analysis prompt with real post data
            posts_summary = "\n".join([
                f"- {p['title']} | Views: {p['views']} | Likes: {p['likes']} | ER: {p['engagement_rate']}%"
                for p in posts[:8]
            ])

            result = f"""
Top Posts Analysis for @{payload.username} (Instagram):

{posts_summary}

Key Insights:
• Average Engagement Rate: {round(sum(p['engagement_rate'] for p in posts)/len(posts), 2)}%
• Highest Performing Post: {max(posts, key=lambda x: x['engagement_rate'])['title'] if posts else 'N/A'}
            """
            
            # Store in vector DB
            from langchain_core.documents import Document
            from langchain_text_splitters import RecursiveCharacterTextSplitter
            from datetime import datetime

            doc = Document(
                page_content=result,
                metadata={"profile": payload.username, "type": "posts_analysis", "timestamp": datetime.now().isoformat()}
            )
            splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
            chunks = splitter.split_documents([doc])
            vector_store.add_documents(chunks)
            
            return {
                "success": True,
                "posts": posts,
                "analysis": result,
                "username": payload.username,
                "mode": "posts"
            }
        else:
            return {"success": False, "error": "Only Instagram supported for now"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/chat")
async def chat_endpoint(payload: ChatPayload):
    try:
        retriever = vector_store.as_retriever(search_kwargs={"k": 4})
        
        template = """You are an expert social media growth strategist.
        Use the following previous analyses and context to answer the user's question.

        Context:
        {context}

        Question: {question}
        """

        prompt = ChatPromptTemplate.from_template(template)

        chain = (
            {"context": retriever, "question": RunnablePassthrough()}
            | prompt
            | llm
            | StrOutputParser()
        )

        response = chain.invoke(payload.question)
        return {"response": response}
        
    except Exception as e:
        return {"response": f"Sorry, I encountered an error: {str(e)}"}

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
