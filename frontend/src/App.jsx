import { useState, useRef, useEffect } from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
// import reactLogo from './assets/react.svg'
// import viteLogo from '/vite.svg'
import './App.css'

// Helper function to format API responses
function formatApiResponse(response) {
  if (!response || !response.type || !response.data) {
    return 'Invalid response format from server.';
  }

  const { type, data } = response;

  if (type === 'roll') {
    const values = data.individual_values?.join(', ') ?? 'N/A';
    const modifier = data.modifier > 0 ? ` + ${data.modifier}` : (data.modifier < 0 ? ` - ${Math.abs(data.modifier)}` : '');
    return `Rolled: ${data.total ?? 'N/A'} (Values: [${values}]${modifier})`;
  }

  if (type === 'stats') {
    // Simple formatting, adjust as needed
    return `Stats (${data.count} rolls):\n` +
           `Min: ${data.minimum}, Max: ${data.maximum}\n` +
           `Mean: ${data.mean?.toFixed(2)}, Median: ${data.median}\n` +
           `Std Dev: ${data.std_dev?.toFixed(2)}`;
           // Bins could be visualized or formatted differently if needed
           // `Bins: ${JSON.stringify(data.bins)}`
  }

  return 'Unknown response type from server.';
}

// Histogram component for stats visualization
function StatsHistogram({ bins }) {
  if (!bins) return null;

  // Convert bins object to array format for recharts
  const data = Object.entries(bins).map(([value, count]) => ({
    value: parseInt(value),
    count: count
  })).sort((a, b) => a.value - b.value);

  return (
    <div className="w-full h-64 mt-10 mb-4">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 5, right: 5, left: 5, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="value" />
          <YAxis />
          <Tooltip />
          <Bar dataKey="count" fill="#8884d8" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

// ChatBubble component to display individual messages
function ChatBubble({ message }) {
  const { text, type, data } = message;
  const isUser = type === 'user';

  return (
    <div className={`my-2 p-3 rounded-lg break-words whitespace-pre-wrap ${
      isUser
        ? 'bg-blue-500 text-white self-end max-w-xs'
        : 'bg-gray-300 text-black w-full'
    }`}>
      {text}
      {!isUser && data?.type === 'stats' && <StatsHistogram bins={data.data.bins} />}
    </div>
  );
}

// ChatArea component to display the list of messages
function ChatArea({ messages }) {
  const chatEndRef = useRef(null);

  // Scroll to bottom when messages change
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="flex-grow w-full max-w-2xl overflow-y-auto p-4 flex flex-col border border-gray-300 rounded mb-4 bg-white">
      <div className="flex-grow" /> {/* Spacer to push content to bottom */}
      <div className="flex flex-col">
        {messages.map((msg) => (
          <ChatBubble key={msg.id} message={msg} />
        ))}
        <div ref={chatEndRef} />
      </div>
    </div>
  );
}

// InputArea component for the text input and send button
function InputArea({ inputValue, setInputValue, onSend, isLoading, inputRef }) {
  const handleKeyDown = (event) => {
    if (event.key === 'Enter' && !event.shiftKey && !isLoading) {
      event.preventDefault(); // Prevent newline on Enter
      onSend();
    }
  };

  return (
    <div className="w-full max-w-2xl pb-4 pt-4 flex items-center">
      <textarea
        ref={inputRef}
        className="flex-grow mr-2 p-2 border border-gray-300 rounded resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
        value={inputValue}
        onChange={(e) => setInputValue(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={isLoading ? "Waiting for response..." : "Type your dice command..."}
        rows="1"
        disabled={isLoading}
      />
      <button
        className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-blue-300"
        onClick={onSend}
        disabled={!inputValue.trim() || isLoading}
      >
        {isLoading ? '...' : 'Send'}
      </button>
    </div>
  );
}

// Main App component
function App() {
  const [messages, setMessages] = useState([
    { id: Date.now(), text: "Enter a dice command, e.g., 'roll 2d6+3' or 'stats 100 1d20'", type: "response" }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const inputRef = useRef(null);

  // Focus input on mount and after sending message
  useEffect(() => {
    inputRef.current?.focus();
  }, [messages]);

  const handleSend = async () => {
    const trimmedInput = inputValue.trim();
    if (!trimmedInput || isLoading) return;

    const userMessageId = Date.now(); // Simple unique ID
    const responseMessageId = userMessageId + 1; // Simple unique ID for response

    const newUserMessage = { id: userMessageId, text: trimmedInput, type: 'user' };
    const loadingMessage = { id: responseMessageId, text: '...', type: 'response' }; // Placeholder

    setMessages(prevMessages => [...prevMessages, newUserMessage, loadingMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      const response = await fetch('http://localhost:8000/prompt', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ command: trimmedInput }),
      });

      let messageText;
      let responseData;
      if (response.ok) {
        responseData = await response.json();
        messageText = formatApiResponse(responseData);
      } else {
        const errorData = await response.json().catch(() => ({ detail: 'Failed to parse error response.' }));
        messageText = `Error: ${response.status} - ${errorData?.detail || response.statusText}`;
      }

      // Update the loading message with the actual response or error
      setMessages(prevMessages =>
        prevMessages.map(msg =>
          msg.id === responseMessageId ? { ...msg, text: messageText, data: responseData } : msg
        )
      );

    } catch (error) {
      console.error("API call failed:", error);
      // Update the loading message with a network error message
      setMessages(prevMessages =>
        prevMessages.map(msg =>
          msg.id === responseMessageId ? { ...msg, text: 'Failed to fetch. Check connection or server.' } : msg
        )
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    // Use flex-col and h-screen for full height layout
    <div className="h-screen flex flex-col items-center bg-gray-100 p-4">
      {/* ChatArea takes available space and handles its own scrolling */}
      <ChatArea messages={messages} />
      {/* InputArea stays fixed at the bottom */}
      <InputArea
        inputValue={inputValue}
        setInputValue={setInputValue}
        onSend={handleSend}
        isLoading={isLoading}
        inputRef={inputRef}
      />
    </div>
  );
}

export default App
