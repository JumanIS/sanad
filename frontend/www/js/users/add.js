import { api } from '../api.js';

export function UserAddPage(page) {
    const app = page.app;
    const $ = app.$;
    const $page = $(page.el);

    $page.find('#btn-save-user').on('click', async () => {
        const form = new FormData();
        form.append('name', $page.find('#u-name').val());
        form.append('email', $page.find('#u-email').val());
        form.append('password', $page.find('#u-password').val());
        form.append('is_teacher', $page.find('#u-is-teacher').prop('checked') ? 'true' : 'false');

        try {
            await api('/users', { method: 'POST', body: form });
            app.dialog.alert('User added successfully', 'Success', () => {
                app.views.main.router.navigate('/users/');
            });
        } catch (err) {
            const msg = typeof err === 'string'
                ? err
                : err.detail || err.message || 'An unexpected error occurred';
            app.dialog.alert(msg, 'Error');
        }
    });
}
