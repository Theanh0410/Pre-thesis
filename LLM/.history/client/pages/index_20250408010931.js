// import { useState } from 'react';

// export default function ChatApp() {
//   const [prompt, setPrompt] = useState('');
//   const [messages, setMessages] = useState([]);
//   const [loading, setLoading] = useState(false);

//   const sendPrompt = async () => {
//     if (!prompt.trim()) return;

//     const userMsg = { role: 'user', text: prompt };
//     setMessages(prev => [...prev, userMsg]);
//     setPrompt('');
//     setLoading(true);

//     try {
//       const res = await fetch('/api/chat', {
//         method: 'POST',
//         headers: { 'Content-Type': 'application/json' },
//         body: JSON.stringify({ prompt: userMsg.text }),
//       });      

//       if (!res.ok || !res.body) {
//         throw new Error(`HTTP error: ${res.status}`);
//       }

//       let botMsg = { role: 'bot', text: '' };
//       setMessages(prev => [...prev, botMsg]);

//       const reader = res.body.getReader();
//       const decoder = new TextDecoder();

//       while (true) {
//         const { done, value } = await reader.read();
//         if (done) break;

//         const chunk = decoder.decode(value);
//         botMsg = { ...botMsg, text: botMsg.text + chunk };
//         setMessages(prev => [...prev.slice(0, -1), botMsg]);
//       }

//     } catch (err) {
//       console.error(err);
//       setMessages(prev => [
//         ...prev.slice(0, -1),
//         { role: 'bot', text: `❌ Error: ${err.message}` }
//       ]);
//     } finally {
//       setLoading(false);
//     }
//   };

//   return (
//     <main style={styles.main}>
//       <div style={styles.container}>
//         <h1 style={styles.title}>🌓 Chat with LLaMA 3.2</h1>

//         <div style={styles.chatWindow}>
//           {messages.map((msg, idx) => (
//             <div key={idx} style={{
//               ...styles.message,
//               color: msg.role === 'user' ? '#8ab4f8' : '#81c995'
//             }}>
//               <strong>{msg.role === 'user' ? 'You' : 'LLaMA'}:</strong> {msg.text}
//             </div>
//           ))}
//           {loading && <div style={styles.typing}>LLaMA is typing...</div>}
//         </div>

//         <textarea
//           style={styles.input}
//           rows={4}
//           value={prompt}
//           onChange={e => setPrompt(e.target.value)}
//           placeholder="Type your message..."
//           onKeyDown={e => {
//             if (e.key === 'Enter' && !e.shiftKey) {
//               e.preventDefault();
//               sendPrompt();
//             }
//           }}
//         />

//         <button
//           style={styles.button}
//           onClick={sendPrompt}
//           disabled={loading || !prompt.trim()}
//         >
//           {loading ? 'Thinking...' : 'Send'}
//         </button>
//       </div>
//     </main>
//   );
// }

// const styles = {
//   main: {
//     padding: '2rem',
//     background: '#121212',
//     fontFamily: 'Arial, sans-serif',
//     minHeight: '100vh',
//     color: '#e0e0e0'
//   },
//   container: {
//     maxWidth: '700px',
//     margin: 'auto',
//     background: '#1e1e1e',
//     padding: '1.5rem',
//     borderRadius: '0.5rem',
//     boxShadow: '0 0 10px rgba(0,0,0,0.3)'
//   },
//   title: {
//     fontSize: '1.5rem',
//     marginBottom: '1rem',
//     color: '#fff'
//   },
//   chatWindow: {
//     height: '300px',
//     overflowY: 'auto',
//     background: '#2b2b2b',
//     border: '1px solid #444',
//     borderRadius: '5px',
//     padding: '1rem',
//     marginBottom: '1rem'
//   },
//   message: {
//     marginBottom: '0.75rem',
//     whiteSpace: 'pre-wrap',
//     wordBreak: 'break-word'
//   },
//   typing: {
//     fontStyle: 'italic',
//     color: '#aaa'
//   },
//   input: {
//     width: '100%',
//     padding: '0.75rem',
//     border: '1px solid #444',
//     borderRadius: '4px',
//     resize: 'vertical',
//     backgroundColor: '#1c1c1c',
//     color: '#f5f5f5',
//     marginBottom: '1rem'
//   },
//   button: {
//     padding: '0.75rem 1.5rem',
//     backgroundColor: '#8ab4f8',
//     color: '#1a1a1a',
//     fontWeight: 'bold',
//     border: 'none',
//     borderRadius: '4px',
//     cursor: 'pointer'
//   }
// };


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
        { role: 'bot', text: `❌ Error: ${err.message}` }
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main style={styles.main}>
      <div style={styles.container}>
        <div style={styles.layout}>
          {/* Left sidebar for conversation history */}
          <div style={styles.sidebar}>
            <h2 style={styles.sidebarTitle}>Conversation History</h2>
            <div style={styles.historyList}>
              {/* Placeholder for history items */}
              <div style={styles.historyItem}>Today's chat</div>
              <div style={styles.historyItem}>Yesterday</div>
              <div style={styles.historyItem}>Last week</div>
            </div>
          </div>
          
          {/* Right main content for chat */}
          <div style={styles.mainContent}>
            <h1 style={styles.title}>🌓 Chat with LLaMA 3.2</h1>

            <div style={styles.chatWindow}>
              {messages.map((msg, idx) => (
                <div key={idx} style={{
                  ...styles.message,
                  color: msg.role === 'user' ? '#8ab4f8' : '#81c995'
                }}>
                  <strong>{msg.role === 'user' ? 'You' : 'SYNERGY'}:</strong> {msg.text}
                </div>
              ))}
              {loading && <div style={styles.typing}>SYNERGY is typing...</div>}
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
        </div>
      </div>
    </main>
  );
}

const styles = {
  main: {
    padding: '2rem',
    background: '#121212',
    fontFamily: 'Arial, sans-serif',
    minHeight: '100vh',
    color: '#e0e0e0',
    fontSize: '16px' // Increased base font size
  },
  container: {
    maxWidth: '1200px', // Wider container
    margin: 'auto',
    background: '#1e1e1e',
    borderRadius: '0.5rem',
    boxShadow: '0 0 10px rgba(0,0,0,0.3)',
    overflow: 'hidden'
  },
  layout: {
    display: 'flex',
    minHeight: '600px'
  },
  sidebar: {
    width: '25%',
    background: '#252525',
    padding: '1.5rem',
    borderRight: '1px solid #444'
  },
  sidebarTitle: {
    fontSize: '1.2rem',
    marginBottom: '1.5rem',
    color: '#fff',
    borderBottom: '1px solid #444',
    paddingBottom: '0.5rem'
  },
  historyList: {
    display: 'flex',
    flexDirection: 'column',
    gap: '0.5rem'
  },
  historyItem: {
    padding: '0.8rem',
    background: '#333',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '1rem',
    '&:hover': {
      background: '#3a3a3a'
    }
  },
  mainContent: {
    width: '75%',
    padding: '1.5rem',
    display: 'flex',
    flexDirection: 'column'
  },
  title: {
    fontSize: '1.8rem', // Larger title
    marginBottom: '1.5rem',
    color: '#fff'
  },
  chatWindow: {
    flex: 1,
    overflowY: 'auto',
    background: '#2b2b2b',
    border: '1px solid #444',
    borderRadius: '5px',
    padding: '1.5rem', // More padding
    marginBottom: '1.5rem',
    fontSize: '1.1rem' // Larger chat text
  },
  message: {
    marginBottom: '1rem', // More space between messages
    whiteSpace: 'pre-wrap',
    wordBreak: 'break-word',
    lineHeight: '1.6', // Better line height
    fontSize: '1.1rem' // Larger message text
  },
  typing: {
    fontStyle: 'italic',
    color: '#aaa',
    fontSize: '1rem'
  },
  input: {
    width: '100%',
    padding: '1rem', // More padding
    border: '1px solid #444',
    borderRadius: '4px',
    resize: 'vertical',
    backgroundColor: '#1c1c1c',
    color: '#f5f5f5',
    marginBottom: '1.5rem',
    fontSize: '1.1rem', // Larger input text
    minHeight: '80px'
  },
  button: {
    padding: '1rem 1.5rem',
    backgroundColor: '#8ab4f8',
    color: '#1a1a1a',
    fontWeight: 'bold',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '1.1rem', // Larger button text
    alignSelf: 'flex-end'
  }
};