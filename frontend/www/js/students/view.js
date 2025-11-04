import { api, getBaseURL } from '../api.js';

export function StudentViewPage(page) {
    const app = page.app;
    const $ = app.$;
    const $page = $(page.el);
    const id = page.route.params.id;

    const user = JSON.parse(localStorage.getItem('user') || '{}');

    async function loadStudent() {
        try {
            const s = await api(`/students/${id}`);
            const base = getBaseURL();
            const img = s.photo ? `${base}/${s.photo}` : './assets/avatar.png';

            $page.find('#student-photo').attr('src', img);
            $page.find('#student-name').text(s.full_name || 'Unnamed');
            $page.find('#student-class').text(s.class_name || 'No class');
            $page.find('#student-parent').text(s.parent_email || 'N/A');

            const list = $page.find('#behaviors-list');
            list.html('');

            if (s.behaviors && s.behaviors.length) {
                s.behaviors.forEach((b) => {
                    const bgStyle = b.is_exam && b.behavior !== 'attentive' ? 'background-color: #f8d7da;' : '';
                    list.append(`
            <li style="${bgStyle}">
              <div class="item-content">
                  <div class="item-inner">
                    <div class="item-title-row">
                        <div class="item-title">${b.behavior} (${b.is_exam ? 'exam' : 'class'})</div>
                        <div class="item-after">%${b.confidence ? Math.round(b.confidence * 100) : '0'}</div>
                    </div>
                    <div class="item-subtitle">${new Date(b.timestamp).toLocaleString()}</div>
                  </div>
              </div>
            </li>
          `);
                });
            } else {
                list.append(`
          <li>
            <div class="item-content">
              <div class="item-inner">
                <div class="item-title text-color-gray">No behaviors recorded</div>
              </div>
            </div>
          </li>
        `);
            }
        } catch (err) {
            const msg =
                typeof err === 'string'
                    ? err
                    : err.detail || err.message || 'Failed to load student';
            app.dialog.alert(msg, 'Error');
        }
    }

    // Show edit/delete only for teachers
    if (user.is_teacher) {
        $page.find('#edit-student-btn').on('click', () => {
            app.views.main.router.navigate(`/student-edit/${id}/`);
        });

        $page.find('#delete-student-btn').on('click', () => {
            app.dialog.confirm('Delete this student?', 'Confirm', async () => {
                try {
                    await api(`/students/${id}`, { method: 'DELETE' });
                    app.dialog.alert('Student deleted successfully', 'Success', () => {
                        app.views.main.router.navigate('/students/');
                    });
                } catch (err) {
                    const msg =
                        typeof err === 'string'
                            ? err
                            : err.detail || err.message || 'Failed to delete student';
                    app.dialog.alert(msg, 'Error');
                }
            });
        });
    } else {
        $page.find('#edit-student-btn').hide();
        $page.find('#delete-student-btn').hide();
    }

    loadStudent();
}
