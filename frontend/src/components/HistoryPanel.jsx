import React from 'react';

const HistoryPanel = ({ history, loading, onSelect }) => (
    <aside className="w-full lg:w-72 bg-slate-950 text-white rounded-xl overflow-hidden flex-shrink-0">
        <div className="px-4 py-4 border-b border-slate-800">
            <p className="text-xs uppercase tracking-[0.2em] text-indigo-300">Your workspace</p>
            <h2 className="font-bold text-lg mt-1">Chat history</h2>
        </div>
        <div className="p-2 space-y-1 max-h-64 lg:max-h-[calc(100vh-180px)] overflow-y-auto">
            {loading && <p className="p-3 text-sm text-slate-400">Loading conversations...</p>}
            {!loading && history.length === 0 && (
                <p className="p-3 text-sm text-slate-400">Your product conversations will appear here.</p>
            )}
            {history.map((item) => (
                <button
                    key={item.id}
                    type="button"
                    onClick={() => onSelect(item)}
                    className="w-full text-left rounded-lg p-3 hover:bg-slate-800 transition-colors"
                >
                    <span className="block text-sm font-medium truncate">{item.query}</span>
                    <span className="block text-xs text-slate-400 mt-1">
                        {new Date(item.created_at).toLocaleString()}
                    </span>
                </button>
            ))}
        </div>
    </aside>
);

export default HistoryPanel;
