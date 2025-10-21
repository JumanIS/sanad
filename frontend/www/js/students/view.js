import { api } from '../api.js';

export function StudentViewPage(page) {
    const app = page.app;
    const $ = app.$;
    const $page = $(page.el);
    const id = page.route.params.id;
    const base = 'http://127.0.0.1:8000';

    async function loadStudent() {
        const s = await api(`/students/${id}`);
        $page.find('#student-photo').attr('src', s.photo ? base + '/storage/' + s.photo : 'https://placehold.co/120x120');
        $page.find('#student-name').text(s.full_name);
        $page.find('#student-class').text(s.class_name);

        const list = $page.find('#behaviors-list');
        if (s.behaviors?.length) {
            list.html(s.behaviors.map(b => `<li>${b.title || 'Behavior'} - ${b.created_at || ''}</li>`).join(''));
        } else list.html('<li>No behaviors recorded</li>');
    }

    $page.find('#edit-student-btn').on('click', () => {
        app.views.main.router.navigate(`/student-edit/${id}/`);
    });

    loadStudent();
}
