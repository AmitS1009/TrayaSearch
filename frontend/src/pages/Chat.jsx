import React, { useCallback, useEffect, useRef, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { apiFetch } from '../api';
import HistoryPanel from '../components/HistoryPanel';
import { useAuth } from '../context/auth-context';

const welcome = {
    role: 'assistant',
    content: "Hi! I'm Neusearch AI. Describe what you need, your concern, or a product ingredient you're interested in.",
};

const Chat = () => {
    const { token } = useAuth();
    const [messages, setMessages] = useState([welcome]);
    const [history, setHistory] = useState([]);
    const [historyLoading, setHistoryLoading] = useState(true);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const messagesEndRef = useRef(null);

    const loadHistory = useCallback(async () => {
        setHistoryLoading(true);
        try {
            setHistory(await apiFetch('/chat/history', {}, token));
        } catch (err) {
            console.error('Unable to load history:', err);
        } finally {
            setHistoryLoading(false);
        }
    }, [token]);

    useEffect(() => {
        loadHistory();
    }, [loadHistory]);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const sendMessage = async (event) => {
        event.preventDefault();
        const query = input.trim();
        if (!query) return;
        setMessages((previous) => [...previous, { role: 'user', content: query }]);
        setInput('');
        setLoading(true);

        try {
            const data = await apiFetch('/chat', {
                method: 'POST',
                body: JSON.stringify({ query }),
            }, token);
            setMessages((previous) => [...previous, {
                role: 'assistant',
                content: data.response,
                retries: data.retries,
                warning: data.warning,
            }]);
            await loadHistory();
        } catch (err) {
            setMessages((previous) => [...previous, {
                role: 'assistant',
                content: `Sorry, I couldn't complete that search: ${err.message}`,
            }]);
        } finally {
            setLoading(false);
        }
    };

    const selectHistory = (item) => {
        setMessages([
            welcome,
            { role: 'user', content: item.query },
            {
                role: 'assistant',
                content: item.response,
                retries: item.self_rag_retries,
            },
        ]);
    };

    return (
        <div className="max-w-7xl mx-auto px-4 py-6 min-h-[calc(100vh-64px)] flex flex-col lg:flex-row gap-5">
            <HistoryPanel history={history} loading={historyLoading} onSelect={selectHistory} />
            <section className="bg-white rounded-xl shadow-lg flex-1 flex flex-col overflow-hidden min-h-[70vh]">
                <div className="bg-indigo-600 p-4 flex justify-between items-center">
                    <div>
                        <p className="text-xs uppercase tracking-[0.2em] text-indigo-200">Self-RAG product advisor</p>
                        <h1 className="text-white text-xl font-bold">Neusearch Assistant</h1>
                    </div>
                    <span className="rounded-full bg-indigo-500 px-3 py-1 text-xs font-bold text-white">Grounded answers</span>
                </div>

                <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50">
                    {messages.map((message, index) => (
                        <div key={`${message.role}-${index}`} className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                            <div className={`max-w-[85%] rounded-xl p-4 ${message.role === 'user'
                                ? 'bg-indigo-600 text-white rounded-br-none'
                                : 'bg-white text-gray-800 shadow-sm rounded-bl-none border border-gray-200'
                            }`}>
                                {message.role === 'assistant' ? (
                                    <>
                                        <div className="prose prose-sm max-w-none">
                                            <ReactMarkdown>{message.content}</ReactMarkdown>
                                        </div>
                                        {typeof message.retries === 'number' && (
                                            <p className="mt-3 text-xs font-medium text-gray-400">
                                                Self-RAG retries: {message.retries}{message.warning ? ` · ${message.warning}` : ''}
                                            </p>
                                        )}
                                    </>
                                ) : <p>{message.content}</p>}
                            </div>
                        </div>
                    ))}
                    {loading && (
                        <div className="flex justify-start">
                            <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
                                <p className="text-sm text-gray-500">Retrieving, reranking, and checking grounding...</p>
                            </div>
                        </div>
                    )}
                    <div ref={messagesEndRef} />
                </div>

                <div className="p-4 bg-white border-t border-gray-200">
                    <form onSubmit={sendMessage} className="flex gap-2">
                        <input
                            type="text"
                            value={input}
                            onChange={(event) => setInput(event.target.value)}
                            placeholder="Try: I have dandruff and a sensitive scalp"
                            className="flex-1 border border-gray-300 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                            disabled={loading}
                        />
                        <button
                            type="submit"
                            disabled={loading || !input.trim()}
                            className="bg-indigo-600 text-white px-6 py-3 rounded-lg font-bold hover:bg-indigo-700 disabled:opacity-50"
                        >
                            Send
                        </button>
                    </form>
                </div>
            </section>
        </div>
    );
};

export default Chat;
