import { useState } from 'react';

export default function ChatApp() {
  const [prompt, setPrompt] = useState('');
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);

  const sendPrompt = async () => {
    if (!prompt.trim()) return;

    const userMsg = { role: 'user', text: prompt };
    setMessages(prev => [...prev, userMsg]);
    setPrompt('');
    setLoading(true);

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: userMsg.text }),
      });

      if (!res.ok || !res.body) {
        throw new Error(`HTTP error: ${res.status}`);
      }

      let botMsg = { role: 'bot', text: '' };
      setMessages(prev => [...prev, botMsg]);

      const reader = res.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        botMsg = { ...botMsg, text: botMsg.text + chunk };
        setMessages(prev => [...prev.slice(0, -1), botMsg]);
      }
    } catch (err) {
      console.error(err);
      setMessages(prev => [
        ...prev.slice(0, -1),
        { role: 'bot', text: `❌ Error: ${err.message}` },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen p-8 bg-[#121212] text-[#e0e0e0] font-sans">
      <div className="max-w-[1200px] mx-auto bg-[#1e1e1e] p-6 rounded-md shadow-md">
        <h1 className="text-2xl text-white mb-4 font-semibold">SYNERGY</h1>

        <div className="h-[300px] overflow-y-auto bg-[#2b2b2b] border border-[#444] rounded-md p-4 mb-4">
          {messages.map((msg, idx) => (
            <div
              key={idx}
              className={`mb-3 whitespace-pre-wrap break-words ${
                msg.role === 'user' ? 'text-blue-300' : 'text-green-300'
              }`}
            >
              <strong>{msg.role === 'user' ? 'You' : 'SYNERGY'}:</strong> {msg.text}
            </div>
          ))}
          {loading && (
            <div className="italic text-gray-400">SYNERGY is typing...</div>
          )}
        </div>

        <textarea
          className="w-full p-3 border border-[#444] rounded resize-y bg-[#1c1c1c] text-white mb-4"
          rows={4}
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="Type your message..."
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              sendPrompt();
            }
          }}
        />

        <button
          className="px-6 py-3 bg-blue-300 text-black font-bold rounded disabled:opacity-50 hover:bg-blue-400 transition"
          onClick={sendPrompt}
          disabled={loading || !prompt.trim()}
        >
          {loading ? 'Thinking...' : 'Send'}
        </button>
      </div>
    </main>
  );
}
