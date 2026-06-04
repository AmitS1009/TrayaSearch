import React from 'react';

const labels = {
    faithfulness: 'Faithfulness',
    answer_relevancy: 'Answer relevancy',
    context_precision: 'Context precision',
    context_recall: 'Context recall',
};

const MetricsDashboard = ({ scores }) => (
    <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {Object.entries(labels).map(([key, label]) => {
            const value = scores?.[key];
            const percentage = typeof value === 'number' ? Math.round(value * 100) : null;
            return (
                <article key={key} className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
                    <p className="text-sm font-medium text-gray-500">{label}</p>
                    <p className="text-3xl font-black text-gray-900 mt-2">
                        {percentage === null ? 'Not run' : `${percentage}%`}
                    </p>
                    <div className="h-2 bg-gray-100 rounded-full mt-4 overflow-hidden">
                        <div
                            className="h-full bg-indigo-600 rounded-full"
                            style={{ width: `${percentage || 0}%` }}
                        />
                    </div>
                </article>
            );
        })}
    </div>
);

export default MetricsDashboard;
