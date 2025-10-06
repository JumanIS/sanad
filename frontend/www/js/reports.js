import { api } from './api.js';

export default function (page) {
    const app = page.app;

    async function loadSessions() {
        const sess = await api('/sessions');
        const ul = app.$('#sessions-ul');
        ul.html('');
        sess.forEach(s => {
            ul.append(`<li class="item-content"><div class="item-inner">
        <div class="item-title">Session #${s.id}</div>
        <div class="item-after">${s.active ? 'Active' : 'Done'}</div>
      </div></li>`);
        });
    }

    app.$('#btn-load-student-report').on('click', async () => {
        const sid = app.$('#rep-student-id').val();
        const data = await api(`/students/${sid}`);
        const ul = app.$('#behaviors-ul');
        ul.html('');
        data.behaviors.forEach(b => {
            ul.append(`<li class="item-content"><div class="item-inner">
        <div class="item-title">${b.timestamp}</div>
        <div class="item-after">${b.behavior}</div>
      </div></li>`);
        });
    });

    loadSessions();
}
