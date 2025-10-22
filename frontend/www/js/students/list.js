import { api, getBaseURL } from '../api.js';
import { getToken } from '../auth.js';

export function StudentsListPage(page) {
    const token = getToken();
    if (!token) return;

    const app = page.app;
    const $ = app.$;
    const $page = $(page.el);

    // get current user data from storage
    const user = JSON.parse(localStorage.getItem('user') || '{}');

    async function loadStudents() {
        try {
            const students = await api('/students');
            const list = $page.find('#students-list');
            list.html('');

            const base = getBaseURL();

            students.forEach((s) => {
                const name = s.full_name || 'Unnamed';
                const cls = s.class_name || 'No class';
                const img = s.photo ? `${base}/${s.photo}` : './assets/avatar.png';

                list.append(`
          <li>
            <a href="/student-view/${s.id}/" class="item-link item-content">
              <div class="item-media">
                <img src="${img}" width="48" height="48" style="border-radius:50%">
              </div>
              <div class="item-inner">
                <div class="item-title-row">
                  <div class="item-title"><div class="item-header">${cls}</div>${name}</div>
                </div>
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

    // hide "Add" button if user is not a teacher
    if (!user.is_teacher) {
        $page.find('#add_student_btn').hide();
    } else {
        $page.find('#add_student_btn').on('click', () => {
            app.views.main.router.navigate('/student-add/');
        });
    }

    loadStudents();
}
