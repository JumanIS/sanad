import { api } from './api.js';
import { getToken } from './auth.js';

export default function (page) {
    const app = page.app;
    const token = getToken();
    let currentSession = null;

    app.$('#btn-start-session').on('click', async () => {
        const res = await api('/sessions/start', { method: 'POST' });
        currentSession = res.session_id;
        app.$('#cur-session-id').text(currentSession);
        app.$('#cur-session-status').text('active');
        const img = app.$('#stream-img');
        img.attr('src', `http://127.0.0.1:8000/detect/stream?session_id=${currentSession}&auth=Bearer%20${token}`);
    });

    app.$('#btn-stop-session').on('click', async () => {
        if (!currentSession) return;
        await api(`/sessions/stop/${currentSession}`, { method: 'POST' });
        app.$('#cur-session-status').text('stopped');
        app.$('#stream-img').attr('src', '');
        currentSession = null;
    });
}
