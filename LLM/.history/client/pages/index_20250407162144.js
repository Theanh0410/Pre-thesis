import { useState } from 'react';

export default function Home() {
  const [prompt, setPrompt] = useState('');
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);

  const sendPrompt = async () => {
    if (!prompt.trim()) return;

    const userMsg = { role: 'user', text: prompt };
    setMessages([...messages, userMsg]);
    setPrompt('');
    setLoading(true);

    const res = await fetch('http://localhost:5000/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt: userMsg.text }),
    });

    const reader = res.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let botMsg = { role: 'bot', text: '' };

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      const chunk = decoder.decode(value);
      botMsg.text += chunk;
      setMessages(prev => [...prev.slice(0, -1), botMsg]);
    }

    setMessages(prev => [...prev, botMsg]);
    setLoading(false);
  };

  return (
    <main style={{ padding: '2rem', fontFamily: 'sans-serif', background: '#f5f5f5', minHeight: '100vh' }}>
      <div style={{ maxWidth: '700px', margin: 'auto', background: 'white', padding: '1.5rem', borderRadius: '0.5rem', boxShadow: '0 0 10px rgba(0,0,0,0.1)' }}>
        <h1 style={{ fontSize: '1.5rem', marginBottom: '1rem' }}>💬 Chat with LLaMA 3.2</h1>
        <div style={{ height: '320px', overflowY: 'auto', border: '1px solid #ccc', padding: '1rem', borderRadius: '0.25rem', background: '#fafafa', marginBottom: '1rem' }}>
          {messages.map((msg, idx) => (
            <div key={idx} style={{ marginBottom: '0.75rem', color: msg.role === 'user' ? '#1a73e8' : '#0f9d58' }}>
              <strong>{msg.role === 'user' ? 'You' : 'LLaMA'}:</strong> {msg.text}
            </div>
          ))}
        </div>
        <textarea
          rows={4}
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          style={{ width: '100%', padding: '0.75rem', borderRadius: '0.25rem', border: '1px solid #ccc', marginBottom: '0.75rem' }}
          placeholder="Type your message..."
        />
        <button
          onClick={sendPrompt}
          disabled={loading}
          style={{ backgroundColor: '#1a73e8', color: 'white', padding: '0.75rem 1.5rem', border: 'none', borderRadius: '0.25rem', cursor: 'pointer' }}
        >
          {loading ? 'Thinking...' : 'Send'}
        </button>
      </div>
    </main>
  );
}