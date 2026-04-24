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
      const res = await fetch('http://localhost:5000/api/chat', {
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
        { role: 'bot', text: `❌ Error: ${err.message}` }
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main style={styles.main}>
      <div style={styles.container}>
        <h1 style={styles.title}>💬 Chat with LLaMA 3.2</h1>

        <div style={styles.chatWindow}>
          {messages.map((msg, idx) => (
            <div key={idx} style={{ ...styles.message, color: msg.role === 'user' ? '#1a73e8' : '#0f9d58' }}>
              <strong>{msg.role === 'user' ? 'You' : 'LLaMA'}:</strong> {msg.text}
            </div>
          ))}
          {loading && <div style={styles.typing}>LLaMA is typing...</div>}
        </div>

        <textarea
          style={styles.input}
          rows={4}
          value={prompt}
          onChange={e => setPrompt(e.target.value)}
          placeholder="Type your message..."
          onKeyDown={e => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              sendPrompt();
            }
          }}
        />

        <button
          style={styles.button}
          onClick={sendPrompt}
          disabled={loading || !prompt.trim()}
        >
          {loading ? 'Thinking...' : 'Send'}
        </button>
      </div>
    </main>
  );
}

const styles = {
  main: {
    padding: '2rem',
    background: '#f0f0f0',
    fontFamily: 'Arial, sans-serif',
    minHeight: '100vh'
  },
  container: {
    maxWidth: '700px',
    margin: 'auto',
    background: 'white',
    padding: '1.5rem',
    borderRadius: '0.5rem',
    boxShadow: '0 0 10px rgba(0,0,0,0.1)'
  },
  title: {
    fontSize: '1.5rem',
    marginBottom: '1rem'
  },
  chatWindow: {
    height: '300px',
    overflowY: 'auto',
    background: '#fafafa',
    border: '1px solid #ccc',
    borderRadius: '5px',
    padding: '1rem',
    marginBottom: '1rem'
  },
  message: {
    marginBottom: '0.75rem',
    whiteSpace: 'pre-wrap',
    wordBreak: 'break-word'
  },
  typing: {
    fontStyle: 'italic',
    color: '#888'
  },
  input: {
    width: '100%',
    padding: '0.75rem',
    border: '1px solid #ccc',
    borderRadius: '4px',
    resize: 'vertical',
    marginBottom: '1rem'
  },
  button: {
    padding: '0.75rem 1.5rem',
    backgroundColor: '#1a73e8',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer'
  }
};
