import { getToken } from './auth.js';
const BASE = 'http://127.0.0.1:8000';

export async function api(url, options = {}) {
    const headers = new Headers(options.headers || {});
    const t = getToken();
    if (t) headers.set('Authorization', `Bearer ${t}`);
    headers.set('Accept', 'application/json');

    const res = await fetch(BASE + url, {
        ...options,
        method: options.method || 'GET',
        mode: 'cors',                    // ensure cross-origin allowed
        credentials: 'include',          // send cookies if backend expects them
        headers,
    });

    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        console.warn('API error', res.status, err);
        throw new Error(err.detail || `Request failed (${res.status})`);
    }
    return res.json();
}
