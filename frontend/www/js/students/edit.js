import { api } from '../api.js';

export function StudentEditPage(page) {
    const app = page.app;
    const $ = app.$;
    const $page = $(page.el);
    const id = page.route.params.id;

    const user = JSON.parse(localStorage.getItem('user') || '{}');

    // Redirect if user is not a teacher
    if (!user.is_teacher) {
        app.views.main.router.navigate('/students/');
        return;
    }

    async function loadStudent() {
        try {
            const s = await api(`/students/${id}`);
            $page.find('#st-name').val(s.full_name || '');
            $page.find('#st-class').val(s.class_name || '');
            $page.find('#st-parent').val(s.parent_email || '');
        } catch (err) {
            const msg = typeof err === 'string'
                ? err
                : err.detail || err.message || 'An unexpected error occurred';
            app.dialog.alert(msg, 'Error');
        }
    }

    $page.find('#btn-update-student').on('click', async () => {
        const form = new FormData();
        form.append('full_name', $page.find('#st-name').val());
        form.append('class_name', $page.find('#st-class').val());
        form.append('parent_email', $page.find('#st-parent').val());

        const photo = $page.find('#st-photo')[0].files[0];
        if (photo) form.append('photo', photo);

        try {
            await api(`/students/${id}`, { method: 'PUT', body: form });
            app.dialog.alert('Student updated successfully', 'Success', () => {
                app.views.main.router.back('/students/');
            });
        } catch (err) {
            const msg = typeof err === 'string'
                ? err
                : err.detail || err.message || 'An unexpected error occurred';
            app.dialog.alert(msg, 'Error');
        }
    });

    loadStudent();
}
