import { api } from '../api.js';

export function StudentAddPage(page) {
    const app = page.app;
    const $ = app.$;
    const $page = $(page.el);

    $page.find('#btn-save-student').on('click', async () => {
        const form = new FormData();
        form.append('full_name', $page.find('#st-name').val());
        form.append('class_name', $page.find('#st-class').val());
        form.append('parent_email', $page.find('#st-parent').val());
        const f = $page.find('#st-photo')[0].files[0];
        if (f) form.append('photo', f);

        try {
            await api('/students', { method: 'POST', body: form });
            app.toast.show({ text: 'Student added', closeTimeout: 1500 });
            app.views.main.router.navigate('/students/');
        } catch {
            app.toast.show({ text: 'Failed to save', closeTimeout: 1500 });
        }
    });
}
