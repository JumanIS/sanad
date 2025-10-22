import { getBaseURL } from './api.js';

export let token = localStorage.getItem('token') || null;

/* ─────────────────────────────
   Login and store user + token
───────────────────────────── */
export async function login(email, password) {
    const base = getBaseURL();
    if (!base) throw new Error('Server host not set');

    const form = new FormData();
    form.append('email', email);
    form.append('password', password);

    const res = await fetch(base + '/auth/login', { method: 'POST', body: form });
    const data = await res.json().catch(() => ({}));

    if (!res.ok) throw new Error(data.detail || 'Login failed');

    token = data.token;
    localStorage.setItem('token', token);

    if (data.user) {
        localStorage.setItem('user', JSON.stringify(data.user));
    }

    return data;
}

export function getToken() {
    return token || localStorage.getItem('token');
}

export function logout(app) {
    token = null;
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    app.loginScreen.open('#login-screen');
}
