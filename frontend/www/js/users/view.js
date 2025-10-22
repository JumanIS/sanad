import { api } from '../api.js';

export function UserViewPage(page) {
    const app = page.app;
    const $ = app.$;
    const $page = $(page.el);
    const id = page.route.params.id;

    async function loadUser() {
        try {
            const u = await api(`/users/${id}`);
            $page.find('#user-name').text(u.name || '');
            $page.find('#user-email').text(u.email || '');
            $page.find('#user-type').text(u.is_teacher ? 'Teacher' : 'Parent');
        } catch (err) {
            const msg = err.detail || 'Failed to load user';
            app.dialog.alert(msg, 'Error');
        }
    }

    // Edit user
    $page.find('#edit-user-btn').on('click', () => {
        app.views.main.router.navigate(`/user-edit/${id}/`);
    });

    // Delete user
    $page.find('#delete-user-btn').on('click', () => {
        app.dialog.confirm('Are you sure you want to delete this user?', 'Confirm', async () => {
            try {
                await api(`/users/${id}`, {
                    method: 'DELETE',
                });
                app.dialog.alert('User deleted successfully', 'Success', () => {
                    app.views.main.router.navigate('/users/');
                });
            } catch (err) {
                const msg = typeof err === 'string'
                    ? err
                    : err.detail || err.message || 'An unexpected error occurred';
                app.dialog.alert(msg, 'Error');
            }
        });
    });

    loadUser();
}
