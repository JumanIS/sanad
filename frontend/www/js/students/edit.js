import { api } from '../api.js';

export function StudentEditPage(page) {
    const app = page.app;
    const $ = app.$;
    const $page = $(page.el);
    const id = page.route.params.id;

    async function loadStudent() {
        const s = await api(`/students/${id}`);
        $page.find('#st-name').val(s.full_name);
        $page.find('#st-class').val(s.class_name);
    }

    $page.find('#btn-update-student').on('click', async () => {
        const form = new FormData();
        form.append('full_name', $page.find('#st-name').val());
        form.append('class_name', $page.find('#st-class').val());
        form.append('_method', 'PUT');

        try {
            await api(`/students/${id}`, { method: 'POST', body: form });
            app.toast.show({ text: 'Updated', closeTimeout: 1500 });
            app.views.main.router.back('/students/');
        } catch {
            app.toast.show({ text: 'Update failed', closeTimeout: 1500 });
        }
    });

    loadStudent();
}
