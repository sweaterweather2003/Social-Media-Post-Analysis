// app/api/chat/route.ts
import { StreamingTextResponse } from 'ai';

export async function POST(req: Request) {
  const { messages } = await req.json();

  const latestMessage = messages[messages.length - 1].content;
  const chatHistory = messages.slice(0, -1).map((m: { role: string; content: string }) => ({
    role: m.role,
    content: m.content,
  }));

  // Use environment variable (very important on Render)
  const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

  const response = await fetch(`${backendUrl}/api/chat`, {
    method: 'POST',
    headers: { 
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      question: latestMessage,
      chat_history: chatHistory,
    }),
  });

  if (!response.ok) {
    throw new Error(`Backend error: ${response.status}`);
  }

  if (!response.body) throw new Error("No response body");
  
  return new StreamingTextResponse(response.body);
}
