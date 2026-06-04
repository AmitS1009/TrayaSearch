import React, { useEffect, useState } from 'react';
import { apiFetch } from '../api';
import MetricsDashboard from '../components/MetricsDashboard';
import { useAuth } from '../context/auth-context';

const Metrics = () => {
    const { token } = useAuth();
    const [scores, setScores] = useState(null);
    const [error, setError] = useState('');

    useEffect(() => {
        apiFetch('/evaluation/scores', {}, token).then(setScores).catch((err) => setError(err.message));
    }, [token]);

    return (
        <div className="max-w-7xl mx-auto px-4 py-10">
            <p className="text-sm font-bold uppercase tracking-[0.2em] text-indigo-600">RAGAS evaluation</p>
            <h1 className="text-4xl font-black text-gray-900 mt-2">Retrieval quality dashboard</h1>
            <p className="text-gray-500 mt-3 mb-8">
                Scores remain marked as not run until an evaluator API key is configured and the test set is evaluated.
            </p>
            {error ? <p className="text-red-600">{error}</p> : <MetricsDashboard scores={scores} />}
        </div>
    );
};

export default Metrics;
