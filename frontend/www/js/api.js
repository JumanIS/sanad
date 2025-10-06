import { getToken } from './auth.js';
const BASE = 'http://127.0.0.1:8000';

export async function api(url, options = {}) {
    const headers = options.headers || {};
    const t = getToken();
    if (t) headers['Authorization'] = `Bearer ${t}`;
    const res = await fetch(BASE + url, { ...options, headers });
    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || 'Request failed');
    }
    return res.json();
}
