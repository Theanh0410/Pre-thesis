// import Image from "next/image";
// import { Geist, Geist_Mono } from "next/font/google";

// const geistSans = Geist({
//   variable: "--font-geist-sans",
//   subsets: ["latin"],
// });

// const geistMono = Geist_Mono({
//   variable: "--font-geist-mono",
//   subsets: ["latin"],
// });

// export default function Home() {
//   return (
//     <div className="grid grid-rows-[20px_1fr_20px] items-center justify-items-center min-h-screen p-8 pb-20 gap-16 sm:p-20 font-[family-name:var(--font-geist-sans)]">
//       <main className="flex flex-col gap-[32px] row-start-2 items-center sm:items-start">
//         <Image
//           className="dark:invert"
//           src="/next.svg"
//           alt="Next.js logo"
//           width={180}
//           height={38}
//           priority
//         />
//         <ol className="list-inside list-decimal text-sm/6 text-center sm:text-left font-[family-name:var(--font-geist-mono)]">
//           <li className="mb-2 tracking-[-.01em]">
//             Get started by editing{" "}
//             <code className="bg-black/[.05] dark:bg-white/[.06] px-1 py-0.5 rounded font-[family-name:var(--font-geist-mono)] font-semibold">
//               pages/index.js
//             </code>
//             .
//           </li>
//           <li className="tracking-[-.01em]">
//             Save and see your changes instantly.
//           </li>
//         </ol>
//         <div className="flex gap-4 items-center flex-col sm:flex-row">
//           <a
//             className="rounded-full border border-solid border-transparent transition-colors flex items-center justify-center bg-foreground text-background gap-2 hover:bg-[#383838] dark:hover:bg-[#ccc] font-medium text-sm sm:text-base h-10 sm:h-12 px-4 sm:px-5 sm:w-auto"
//             href="https://vercel.com/new?utm_source=create-next-app&utm_medium=default-template-tw&utm_campaign=create-next-app"
//             target="_blank"
//             rel="noopener noreferrer"
//           >
//             <Image
//               className="dark:invert"
//               src="/vercel.svg"
//               alt="Vercel logomark"
//               width={20}
//               height={20}
//             />
//             Deploy now
//           </a>
//           <a
//             className="rounded-full border border-solid border-black/[.08] dark:border-white/[.145] transition-colors flex items-center justify-center hover:bg-[#f2f2f2] dark:hover:bg-[#1a1a1a] hover:border-transparent font-medium text-sm sm:text-base h-10 sm:h-12 px-4 sm:px-5 w-full sm:w-auto md:w-[158px]"
//             href="https://nextjs.org/docs?utm_source=create-next-app&utm_medium=default-template-tw&utm_campaign=create-next-app"
//             target="_blank"
//             rel="noopener noreferrer"
//           >
//             Read our docs
//           </a>
//         </div>
//       </main>
//       <footer className="row-start-3 flex gap-[24px] flex-wrap items-center justify-center">
//         <a
//           className="flex items-center gap-2 hover:underline hover:underline-offset-4"
//           href="https://nextjs.org/learn?utm_source=create-next-app&utm_medium=default-template-tw&utm_campaign=create-next-app"
//           target="_blank"
//           rel="noopener noreferrer"
//         >
//           <Image
//             aria-hidden
//             src="/file.svg"
//             alt="File icon"
//             width={16}
//             height={16}
//           />
//           Learn
//         </a>
//         <a
//           className="flex items-center gap-2 hover:underline hover:underline-offset-4"
//           href="https://vercel.com/templates?framework=next.js&utm_source=create-next-app&utm_medium=default-template-tw&utm_campaign=create-next-app"
//           target="_blank"
//           rel="noopener noreferrer"
//         >
//           <Image
//             aria-hidden
//             src="/window.svg"
//             alt="Window icon"
//             width={16}
//             height={16}
//           />
//           Examples
//         </a>
//         <a
//           className="flex items-center gap-2 hover:underline hover:underline-offset-4"
//           href="https://nextjs.org?utm_source=create-next-app&utm_medium=default-template-tw&utm_campaign=create-next-app"
//           target="_blank"
//           rel="noopener noreferrer"
//         >
//           <Image
//             aria-hidden
//             src="/globe.svg"
//             alt="Globe icon"
//             width={16}
//             height={16}
//           />
//           Go to nextjs.org →
//         </a>
//       </footer>
//     </div>
//   );
// }


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
//         <h1 style={styles.title}>🌓 SYNERGY</h1>

//         <div style={styles.chatWindow}>
//           {messages.map((msg, idx) => (
//             <div key={idx} style={{
//               ...styles.message,
//               color: msg.role === 'user' ? '#8ab4f8' : '#81c995'
//             }}>
//               <strong>{msg.role === 'user' ? 'You' : 'SYNERGY'}:</strong> {msg.text}
//             </div>
//           ))}
//           {loading && <div style={styles.typing}>SYNERGY is typing...</div>}
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
    <main className="min-h-screen p-8 bg-[#121212] text-[#e0e0e0] font-sans">
      <div className="max-w-[700px] mx-auto bg-[#1e1e1e] p-6 rounded-lg shadow-lg">
        <h1 className="text-white text-2xl font-semibold mb-4">🌓 SYNERGY</h1>

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
          className="w-full p-3 border border-[#444] rounded bg-[#1c1c1c] text-white mb-4 resize-y"
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
          className="px-6 py-3 bg-blue-300 text-black font-bold rounded hover:bg-blue-400 transition-all disabled:opacity-50"
          onClick={sendPrompt}
          disabled={loading || !prompt.trim()}
        >
          {loading ? 'Thinking...' : 'Send'}
        </button>
      </div>
    </main>
  );
}
