import { api } from '../api.js';

export function UserEditPage(page) {
    const app = page.app;
    const $ = app.$;
    const $page = $(page.el);
    const id = page.route.params.id;

    async function loadUser() {
        try {
            const u = await api(`/users/${id}`);
            $page.find('#u-name').val(u.name || '');
            $page.find('#u-email').val(u.email || '');
            $page.find('#u-password').val(''); // blank for security
            $page.find('#u-is-teacher').prop('checked', !!u.is_teacher);
        } catch (err) {
            const msg = err.detail || 'Failed to load user';
            app.dialog.alert(msg, 'Error');
        }
    }

    $page.find('#btn-update-user').on('click', async () => {
        const form = new FormData();
        form.append('name', $page.find('#u-name').val());
        form.append('email', $page.find('#u-email').val());
        const password = $page.find('#u-password').val();
        if (password) form.append('password', password);
        form.append('is_teacher', $page.find('#u-is-teacher').prop('checked') ? 'true' : 'false');
        form.append('_method', 'PUT');

        try {
            await api(`/users/${id}`, { method: 'PUT', body: form });
            app.dialog.alert('User updated successfully', 'Success', () => {
                app.views.main.router.navigate('/users/');
            });
        } catch (err) {
            const msg = typeof err === 'string'
                ? err
                : err.detail || err.message || 'An unexpected error occurred';
            app.dialog.alert(msg, 'Error');
        }
    });

    loadUser();
}
