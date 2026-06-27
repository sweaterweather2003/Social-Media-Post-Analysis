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
  const [igUsername, setIgUsername] = useState("");
  const [xUsername, setxUsername] = useState("");
  const [fbPage, setFbPage] = useState("");
  const [postInput, setPostInput] = useState("");
  const [mode, setMode] = useState<"accounts" | "posts">("accounts");
  const [postType, setPostType] = useState<"reels" | "all">("reels");
  const [isProcessing, setIsProcessing] = useState(false);
  const [lastAnalysis, setLastAnalysis] = useState<any>(null);

  const { messages, input, handleInputChange, handleSubmit, append, isLoading } = useChat({
    api: "/api/chat",
  });

  const chatEndRef = useRef<HTMLDivElement>(null);
  const hasInteracted = useRef(false); // Prevents auto-scroll on initial load

  useEffect(() => {
    // Only scroll if user has interacted with chat or there are messages
    if (hasInteracted.current || messages.length > 0 || isLoading) {
      chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, isLoading]);

  const quickPrompts = [
    "What content performed best across platforms last 30 days?",
    "Suggest 5 ideas for next week's posts to maximize engagement",
    "Analyze top hashtags and trending patterns right now",
    "Give me a full growth strategy for the next 14 days",
    "Compare my Instagram vs x performance",
  ];

  const extractShortcode = (input: string): string[] => {
    return input.split(',').map(item => {
      const trimmed = item.trim();
      if (!trimmed) return null;
      const urlMatch = trimmed.match(/instagram\.com\/(?:reel|p)\/([A-Za-z0-9_-]+)/);
      if (urlMatch && urlMatch[1]) return urlMatch[1];
      return trimmed;
    }).filter(Boolean) as string[];
  };

  const handleAnalyzeAccounts = async () => {
    if (!igUsername && !xUsername && !fbPage) {
      alert("Please enter at least one username or page name");
      return;
    }

    setIsProcessing(true);
    const analyses: any[] = [];

    try {
      if (igUsername) {
        const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/analyze-profile`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ 
            profile: igUsername, 
            focus: "growth, best performing posts, current trends, improvement suggestions" 
          }),
        });
        const data = await res.json();
        analyses.push({ platform: "Instagram", ...data });
      }
      if (xUsername) {
        const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/analyze-profile`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ 
            profile: xUsername, 
            focus: "growth, best performing posts, current trends, improvement suggestions" 
          }),
        });
        const data = await res.json();
        analyses.push({ platform: "x/X", ...data });
      }
      if (fbPage) {
        const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/analyze-profile`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ 
            profile: fbPage, 
            focus: "growth, best performing posts, current trends, improvement suggestions" 
          }),
        });
        const data = await res.json();
        analyses.push({ platform: "Facebook", ...data });
      }

      setLastAnalysis(analyses);
      alert(`✅ Analysis completed for ${analyses.length} profile(s)!`);
      
      if (analyses.length > 0) {
        append({ role: "user", content: `Here is the analysis for ${igUsername || xUsername || fbPage}` });
      }
    } catch (error) {
      console.error(error);
      alert("Failed to analyze accounts. Make sure backend is running.");
    }
    setIsProcessing(false);
  };

  const handleAnalyzePosts = async () => {
    if (!postInput.trim()) {
      alert("Please enter at least one Instagram post URL or shortcode");
      return;
    }

    setIsProcessing(true);
    const shortcodeList = extractShortcode(postInput);

    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/analyze-posts`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          shortcodes: shortcodeList,
          focus: "engagement comparison, best performing, improvement suggestions",
          post_type: postType
        }),
      });
      
      const data = await res.json();
      
      setLastAnalysis([{ 
        platform: `Instagram ${postType === "reels" ? "Reels" : "Posts"}`, 
        ...data 
      }]);
      
      alert(`✅ Analyzed ${shortcodeList.length} ${postType === "reels" ? "Reels" : "Posts"}!`);
      
      if (data.success) {
        append({ 
          role: "user", 
          content: `Here is the analysis for ${postType === "reels" ? "Reels" : "Posts"}: ${shortcodeList.join(", ")}` 
        });
      }
    } catch (error) {
      console.error(error);
      alert("Failed to analyze posts. Make sure backend is running.");
    }
    setIsProcessing(false);
  };

  const handleSubmitWithInteraction = (e: React.FormEvent) => {
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
          <h1 style={{ fontSize: "32px", fontWeight: 900, margin: 0 }}>SOCIAL GROWTH OS</h1>
          <p style={{ fontSize: "12px", color: "#a1a1aa", marginTop: "4px" }}>MULTI-PLATFORM AI STRATEGIST</p>
        </div>
        <div style={{ padding: "8px 16px", backgroundColor: "#18181b", border: "1px solid #27272a", fontSize: "12px" }}>
          SYSTEM ONLINE
        </div>
      </header>

      {/* Analysis Mode Toggle */}
      <section style={{ border: "2px solid #27272a", padding: "24px", marginBottom: "32px", backgroundColor: "#09090b" }}>
        <div style={{ display: "flex", gap: "12px", marginBottom: "20px", borderBottom: "1px solid #27272a", paddingBottom: "16px" }}>
          <button
            onClick={() => setMode("accounts")}
            style={{
              padding: "10px 24px",
              background: mode === "accounts" ? "#fff" : "#18181b",
              color: mode === "accounts" ? "#000" : "#fff",
              border: "1px solid #27272a",
              fontWeight: "bold",
              borderRadius: "6px"
            }}
          >
            📊 Compare Accounts
          </button>
          <button
            onClick={() => setMode("posts")}
            style={{
              padding: "10px 24px",
              background: mode === "posts" ? "#fff" : "#18181b",
              color: mode === "posts" ? "#000" : "#fff",
              border: "1px solid #27272a",
              fontWeight: "bold",
              borderRadius: "6px"
            }}
          >
            📍 Compare Instagram Posts
          </button>
        </div>

        <h2 style={{ fontSize: "20px", fontWeight: 900, marginBottom: "20px" }}>
          {mode === "accounts" ? "🔍 MULTI-PLATFORM ACCOUNT ANALYSIS" : "📍 INSTAGRAM POST COMPARISON"}
        </h2>
        
        {mode === "accounts" ? (
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))", gap: "20px" }}>
            <div>
              <label style={{ display: "block", fontSize: "11px", color: "#a1a1aa", marginBottom: "8px" }}>INSTAGRAM USERNAME</label>
              <input type="text" placeholder="@yourhandle" value={igUsername} onChange={(e) => setIgUsername(e.target.value)} style={{ width: "100%", padding: "14px", background: "#000", border: "1px solid #27272a", color: "white" }} />
            </div>
            <div>
              <label style={{ display: "block", fontSize: "11px", color: "#a1a1aa", marginBottom: "8px" }}>x / TWITTER USERNAME</label>
              <input type="text" placeholder="@yourhandle" value={xUsername} onChange={(e) => setxUsername(e.target.value)} style={{ width: "100%", padding: "14px", background: "#000", border: "1px solid #27272a", color: "white" }} />
            </div>
            <div>
              <label style={{ display: "block", fontSize: "11px", color: "#a1a1aa", marginBottom: "8px" }}>FACEBOOK PAGE NAME</label>
              <input type="text" placeholder="YourPageName" value={fbPage} onChange={(e) => setFbPage(e.target.value)} style={{ width: "100%", padding: "14px", background: "#000", border: "1px solid #27272a", color: "white" }} />
            </div>
          </div>
        ) : (
          <div>
            <label style={{ display: "block", fontSize: "11px", color: "#a1a1aa", marginBottom: "8px" }}>POST TYPE</label>
            <div style={{ display: "flex", gap: "10px", marginBottom: "16px" }}>
              <button 
                onClick={() => setPostType("reels")} 
                style={{ 
                  padding: "8px 20px", 
                  background: postType === "reels" ? "#fff" : "#18181b", 
                  color: postType === "reels" ? "#000" : "#fff", 
                  border: "1px solid #27272a", 
                  borderRadius: "6px" 
                }}
              >
                🎥 Reels Only
              </button>
              <button 
                onClick={() => setPostType("all")} 
                style={{ 
                  padding: "8px 20px", 
                  background: postType === "all" ? "#fff" : "#18181b", 
                  color: postType === "all" ? "#000" : "#fff", 
                  border: "1px solid #27272a", 
                  borderRadius: "6px" 
                }}
              >
                📸 All Posts
              </button>
            </div>

            <label style={{ display: "block", fontSize: "11px", color: "#a1a1aa", marginBottom: "8px" }}>
              INSTAGRAM POST URLS OR SHORTCODES (comma separated)
            </label>
            <input
              type="text"
              placeholder="https://www.instagram.com/reel/DZNdBTogxVy/ or DZNdBTogxVy"
              value={postInput}
              onChange={(e) => setPostInput(e.target.value)}
              style={{ width: "100%", padding: "14px", background: "#000", border: "1px solid #27272a", color: "white", marginBottom: "12px" }}
            />
            <p style={{ fontSize: "12px", color: "#a1a1aa" }}>
              You can paste full URLs or shortcodes.
            </p>
          </div>
        )}

        <button
          onClick={mode === "accounts" ? handleAnalyzeAccounts : handleAnalyzePosts}
          disabled={isProcessing || (mode === "accounts" ? (!igUsername && !xUsername && !fbPage) : !postInput.trim())}
          style={{ marginTop: "20px", padding: "14px 32px", background: "#fff", color: "#000", fontWeight: "bold", border: "none" }}
        >
          {isProcessing ? "ANALYZING..." : mode === "accounts" ? "ANALYZE ALL ACCOUNTS" : `COMPARE ${postType === "reels" ? "REELS" : "POSTS"}`}
        </button>
      </section>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "32px" }}>
        <section style={{ border: "2px solid #27272a", padding: "24px", backgroundColor: "#09090b" }}>
          <h2 style={{ fontSize: "20px", marginBottom: "20px" }}>📈 LATEST ANALYSIS</h2>
          {lastAnalysis ? (
            <div style={{ fontSize: "13px", maxHeight: "600px", overflowY: "auto" }}>
              {lastAnalysis.map((item: any, index: number) => (
                <div key={index} style={{ marginBottom: "20px", padding: "12px", border: "1px solid #27272a" }}>
                  <strong>{item.platform}:</strong>
                  <div style={{ marginTop: "8px", color: "#a1a1aa", whiteSpace: "pre-wrap" }}>
                    {item.analysis ? item.analysis.substring(0, 400) + "..." : "Analysis completed"}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div style={{ color: "#52525b", padding: "60px 0", textAlign: "center" }}>
              Select mode and enter data above
            </div>
          )}
        </section>

        <section style={{ border: "2px solid #27272a", backgroundColor: "#09090b", height: "720px", display: "flex", flexDirection: "column" }}>
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
              placeholder="Ask anything about performance, trends, or strategy..."
              style={{ flex: 1, padding: "12px", background: "#000", border: "1px solid #27272a", color: "white" }}
            />
            <button type="submit" style={{ padding: "0 24px", background: "#fff", color: "#000", fontWeight: "bold" }}>
              SEND
            </button>
          </form>
        </section>
      </div>

      <div style={{ marginTop: "32px", border: "2px solid #27272a", padding: "20px", backgroundColor: "#09090b" }}>
        <h3 style={{ marginBottom: "12px", fontSize: "14px" }}>QUICK INSIGHTS</h3>
        <div style={{ display: "flex", flexWrap: "wrap", gap: "10px" }}>
          {quickPrompts.map((prompt, i) => (
            <button
              key={i}
              onClick={() => append({ role: "user", content: prompt })}
              style={{ padding: "10px 16px", background: "#18181b", border: "1px solid #27272a", fontSize: "13px", cursor: "pointer" }}
            >
              {prompt}
            </button>
          ))}
        </div>
      </div>
    </main>
  );
}
