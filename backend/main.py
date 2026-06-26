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

class ChatPayload(BaseModel):
    question: str
    chat_history: List[Dict[str, str]] = []

@app.post("/api/analyze-profile")
async def analyze(payload: ProfilePayload):
    try:
        result = analyze_profile(payload.profile, payload.focus)
        return {"success": True, "analysis": result, "profile": payload.profile}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/analyze-posts")
async def analyze_posts_endpoint(payload: PostsPayload):
    try:
        result = analyze_posts(payload.shortcodes, payload.focus)
        return {"success": True, "analysis": result, "shortcodes": payload.shortcodes}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/chat")
async def chat_endpoint(payload: ChatPayload):
    try:
        retriever = vector_store.as_retriever(search_kwargs={"k": 4})
        
        template = """You are an expert social media growth strategist.
        Use the following previous analyses and context to answer the user's question naturally.

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
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8001)))
