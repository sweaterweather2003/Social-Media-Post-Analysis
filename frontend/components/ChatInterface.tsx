'use client';

import { useState } from 'react';
import axios from 'axios';

export default function ChatInterface({ videoA, videoB }: { videoA: any; videoB: any }) {
  const [messages, setMessages] = useState<any[]>([
    { role: 'assistant', content: "Hi! Ask me anything about these two videos." }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  const sendMessage = async () => {
    if (!input.trim()) return;
    
    const userMsg = { role: 'user', content: input };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const res = await axios.post(`${apiUrl}/chat`, {
        message: input,
        video_a_metadata: videoA,
        video_b_metadata: videoB
      });

      setMessages(prev => [...prev, { role: 'assistant', content: res.data.response }]);
    } catch (err) {
      setMessages(prev => [...prev, { role: 'assistant', content: "Sorry, I couldn't process that." }]);
    }
    setLoading(false);
  };

  return (
    <div className="chat-container border border-zinc-700 p-6">
      <div className="flex-1 overflow-auto mb-4 space-y-4" id="chat">
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[80%] p-4 rounded-2xl ${msg.role === 'user' ? 'bg-violet-600' : 'bg-zinc-800'}`}>
              {msg.content}
            </div>
          </div>
        ))}
      </div>

      <div className="flex gap-3">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
          placeholder="Why did Video A perform better?"
          className="flex-1 p-4 bg-zinc-900 border border-zinc-700 rounded-xl focus:outline-none"
        />
        <button
          onClick={sendMessage}
          disabled={loading}
          className="px-8 bg-white text-black font-medium rounded-xl hover:bg-gray-200 disabled:opacity-50"
        >
          Send
        </button>
      </div>
    </div>
  );
}
