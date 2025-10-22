import { getToken } from './auth.js';

/* Get saved backend host (IP or domain) */
export function getBaseURL() {
    const saved = localStorage.getItem('base_url');
    if (!saved) return '';
    // Ensure no trailing slash
    return saved.endsWith('/') ? saved.slice(0, -1) : saved;
}

/* Generic API wrapper */
export async function api(url, options = {}) {
    const base = getBaseURL();
    if (!base) throw new Error('Server host not set. Please login again.', url);

    const headers = new Headers(options.headers || {});
    const t = getToken();
    if (t) headers.set('Authorization', `Bearer ${t}`);
    headers.set('Accept', 'application/json');

    const res = await fetch(base + url, {
        ...options,
        method: options.method || 'GET',
        mode: 'cors',
        credentials: 'include',
        headers,
    });

    let data = {};
    try {
        data = await res.json();
    } catch {
        data = {};
    }

    if (!res.ok) {
        // Pass backend detail field if available
        throw { detail: data.detail || `Request failed (${res.status})` };
    }

    return data;
}
