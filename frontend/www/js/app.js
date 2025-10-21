import routes from './routes.js';
import { login, getToken } from './auth.js';
import usersPage from './users.js';
import studentsPage from './students.js';
import streamPage from './stream.js';
import reportsPage from './reports.js';

import { StudentsListPage } from './students/list.js';
import { StudentAddPage } from './students/add.js';
import { StudentEditPage } from './students/edit.js';
import { StudentViewPage } from './students/view.js';

const app = new Framework7({
    name: 'SANAD',
    el: '#app',
    routes,
    on: {
        pageInit: function (page) {
            const n = page.name;
            if (n === 'users') usersPage(page);
            if (n === 'stream') streamPage(page);

            if (n === 'students') StudentsListPage(page);
            if (n === 'student-add') StudentAddPage(page);
            if (n === 'student-edit') StudentEditPage(page);
            if (n === 'student-view') StudentViewPage(page);
        },
    }
});

window.app = app;
app.views.main.router.on('routeChanged', (route) => {
    const current = route.url;
    const toolbar = document.querySelector('.toolbar.tabbar');
    if (!toolbar) return;

    const links = toolbar.querySelectorAll('.tab-link');
    links.forEach((a) => {
        const href = a.getAttribute('href');
        if (href === current) a.classList.add('tab-link-active');
        else a.classList.remove('tab-link-active');
    });

    // move the highlight bar to the active link
    const instance = toolbar.f7Tabbar;
    if (instance && instance.setHighlight) instance.setHighlight();
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
