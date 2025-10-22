import { api } from '../api.js';
import {getToken} from "../auth.js";

export function UsersListPage(page) {
    const token = getToken();
    if (!token) return;

    const app = page.app;
    const $ = app.$;
    const $page = $(page.el);

    async function loadUsers() {
        try {
            const users = await api('/users');
            const list = $page.find('#users-list');
            list.html('');
            users.forEach((u) => {
                list.append(`
          <li>
            <a href="/user-view/${u.id}/" class="item-link item-content">
              <div class="item-inner">
                <div class="item-title-row">
                  <div class="item-title">${u.name}</div>
                  <div class="item-after">${u.is_teacher ? 'Teacher' : 'Parent'}</div>
                </div>
                <div class="item-subtitle">${u.email}</div>
              </div>
            </a>
          </li>
        `);
            });
        } catch (err) {
            const msg = typeof err === 'string'
                ? err
                : err.detail || err.message || 'An unexpected error occurred';
            app.dialog.alert(msg, 'Error');
        }
    }

    $page.find('#add_user_btn').on('click', () => {
        app.views.main.router.navigate('/user-add/');
    });

    loadUsers();
}
