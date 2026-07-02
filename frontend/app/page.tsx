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
  const [postInput, setPostInput] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);
  const [lastAnalysis, setLastAnalysis] = useState<any>(null);

  const { messages, input, handleInputChange, handleSubmit, append, isLoading } = useChat({
    api: "/api/chat",
  });

  const chatSectionRef = useRef<HTMLDivElement>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);
  const hasInteracted = useRef(false);

  useEffect(() => {
    if (hasInteracted.current || messages.length > 0 || isLoading) {
      chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, isLoading]);

  const extractUrls = (input: string): string[] => {
    return input.split(',').map(item => item.trim()).filter(Boolean);
  };

  const handleAnalyzePosts = async () => {
    if (!postInput.trim()) {
      alert("Please enter at least one Instagram post URL");
      return;
    }

    setIsProcessing(true);
    const postUrls = extractUrls(postInput);

    try {
      const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';
      
      const res = await fetch(`${backendUrl}/api/analyze-posts`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          post_urls: postUrls,
        }),
      });
      
      const data = await res.json();
      
      if (data.success) {
        setLastAnalysis(data);
        alert(`✅ Successfully analyzed ${postUrls.length} post(s)!`);
        
        setTimeout(() => {
          chatSectionRef.current?.scrollIntoView({ behavior: "smooth" });
        }, 300);

        append({ 
          role: "user", 
          content: `Analyze these Instagram posts: ${postUrls.join(", ")}` 
        });
      } else {
        alert("Analysis failed: " + data.error);
      }
    } catch (error) {
      console.error(error);
      alert("Failed to connect to backend. Make sure the FastAPI server is running on port 8001.");
    }
    setIsProcessing(false);
  };

  const handleSubmitWithInteraction = (e: React.FormEvent<HTMLFormElement>) => {
    hasInteracted.current = true;
    handleSubmit(e);
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
          <h1 style={{ fontSize: "32px", fontWeight: 900, margin: 0 }}>INSTAGRAM GROWTH OS</h1>
          <p style={{ fontSize: "12px", color: "#a1a1aa", marginTop: "4px" }}>Apify + AI Powered Engagement Analyzer</p>
        </div>
        <div style={{ padding: "8px 16px", backgroundColor: "#18181b", border: "1px solid #27272a", fontSize: "12px" }}>
          SYSTEM ONLINE
        </div>
      </header>

      <section style={{ border: "2px solid #27272a", padding: "24px", marginBottom: "32px", backgroundColor: "#09090b" }}>
        <h2 style={{ fontSize: "20px", fontWeight: 900, marginBottom: "20px" }}>📍 INSTAGRAM POST ANALYSIS</h2>
        
        <label style={{ display: "block", fontSize: "11px", color: "#a1a1aa", marginBottom: "8px" }}>
          INSTAGRAM POST URLS (comma separated)
        </label>
        <input
          type="text"
          placeholder="https://www.instagram.com/p/DZ7TD3tDIEd/, https://www.instagram.com/p/DZffvjhj503/"
          value={postInput}
          onChange={(e) => setPostInput(e.target.value)}
          style={{ width: "100%", padding: "14px", background: "#000", border: "1px solid #27272a", color: "white", marginBottom: "12px" }}
        />
        <p style={{ fontSize: "12px", color: "#a1a1aa" }}>
          Paste full Instagram post URLs. Multiple URLs supported.
        </p>

        <button
          onClick={handleAnalyzePosts}
          disabled={isProcessing || !postInput.trim()}
          style={{ marginTop: "20px", padding: "14px 32px", background: "#fff", color: "#000", fontWeight: "bold", border: "none" }}
        >
          {isProcessing ? "ANALYZING WITH APIFY..." : "ANALYZE POSTS"}
        </button>
      </section>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "32px" }}>
        <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
          <section style={{ border: "2px solid #27272a", padding: "24px", backgroundColor: "#09090b" }}>
            <h2 style={{ fontSize: "20px", marginBottom: "20px" }}>📈 LATEST ANALYSIS</h2>
            {lastAnalysis ? (
              <div style={{ fontSize: "13px", maxHeight: "500px", overflowY: "auto" }}>
                <div style={{ padding: "12px", border: "1px solid #27272a", marginBottom: "16px" }}>
                  <strong>Summary:</strong><br />
                  Total Posts: {lastAnalysis.summary?.total_posts}<br />
                  Avg Likes: {lastAnalysis.summary?.avg_likes}<br />
                  Avg Comments: {lastAnalysis.summary?.avg_comments}
                </div>

                {/* Charts */}
                <div>
                  <h3 style={{ marginBottom: "12px" }}>📊 Generated Charts</h3>
                  <img 
                    src="http://localhost:8001/engagement_trend.png" 
                    alt="Engagement Trend" 
                    style={{ width: "100%", border: "1px solid #27272a", marginBottom: "12px" }}
                    onError={(e) => { e.currentTarget.style.display = 'none'; }}
                  />
                  <img 
                    src="http://localhost:8001/top_posts.png" 
                    alt="Top Posts" 
                    style={{ width: "100%", border: "1px solid #27272a" }}
                    onError={(e) => { e.currentTarget.style.display = 'none'; }}
                  />
                </div>
              </div>
            ) : (
              <div style={{ color: "#52525b", padding: "60px 0", textAlign: "center" }}>
                Enter post URLs above to begin analysis
              </div>
            )}
          </section>
        </div>

        <section ref={chatSectionRef} style={{ border: "2px solid #27272a", backgroundColor: "#09090b", height: "720px", display: "flex", flexDirection: "column" }}>
          <div style={{ padding: "16px 20px", borderBottom: "1px solid #27272a", backgroundColor: "#000" }}>
            <span style={{ fontWeight: "bold" }}>💡 GROWTH STRATEGIST CHAT</span>
          </div>

          <div className="console-scrollbar" style={{ flex: 1, overflowY: "auto", padding: "20px", display: "flex", flexDirection: "column", gap: "16px" }}>
            {messages.length === 0 && (
              <div style={{ padding: "20px", border: "1px solid #27272a" }}>
                <p style={{ color: "#a1a1aa" }}>
                  Hello! I'm your AI Social Growth Strategist.<br />
                  Analyze posts first, then ask me anything.
                </p>
              </div>
            )}
            
            {messages.map((message) => (
              <div
                key={message.id}
                style={{
                  padding: "16px",
                  border: "1px solid #27272a",
                  backgroundColor: message.role === "user" ? "#18181b" : "#09090b"
                }}
              >
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

          <form onSubmit={handleSubmitWithInteraction} style={{ padding: "16px", borderTop: "1px solid #27272a", display: "flex", gap: "8px" }}>
            <input
              type="text"
              value={input}
              onChange={handleInputChange}
              placeholder="Why did one post perform better? What should I post next?"
              style={{ flex: 1, padding: "12px", background: "#000", border: "1px solid #27272a", color: "white" }}
            />
            <button type="submit" style={{ padding: "0 24px", background: "#fff", color: "#000", fontWeight: "bold" }}>
              SEND
            </button>
          </form>
        </section>
      </div>
    </main>
  );
}
