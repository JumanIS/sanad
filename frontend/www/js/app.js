import routes from './routes.js';
import { login, getToken, logout } from './auth.js';
import { StreamPage } from './stream.js';

import { StudentsListPage } from './students/list.js';
import { StudentAddPage } from './students/add.js';
import { StudentEditPage } from './students/edit.js';
import { StudentViewPage } from './students/view.js';

import { UsersListPage } from './users/list.js';
import { UserAddPage } from './users/add.js';
import { UserEditPage } from './users/edit.js';
import { UserViewPage } from './users/view.js';

const app = new Framework7({
    name: 'SANAD',
    el: '#app',
    routes,
    on: {
        pageInit: function (page) {
            const n = page.name;
            if (n === 'stream') StreamPage(page);

            if (n === 'students') StudentsListPage(page);
            if (n === 'student-add') StudentAddPage(page);
            if (n === 'student-edit') StudentEditPage(page);
            if (n === 'student-view') StudentViewPage(page);

            if (n === 'users') UsersListPage(page);
            if (n === 'user-add') UserAddPage(page);
            if (n === 'user-edit') UserEditPage(page);
            if (n === 'user-view') UserViewPage(page);

            if (!page.$el.find('.ptr-content').length) return;
            app.ptr.create('.ptr-content');
        },
    }
});

window.app = app;
app.views.main.router.on('routeChanged', (route) => {
    const path = route.url.split('?')[0];

    const links = document.querySelectorAll('.toolbar .tab-link');
    const highlight = document.querySelector('.toolbar .tab-link-highlight');

    // remove all active
    links.forEach(link => link.classList.remove('tab-link-active'));

    // find link that matches current route
    let active = Array.from(links).find(link => link.getAttribute('href') === path);
    if (!active) active = links[0];

    active.classList.add('tab-link-active');

    // move highlight under active link
    if (highlight && active) {
        const rect = active.getBoundingClientRect();
        const parentRect = active.parentElement.getBoundingClientRect();
        const left = rect.left - parentRect.left;
        highlight.style.width = `${rect.width}px`;
        highlight.style.transform = `translate3d(${left}px,0,0)`;
    }
});

app.on('pageAfterIn', () => document.activeElement?.blur());


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
        const host = document.getElementById('login-host').value.trim();
        const email = document.getElementById('login-email').value.trim();
        const password = document.getElementById('login-password').value.trim();

        if (!host || !email || !password) {
            app.dialog.alert('Please enter all fields', 'Error');
            return;
        }

        // Normalize host → add http:// if missing
        let base_url = host;
        if (!/^https?:\/\//i.test(base_url)) base_url = 'http://' + base_url;

        // Save it in localStorage (used by api.js)
        localStorage.setItem('base_url', base_url);

        try {
            await login(email, password);
            app.loginScreen.close('#login-screen');
            app.views.main.router.navigate('/students/');
            const page = app.views.main.router.currentPageEl.f7Page; // get Framework7 page object
            StudentsListPage(page);
        } catch (err) {
            const msg = typeof err === 'string'
                ? err
                : err.detail || err.message || 'An unexpected error occurred';
            app.dialog.alert(msg, 'Error');
        }
    }
});

document.addEventListener('ptr:refresh', async (e) => {
    const view = app.views.current;
    const router = view.router;
    const currentRoute = router.currentRoute;

    // reload the same page
    await router.navigate(currentRoute.url, {
        reloadCurrent: true,
        ignoreCache: true
    });
    app.ptr.done();
});

document.addEventListener('click', (e) => {
    const btn = e.target.closest('#logout-btn');
    if (btn) {
        logout(app);
    }
});