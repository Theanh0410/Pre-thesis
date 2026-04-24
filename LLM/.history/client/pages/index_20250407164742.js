import { useState } from 'react';

export default function ChatApp() {
  const [prompt, setPrompt] = useState('');
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);

  // const sendPrompt = async () => {
  //   if (!prompt.trim()) return;

  //   // Thêm tin nhắn người dùng
  //   const userMsg = { role: 'user', text: prompt };
  //   setMessages(prev => [...prev, userMsg]);
  //   setPrompt('');
  //   setLoading(true);

  //   try {
  //     // Gọi API
  //     const res = await fetch('http://localhost:5000/api/chat', {
  //       method: 'POST',
  //       headers: { 'Content-Type': 'application/json' },
  //       body: JSON.stringify({ prompt: userMsg.text }),
  //     });

  //     // Kiểm tra response
  //     if (!res.ok) {
  //       throw new Error(`Server error: ${res.status} ${res.statusText}`);
  //     }

  //     if (!res.body) {
  //       throw new Error('No response body received');
  //     }

  //     // Thêm placeholder cho bot response
  //     let botMsg = { role: 'bot', text: '' };
  //     setMessages(prev => [...prev, botMsg]);

  //     // Xử lý stream
  //     const reader = res.body.getReader();
  //     const decoder = new TextDecoder();

  //     while (true) {
  //       const { done, value } = await reader.read();
  //       if (done) break;
        
  //       const chunk = decoder.decode(value, { stream: true });
  //       botMsg = { ...botMsg, text: botMsg.text + chunk };
        
  //       // Cập nhật tin nhắn cuối cùng
  //       setMessages(prev => [...prev.slice(0, -1), botMsg]);
  //     }
  //   } catch (error) {
  //     console.error('API call failed:', error);
      
  //     // Thay thế placeholder bằng thông báo lỗi
  //     setMessages(prev => [
  //       ...prev.slice(0, -1), 
  //       { 
  //         role: 'bot', 
  //         text: `❌ Error: ${error.message || 'Failed to get response'}` 
  //       }
  //     ]);
  //   } finally {
  //     setLoading(false);
  //   }
  // };
  const sendPrompt = async () => {
    try {
      const res = await fetch('http://localhost:5000/api/chat', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Accept': 'text/plain' 
        },
        body: JSON.stringify({ prompt }),
      });
  
      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`);
      }
      
      // Xử lý stream...
    } catch (error) {
      console.error('Fetch error:', error);
      setMessages(prev => [...prev, {
        role: 'bot',
        text: `⚠️ Connection error: ${error.message}`
      }]);
    }
  };

  return (
    <main style={styles.main}>
      <div style={styles.container}>
        <h1 style={styles.title}>💬 Chat with LLaMA 3.2</h1>
        
        <div style={styles.chatWindow}>
          {messages.map((msg, idx) => (
            <div 
              key={idx} 
              style={{
                ...styles.message,
                color: msg.role === 'user' ? '#1a73e8' : '#0f9d58'
              }}
            >
              <strong>{msg.role === 'user' ? 'You' : 'LLaMA'}:</strong> {msg.text}
            </div>
          ))}
          {loading && (
            <div style={styles.typingIndicator}>LLaMA is typing...</div>
          )}
        </div>
        
        <textarea
          rows={4}
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          style={styles.input}
          placeholder="Type your message..."
          disabled={loading}
          onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && sendPrompt()}
        />
        
        <button
          onClick={sendPrompt}
          disabled={loading || !prompt.trim()}
          style={styles.button}
        >
          {loading ? 'Thinking...' : 'Send'}
        </button>
      </div>
    </main>
  );
}

// Styles
const styles = {
  main: {
    padding: '2rem',
    fontFamily: 'sans-serif',
    background: '#f5f5f5',
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
    height: '320px',
    overflowY: 'auto',
    border: '1px solid #ccc',
    padding: '1rem',
    borderRadius: '0.25rem',
    background: '#fafafa',
    marginBottom: '1rem'
  },
  message: {
    marginBottom: '0.75rem',
    whiteSpace: 'pre-wrap',
    wordBreak: 'break-word'
  },
  typingIndicator: {
    color: '#666',
    fontStyle: 'italic',
    marginBottom: '0.75rem'
  },
  input: {
    width: '100%',
    padding: '0.75rem',
    borderRadius: '0.25rem',
    border: '1px solid #ccc',
    marginBottom: '0.75rem',
    resize: 'vertical'
  },
  button: {
    backgroundColor: '#1a73e8',
    color: 'white',
    padding: '0.75rem 1.5rem',
    border: 'none',
    borderRadius: '0.25rem',
    cursor: 'pointer',
    opacity: 1,
    transition: 'opacity 0.2s',
    ':disabled': {
      opacity: 0.6,
      cursor: 'not-allowed'
    }
  }
};

// import { useState } from 'react';

// export default function Home() {
//   const [prompt, setPrompt] = useState('');
//   const [messages, setMessages] = useState([]);
//   const [loading, setLoading] = useState(false);

//   const sendPrompt = async () => {
//     if (!prompt.trim()) return;
  
//     const userMsg = { role: 'user', text: prompt };
//     setMessages([...messages, userMsg]);
//     setPrompt('');
//     setLoading(true);
  
//     try {
//       const res = await fetch('http://localhost:5000/api/chat', {
//         method: 'POST',
//         headers: { 'Content-Type': 'application/json' },
//         body: JSON.stringify({ prompt: userMsg.text }),
//       });
  
//       const reader = res.body.getReader();
//       const decoder = new TextDecoder('utf-8');
//       let botMsg = { role: 'bot', text: '' };
//       setMessages(prev => [...prev, botMsg]);
  
//       while (true) {
//         const { done, value } = await reader.read();
//         if (done) break;
//         const chunk = decoder.decode(value);
//         botMsg.text += chunk;
//         setMessages(prev => [...prev.slice(0, -1), botMsg]);
//       }
  
//     } catch (error) {
//       console.error("Fetch failed:", error);
//       setMessages(prev => [...prev, { role: 'bot', text: '❌ Error: Unable to fetch response from backend.' }]);
//     }
  
//     setLoading(false);
//   };
  
//   // const sendPrompt = async () => {
//   //   if (!prompt.trim()) return;

//   //   const userMsg = { role: 'user', text: prompt };
//   //   setMessages([...messages, userMsg]);
//   //   setPrompt('');
//   //   setLoading(true);

    

//   //   const res = await fetch('http://localhost:5000/api/chat', {
//   //     method: 'POST',
//   //     headers: { 'Content-Type': 'application/json' },
//   //     body: JSON.stringify({ prompt: userMsg.text }),
//   //   });

//   //   const reader = res.body.getReader();
//   //   const decoder = new TextDecoder('utf-8');
//   //   let botMsg = { role: 'bot', text: '' };

//   //   while (true) {
//   //     const { done, value } = await reader.read();
//   //     if (done) break;
//   //     const chunk = decoder.decode(value);
//   //     botMsg.text += chunk;
//   //     setMessages(prev => [...prev.slice(0, -1), botMsg]);
//   //   }

//   //   setMessages(prev => [...prev, botMsg]);
//   //   setLoading(false);
//   // };

//   return (
//     <main style={{ padding: '2rem', fontFamily: 'sans-serif', background: '#f5f5f5', minHeight: '100vh' }}>
//       <div style={{ maxWidth: '700px', margin: 'auto', background: 'white', padding: '1.5rem', borderRadius: '0.5rem', boxShadow: '0 0 10px rgba(0,0,0,0.1)' }}>
//         <h1 style={{ fontSize: '1.5rem', marginBottom: '1rem' }}>💬 Chat with LLaMA 3.2</h1>
//         <div style={{ height: '320px', overflowY: 'auto', border: '1px solid #ccc', padding: '1rem', borderRadius: '0.25rem', background: '#fafafa', marginBottom: '1rem' }}>
//           {messages.map((msg, idx) => (
//             <div key={idx} style={{ marginBottom: '0.75rem', color: msg.role === 'user' ? '#1a73e8' : '#0f9d58' }}>
//               <strong>{msg.role === 'user' ? 'You' : 'LLaMA'}:</strong> {msg.text}
//             </div>
//           ))}
//         </div>
//         <textarea
//           rows={4}
//           value={prompt}
//           onChange={(e) => setPrompt(e.target.value)}
//           style={{ width: '100%', padding: '0.75rem', borderRadius: '0.25rem', border: '1px solid #ccc', marginBottom: '0.75rem' }}
//           placeholder="Type your message..."
//         />
//         <button
//           onClick={sendPrompt}
//           disabled={loading}
//           style={{ backgroundColor: '#1a73e8', color: 'white', padding: '0.75rem 1.5rem', border: 'none', borderRadius: '0.25rem', cursor: 'pointer' }}
//         >
//           {loading ? 'Thinking...' : 'Send'}
//         </button>
//       </div>
//     </main>
//   );
// }