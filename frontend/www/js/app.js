import routes from './routes.js';
import { login, getToken } from './auth.js';
import usersPage from './users.js';
import studentsPage from './students.js';
import streamPage from './stream.js';
import reportsPage from './reports.js';

const app = new Framework7({
    name: 'School Behavior AI',
    el: '#app',
    routes,
});

window.app = app;

// Attach page logic
app.on('page:init', (page) => {
    const n = page.name;
    if (n === 'users') usersPage(page);
    if (n === 'students') studentsPage(page);
    if (n === 'stream') streamPage(page);
    if (n === 'reports') reportsPage(page);
});

// === Force login screen on startup ===
document.addEventListener('DOMContentLoaded', () => {
    const token = getToken();
    if (!token) {
        // open login screen immediately
        app.loginScreen.open('#login-screen', true);
    } else {
        // go directly to main view if already logged in
        app.views.main.router.navigate('/students/');
    }
});

// === Login button ===
document.addEventListener('click', async (e) => {
    if (e.target.id === 'btn-login') {
        const email = document.getElementById('login-email').value.trim();
        const password = document.getElementById('login-password').value.trim();
        try {
            await login(email, password);
            app.loginScreen.close('#login-screen');
            app.views.main.router.navigate('/students/');
        } catch {
            app.dialog.alert('Login failed');
        }
    }
});
