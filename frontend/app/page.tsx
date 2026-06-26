"use client";

import React, { useState, useRef, useEffect } from "react";
import { useChat } from "ai/react";

const renderCleanConsoleOutput = (text: string) => {
  return text.split("\n").map((line, lineIdx) => {
    let processedLine = line.trim();
    let isBullet = false;

    if (processedLine.startsWith("* ") || processedLine.startsWith("- ")) {
      processedLine = processedLine.replace(/^\s*[*-]\s+/, "");
      isBullet = true;
    }

    const parts = processedLine.split("**");
    const formattedElements = parts.map((part, partIdx) => {
      if (partIdx % 2 !== 0) {
        return <strong key={partIdx} style={{ color: "#34d399" }}>{part}</strong>;
      }
      return part;
    });

    if (isBullet) {
      return (
        <div key={lineIdx} style={{ display: "flex", gap: "8px", paddingLeft: "12px", marginBottom: "6px" }}>
          <span style={{ color: "#34d399" }}>•</span>
          <span>{formattedElements}</span>
        </div>
      );
    }

    return <div key={lineIdx} style={{ marginBottom: "4px" }}>{formattedElements}</div>;
  });
};

export default function Home() {
  const [mode, setMode] = useState<"profile" | "posts">("profile");
  const [igUsername, setIgUsername] = useState("");
  const [xUsername, setxUsername] = useState("");
  const [fbPage, setFbPage] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);
  const [lastAnalysis, setLastAnalysis] = useState<any>(null);
  const [postsData, setPostsData] = useState<any>(null);

  const { messages, input, handleInputChange, handleSubmit, append, isLoading } = useChat({
    api: "/api/chat",
  });

  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  const quickPrompts = [
    "What content performed best across platforms last 30 days?",
    "Suggest 5 ideas for next week's posts to maximize engagement",
    "Analyze top hashtags and trending patterns right now",
    "Give me a full growth strategy for the next 14 days",
    "Compare my Instagram vs X performance",
  ];

  const handleAnalyze = async () => {
    if (mode === "profile") {
      if (!igUsername && !xUsername && !fbPage) {
        alert("Please enter at least one username");
        return;
      }
    } else {
      if (!igUsername) {
        alert("Please enter an Instagram username for posts analysis");
        return;
      }
    }

    setIsProcessing(true);
    setLastAnalysis(null);
    setPostsData(null);

    try {
      if (mode === "profile") {
        const analyses: any[] = [];
        if (igUsername) {
          const res = await fetch("http://localhost:8001/api/analyze-profile", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ profile: igUsername }),
          });
          const data = await res.json();
          analyses.push({ platform: "Instagram", ...data });
        }
        // Add X and FB similarly if needed
        setLastAnalysis(analyses);
      } else {
        const res = await fetch("http://localhost:8001/api/analyze-posts", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ username: igUsername, platform: "Instagram" }),
        });
        const data = await res.json();
        setPostsData(data);
      }

      alert(`✅ Analysis completed!`);
    } catch (error) {
      console.error(error);
      alert("Failed to analyze. Make sure backend is running.");
    }
    setIsProcessing(false);
  };

  return (
    <main style={{ minHeight: "100vh", backgroundColor: "#000000", color: "#ffffff", padding: "24px", fontFamily: "monospace" }}>
      <style dangerouslySetInnerHTML={{__html: `
        .console-scrollbar::-webkit-scrollbar { width: 8px; }
        .console-scrollbar::-webkit-scrollbar-track { background: #000000; }
        .console-scrollbar::-webkit-scrollbar-thumb { background: #3f3f46; }
        .console-scrollbar::-webkit-scrollbar-thumb:hover { background: #71717a; }
        @keyframes botPulse { 0% { opacity: 0.4; } 50% { opacity: 1; } 100% { opacity: 0.4; } }
        .bot-pulse-icon { animation: botPulse 1.5s infinite; }
      `}} />

      <header style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "24px", marginBottom: "32px", border: "2px solid #27272a", backgroundColor: "#09090b" }}>
        <div>
          <h1 style={{ fontSize: "32px", fontWeight: 900, margin: 0 }}>SOCIAL GROWTH OS</h1>
          <p style={{ fontSize: "12px", color: "#a1a1aa", marginTop: "4px" }}>MULTI-PLATFORM AI STRATEGIST</p>
        </div>
        <div style={{ padding: "8px 16px", backgroundColor: "#18181b", border: "1px solid #27272a", fontSize: "12px" }}>
          SYSTEM ONLINE
        </div>
      </header>

      {/* MODE SWITCH */}
      <div style={{ marginBottom: "24px", display: "flex", gap: "12px", justifyContent: "center" }}>
        <button 
          onClick={() => setMode("profile")}
          style={{ 
            padding: "10px 24px", 
            background: mode === "profile" ? "#fff" : "#18181b", 
            color: mode === "profile" ? "#000" : "#fff",
            border: "1px solid #27272a",
            fontWeight: "bold"
          }}
        >
          Compare Accounts (Cross-Platform)
        </button>
        <button 
          onClick={() => setMode("posts")}
          style={{ 
            padding: "10px 24px", 
            background: mode === "posts" ? "#fff" : "#18181b", 
            color: mode === "posts" ? "#000" : "#fff",
            border: "1px solid #27272a",
            fontWeight: "bold"
          }}
        >
          Analyze Posts Engagement (Single Account)
        </button>
      </div>

      {/* INPUT SECTION */}
      <section style={{ border: "2px solid #27272a", padding: "24px", marginBottom: "32px", backgroundColor: "#09090b" }}>
        <h2 style={{ fontSize: "20px", fontWeight: 900, marginBottom: "20px" }}>
          {mode === "profile" ? "🔍 MULTI-PLATFORM ANALYSIS" : "📊 POSTS ENGAGEMENT ANALYSIS"}
        </h2>
        
        {mode === "profile" ? (
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))", gap: "20px" }}>
            <div>
              <label style={{ display: "block", fontSize: "11px", color: "#a1a1aa", marginBottom: "8px" }}>INSTAGRAM USERNAME</label>
              <input type="text" placeholder="@yourhandle" value={igUsername} onChange={(e) => setIgUsername(e.target.value)} style={{ width: "100%", padding: "14px", background: "#000", border: "1px solid #27272a", color: "white" }} />
            </div>
            <div>
              <label style={{ display: "block", fontSize: "11px", color: "#a1a1aa", marginBottom: "8px" }}>X / TWITTER USERNAME</label>
              <input type="text" placeholder="@yourhandle" value={xUsername} onChange={(e) => setxUsername(e.target.value)} style={{ width: "100%", padding: "14px", background: "#000", border: "1px solid #27272a", color: "white" }} />
            </div>
            <div>
              <label style={{ display: "block", fontSize: "11px", color: "#a1a1aa", marginBottom: "8px" }}>FACEBOOK PAGE NAME</label>
              <input type="text" placeholder="YourPageName" value={fbPage} onChange={(e) => setFbPage(e.target.value)} style={{ width: "100%", padding: "14px", background: "#000", border: "1px solid #27272a", color: "white" }} />
            </div>
          </div>
        ) : (
          <div>
            <label style={{ display: "block", fontSize: "11px", color: "#a1a1aa", marginBottom: "8px" }}>INSTAGRAM USERNAME (@)</label>
            <input type="text" placeholder="@yourhandle" value={igUsername} onChange={(e) => setIgUsername(e.target.value)} style={{ width: "100%", padding: "14px", background: "#000", border: "1px solid #27272a", color: "white" }} />
          </div>
        )}

        <button onClick={handleAnalyze} disabled={isProcessing} style={{ marginTop: "20px", padding: "14px 32px", background: "#fff", color: "#000", fontWeight: "bold", border: "none" }}>
          {isProcessing ? "ANALYZING..." : mode === "profile" ? "ANALYZE ALL ACCOUNTS" : "ANALYZE POSTS"}
        </button>
      </section>

      {/* RESULTS */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "32px" }}>
        <section style={{ border: "2px solid #27272a", padding: "24px", backgroundColor: "#09090b", maxHeight: "720px", overflowY: "auto" }}>
          <h2 style={{ fontSize: "20px", marginBottom: "20px" }}>📈 ANALYSIS RESULTS</h2>
          {mode === "posts" && postsData ? (
            <div>
              <h3>Top Posts from @{postsData.username}</h3>
              {postsData.posts?.map((post: any, i: number) => (
                <div key={i} style={{ border: "1px solid #27272a", padding: "12px", marginBottom: "12px" }}>
                  <div><strong>{post.title}</strong></div>
                  <div style={{ fontSize: "12px", color: "#a1a1aa" }}>
                    Views: {post.views} | Likes: {post.likes} | Comments: {post.comments} | ER: {post.engagement_rate}%
                  </div>
                </div>
              ))}
            </div>
          ) : lastAnalysis ? (
            lastAnalysis.map((item: any, index: number) => (
              <div key={index} style={{ marginBottom: "20px", padding: "12px", border: "1px solid #27272a" }}>
                <strong>{item.platform}:</strong>
                <div style={{ marginTop: "8px", color: "#a1a1aa", whiteSpace: "pre-wrap" }}>
                  {item.analysis?.substring(0, 400) + "..."}
                </div>
              </div>
            ))
          ) : (
            <div style={{ color: "#52525b", padding: "60px 0", textAlign: "center" }}>
              Select mode and enter username(s) to analyze
            </div>
          )}
        </section>

        {/* Chat remains the same */}
        <section style={{ border: "2px solid #27272a", backgroundColor: "#09090b", height: "720px", display: "flex", flexDirection: "column" }}>
          {/* ... Chat UI stays exactly the same as before ... */}
          <div style={{ padding: "16px 20px", borderBottom: "1px solid #27272a", backgroundColor: "#000" }}>
            <span style={{ fontWeight: "bold" }}>💡 GROWTH STRATEGIST CHAT</span>
          </div>

          <div className="console-scrollbar" style={{ flex: 1, overflowY: "auto", padding: "20px", display: "flex", flexDirection: "column", gap: "16px" }}>
            {messages.length === 0 && (
              <div style={{ padding: "20px", border: "1px solid #27272a" }}>
                <p style={{ color: "#a1a1aa" }}>
                  Hello! I'm your AI Social Growth Strategist.<br />
                  Analyze your accounts or posts first, then ask me anything.
                </p>
              </div>
            )}
            
            {messages.map((message) => (
              <div key={message.id} style={{ padding: "16px", border: "1px solid #27272a", backgroundColor: message.role === "user" ? "#18181b" : "#09090b" }}>
                <div style={{ fontSize: "10px", color: "#71717a", marginBottom: "8px" }}>
                  {message.role === "user" ? "YOU" : "STRATEGIST"}
                </div>
                <div style={{ fontSize: "13px", lineHeight: "1.6" }}>
                  {renderCleanConsoleOutput(message.content)}
                </div>
              </div>
            ))}

            {isLoading && (
              <div style={{ padding: "16px", border: "1px dashed #3f3f46" }}>
                <span className="bot-pulse-icon" style={{ marginRight: "8px" }}>🤖</span> 
                Researching latest trends...
              </div>
            )}
            <div ref={chatEndRef} />
          </div>

          <form onSubmit={handleSubmit} style={{ padding: "16px", borderTop: "1px solid #27272a", display: "flex", gap: "8px" }}>
            <input type="text" value={input} onChange={handleInputChange} placeholder="Ask anything..." style={{ flex: 1, padding: "12px", background: "#000", border: "1px solid #27272a", color: "white" }} />
            <button type="submit" style={{ padding: "0 24px", background: "#fff", color: "#000", fontWeight: "bold" }}>SEND</button>
          </form>
        </section>
      </div>
    </main>
  );
}
