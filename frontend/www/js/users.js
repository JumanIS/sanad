import { api } from './api.js';
export default function (page) {
    const app = page.app;

    app.$('#btn-create-user').on('click', async () => {
        const name = app.$('#user-name').val();
        const email = app.$('#user-email').val();
        const password = app.$('#user-password').val();
        const is_teacher = app.$('#user-role').val();
        const form = new FormData();
        form.append('name', name);
        form.append('email', email);
        form.append('password', password);
        form.append('is_teacher', is_teacher);
        await api('/users', { method: 'POST', body: form });
        app.dialog.alert('User created');
    });
}
