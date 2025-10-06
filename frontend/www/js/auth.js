export let token = localStorage.getItem('token') || null;

export async function login(email, password) {
    const form = new FormData();
    form.append('email', email);
    form.append('password', password);
    const res = await fetch('http://127.0.0.1:8000/auth/login', { method: 'POST', body: form });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Login failed');
    token = data.token;
    localStorage.setItem('token', token);
    return data;
}

export function getToken() {
    return token || localStorage.getItem('token');
}

export function logout(app) {
    token = null;
    localStorage.removeItem('token');
    app.views.main.router.navigate('/login/');
}
