// import React, { useState } from 'react';

// export default function ChatApp() {
//   const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
//   const [messages, setMessages] = useState([]);
//   const [prompt, setPrompt] = useState('');
//   const [loading, setLoading] = useState(false);

//   const sendPrompt = () => {
//     if (!prompt.trim()) return;

//     const newMessage = { role: 'user', text: prompt };
//     setMessages((prev) => [...prev, newMessage]);
//     setPrompt('');
//     setLoading(true);

//     // Giả lập phản hồi
//     setTimeout(() => {
//       setMessages((prev) => [
//         ...prev,
//         { role: 'synergy', text: `You said: "${prompt}"` },
//       ]);
//       setLoading(false);
//     }, 1000);
//   };

//   return (
//     <div className="flex h-screen bg-[#0f0f0f] text-[#e0e0e0]">
//       {/* Sidebar */}
//       <div className={`bg-[#121212] border-r border-[#333] transition-all duration-300 ${sidebarCollapsed ? 'w-16' : 'w-64'}`}>
//         <div className="p-4 border-b border-[#333] flex items-center justify-between">
//           {!sidebarCollapsed && <h2 className="text-xl font-bold">SYNERGY</h2>}
//           <button 
//             onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
//             className="p-1 rounded hover:bg-[#2b2b2b]"
//           >
//             {sidebarCollapsed ? '→' : '←'}
//           </button>
//         </div>
//         {!sidebarCollapsed && (
//           <div className="p-4">
//             <div className="mb-6">
//               <h3 className="text-sm uppercase text-[#999] mb-2">Chats</h3>
//               {/* Danh sách chats */}
//             </div>
//           </div>
//         )}
//       </div>

//       {/* Main content */}
//       <main className="flex-1 flex flex-col overflow-hidden">
//         {/* Header */}
//         <header className="bg-[#121212] border-b border-[#333] p-4 flex items-center justify-between">
//           <h1 className="text-xl font-semibold">SYNERGY</h1>
//           <div className="flex items-center space-x-4">
//             {/* Các nút điều khiển */}
//           </div>
//         </header>

//         {/* Chat container */}
//         <div className="flex-1 overflow-y-auto p-4 bg-[#0f0f0f]">
//           <div className="max-w-4xl mx-auto">
//             {messages.map((msg, idx) => (
//               <div
//                 key={idx}
//                 className={`mb-6 p-4 rounded-lg ${msg.role === 'user' ? 'bg-[#1e1e1e]' : 'bg-[#252525]'}`}
//               >
//                 <div className="flex items-start mb-2">
//                   <div className={`w-8 h-8 rounded-full flex items-center justify-center mr-3 ${msg.role === 'user' ? 'bg-blue-500' : 'bg-green-500'}`}>
//                     {msg.role === 'user' ? 'U' : 'S'}
//                   </div>
//                   <strong>{msg.role === 'user' ? 'You' : 'SYNERGY'}</strong>
//                 </div>
//                 <div className="whitespace-pre-wrap pl-11">{msg.text}</div>
//               </div>
//             ))}
//             {loading && (
//               <div className="flex items-center p-4 text-gray-400">
//                 <div className="animate-pulse mr-2">•</div>
//                 SYNERGY is thinking...
//               </div>
//             )}
//           </div>
//         </div>

//         {/* Input area */}
//         <div className="bg-[#121212] border-t border-[#333] p-4">
//           <div className="max-w-4xl mx-auto">
//             <div className="relative">
//               <textarea
//                 className="w-full p-4 pr-16 rounded-lg bg-[#1e1e1e] border border-[#333] text-white resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
//                 rows={4}
//                 value={prompt}
//                 onChange={(e) => setPrompt(e.target.value)}
//                 placeholder="Message SYNERGY..."
//                 onKeyDown={(e) => {
//                   if (e.key === 'Enter' && !e.shiftKey) {
//                     e.preventDefault();
//                     setTimeout(() => sendPrompt(), 0); // Prevent tràn dòng
//                   }
//                 }}
//               />
//               <button
//                 className="absolute right-3 bottom-3 p-2 bg-blue-500 rounded-lg disabled:opacity-50 hover:bg-blue-600 transition"
//                 onClick={sendPrompt}
//                 disabled={loading || !prompt.trim()}
//               >
//                 {loading ? (
//                   <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
//                     <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
//                     <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
//                   </svg>
//                 ) : (
//                   '→'
//                 )}
//               </button>
//             </div>
//             <div className="mt-2 text-xs text-gray-400 text-center">
//               SYNERGY may produce inaccurate information
//             </div>
//           </div>
//         </div>
//       </main>
//     </div>
//   );
// }


import { useState } from 'react';

export default function ChatApp() {
  const [prompt, setPrompt] = useState('');
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

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
//     <div className="flex h-screen bg-[#0f0f0f] text-[#e0e0e0]">
//     {/* Sidebar có thể thu nhỏ */}
//     <div className={`bg-[#121212] border-r border-[#333] transition-all duration-300 ${sidebarCollapsed ? 'w-16' : 'w-64'}`}>
//       <div className="p-4 border-b border-[#333] flex items-center justify-between">
//         {!sidebarCollapsed && <h2 className="text-xl font-bold">SYNERGY</h2>}
//         <button 
//           onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
//           className="p-1 rounded hover:bg-[#2b2b2b]"
//         >
//           {sidebarCollapsed ? '→' : '←'}
//         </button>
//       </div>
//       {!sidebarCollapsed && (
//         <div className="p-4">
//           <div className="mb-6">
//             <h3 className="text-sm uppercase text-[#999] mb-2">Chats</h3>
//             {/* Danh sách chats */}
//           </div>
//         </div>
//       )}
//     </div>

//     {/* Main content */}
//     <main className="flex-1 flex flex-col overflow-hidden">
//       {/* Header */}
//       <header className="bg-[#121212] border-b border-[#333] p-4 flex items-center justify-between">
//         <h1 className="text-xl font-semibold">SYNERGY</h1>
//         <div className="flex items-center space-x-4">
//           {/* Các nút điều khiển */}
//         </div>
//       </header>

//       {/* Chat container */}
//       <div className="flex-1 overflow-y-auto p-4 bg-[#0f0f0f]">
//         <div className="max-w-4xl mx-auto">
//           {messages.map((msg, idx) => (
//             <div
//               key={idx}
//               className={`mb-6 p-4 rounded-lg ${msg.role === 'user' ? 'bg-[#1e1e1e]' : 'bg-[#252525]'}`}
//             >
//               <div className="flex items-start mb-2">
//                 <div className={`w-8 h-8 rounded-full flex items-center justify-center mr-3 ${msg.role === 'user' ? 'bg-blue-500' : 'bg-green-500'}`}>
//                   {msg.role === 'user' ? 'U' : 'S'}
//                 </div>
//                 <strong>{msg.role === 'user' ? 'You' : 'SYNERGY'}</strong>
//               </div>
//               <div className="whitespace-pre-wrap pl-11">{msg.text}</div>
//             </div>
//           ))}
//           {loading && (
//             <div className="flex items-center p-4 text-gray-400">
//               <div className="animate-pulse mr-2">•</div>
//               SYNERGY is thinking...
//             </div>
//           )}
//         </div>
//       </div>

//       {/* Input area */}
//       <div className="bg-[#121212] border-t border-[#333] p-4">
//         <div className="max-w-4xl mx-auto">
//           <div className="relative">
//             <textarea
//               className="w-full p-4 pr-16 rounded-lg bg-[#1e1e1e] border border-[#333] text-white resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
//               rows={4}
//               value={prompt}
//               onChange={(e) => setPrompt(e.target.value)}
//               placeholder="Message SYNERGY..."
//               onKeyDown={(e) => {
//                 if (e.key === 'Enter' && !e.shiftKey) {
//                   e.preventDefault();
//                   sendPrompt();
//                 }
//               }}
//             />
//             <button
//               className="absolute right-3 bottom-3 p-2 bg-blue-500 rounded-lg disabled:opacity-50 hover:bg-blue-600 transition"
//               onClick={sendPrompt}
//               disabled={loading || !prompt.trim()}
//             >
//               {loading ? (
//                 <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
//                   <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
//                   <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
//                 </svg>
//               ) : (
//                 '→'
//               )}
//             </button>
//           </div>
//           <div className="mt-2 text-xs text-gray-400 text-center">
//             SYNERGY may produce inaccurate information
//           </div>
//         </div>
//       </div>
//     </main>
//   </div>




    <main className="min-h-screen p-8 bg-[#121212] text-[#e0e0e0] font-sans">
      <div className="max-w-[1300px] mx-auto bg-[#1e1e1e] p-6 rounded-md shadow-md">
        <h1 className="text-4xl text-white mb-4 font-semibold">SYNERGY</h1>

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
