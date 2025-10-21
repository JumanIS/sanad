import { api } from '../api.js';

export function StudentsListPage(page) {
    const app = page.app;
    const $ = app.$;
    const $page = $(page.el);
    const base = 'http://127.0.0.1:8000';

    async function loadStudents() {
        try {
            const students = await api('/students');
            const list = $page.find('#students-list');
            list.html('');
            students.forEach(s => {
                list.append(`
          <li>
            <a href="/student-view/${s.id}/" class="item-link item-content">
              <div class="item-media">
                <img src="${s.photo ? base + '/storage/' + s.photo : 'https://placehold.co/64x64'}"
                     width="48" height="48" style="border-radius:50%">
              </div>
              <div class="item-inner">
                <div class="item-title-row">
                  <div class="item-title">${s.full_name}</div>
                  <div class="item-after">${s.class_name}</div>
                </div>
              </div>
            </a>
          </li>
        `);
            });
        } catch {
            app.toast.show({ text: 'Failed to load students', closeTimeout: 1500 });
        }
    }

    $page.find('#add_student_btn').on('click', () => {
        app.views.main.router.navigate('/student-add/');
    });

    loadStudents();
}
