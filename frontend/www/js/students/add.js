import { api } from '../api.js';

export function StudentAddPage(page) {
    const app = page.app;
    const $ = app.$;
    const $page = $(page.el);

    $page.find('#btn-save-student').on('click', async () => {
        const name = $page.find('#st-name').val();
        const cls = $page.find('#st-class').val();
        const photo = $page.find('#st-photo')[0].files[0];

        const form = new FormData();
        form.append('full_name', name);
        form.append('class_name', cls);
        if (photo) form.append('photo', photo);

        try {
            await api('/students', { method: 'POST', body: form });
            app.toast.show({ text: 'Student added', closeTimeout: 1500 });
            app.views.main.router.back('/students/');
        } catch {
            app.toast.show({ text: 'Failed to save', closeTimeout: 1500 });
        }
    });
}
