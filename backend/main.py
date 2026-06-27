from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict
from rag_engine import analyze_profile, analyze_posts, vector_store, llm
import uvicorn
from dotenv import load_dotenv
import os

# LangChain imports
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

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
    shortcodes: List[str]
    focus: str = "engagement comparison, best performing, improvement suggestions"
    post_type: str = "reels"

class ChatPayload(BaseModel):
    question: str
    chat_history: List[Dict[str, str]] = []

# Store user preferences (persistent during server runtime)
user_preferences = {"default": "No special preferences set yet."}

@app.post("/api/analyze-profile")
async def analyze(payload: ProfilePayload):
    try:
        result = analyze_profile(payload.profile, payload.focus)
        return {"success": True, "analysis": result, "profile": payload.profile}
    except Exception as e:
        if "ALL_API_KEYS_EXHAUSTED" in str(e):
            return {"success": False, "error": "All API keys have reached their daily limit. Please try again in about 12 hours."}
        return {"success": False, "error": str(e)}

@app.post("/api/analyze-posts")
async def analyze_posts_endpoint(payload: PostsPayload):
    try:
        result = analyze_posts(payload.shortcodes, payload.focus, payload.post_type)
        return {"success": True, "analysis": result, "shortcodes": payload.shortcodes}
    except Exception as e:
        if "ALL_API_KEYS_EXHAUSTED" in str(e):
            return {"success": False, "error": "All API keys have reached their daily limit. Please try again in about 12 hours."}
        return {"success": False, "error": str(e)}

@app.post("/api/chat")
async def chat_endpoint(payload: ChatPayload):
    try:
        user_id = "default"
        current_prefs = user_preferences.get(user_id, "No special preferences set yet.")

        retriever = vector_store.as_retriever(search_kwargs={"k": 4})
        
        template = """You are an expert social media growth strategist.
        You must strictly follow the user's preferences at all times.

        Current User Preferences / Instructions:
        {preferences}

        Use the following previous analyses and context to answer the user's question naturally.

        Context:
        {context}

        Question: {question}

        Respond in clean, natural English. Follow all user preferences exactly."""

        prompt = ChatPromptTemplate.from_template(template)

        chain = (
            {
                "context": retriever, 
                "question": RunnablePassthrough(),
                "preferences": lambda x: current_prefs
            }
            | prompt
            | llm
            | StrOutputParser()
        )

        response = chain.invoke(payload.question)
        
        # Detect if user is giving new instructions/preferences
        q_lower = payload.question.lower()
        preference_keywords = ["don't", "do not", "never", "always", "stop", "focus on", "only talk about", 
                             "avoid", "ignore", "remember", "from now on", "please don't"]
        
        if any(keyword in q_lower for keyword in preference_keywords):
            user_preferences[user_id] = payload.question
            print(f"✅ Updated user preference: {payload.question}")
            response += "\n\n✅ Got it! I'll remember your preference going forward."

        return {"response": response}
        
    except Exception as e:
        if "ALL_API_KEYS_EXHAUSTED" in str(e):
            return {"response": "⚠️ All API keys have reached their daily limit.\n\nPlease try again in about 12 hours."}
        return {"response": f"Sorry, I encountered an error: {str(e)}"}

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8001)))
