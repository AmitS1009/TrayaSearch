const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export async function apiFetch(path, options = {}, token = null) {
    const headers = new Headers(options.headers || {});
    if (options.body && !headers.has('Content-Type')) {
        headers.set('Content-Type', 'application/json');
    }
    if (token) {
        headers.set('Authorization', `Bearer ${token}`);
    }

    const response = await fetch(`${API_URL}${path}`, { ...options, headers });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
        throw new Error(data.detail || 'Request failed');
    }
    return data;
}
