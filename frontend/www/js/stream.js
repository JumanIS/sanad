import { api, getBaseURL } from './api.js';
import {getToken} from "./auth.js";

export function StreamPage(page) {
    const token = getToken();
    if (!token) return;

    const app = page.app;
    const $ = app.$;
    const $page = $(page.el);

    const base = getBaseURL();
    const user = JSON.parse(localStorage.getItem('user') || '{}');

    if (!user.is_teacher) {
        app.views.main.router.navigate('/students/');
        return;
    }

    const $btn = $page.find('#toggle-session-btn');
    const $live = $page.find('#live-stream');
    const $container = $page.find('#stream-container');

    let activeSession = null;
    let stopping = false; // <--- guard flag

    async function checkSession() {
        try {
            const sessions = await api('/sessions');
            activeSession = sessions.find((s) => s.active) || null;
            await updateUI(activeSession ? activeSession.id : null);
        } catch (err) {
            const msg =
                typeof err === 'string'
                    ? err
                    : err.detail || err.message || 'An unexpected error occurred';
            app.dialog.alert(msg, 'Error');
        }
    }

    async function stopSession(id) {
        if (stopping) return; // prevent double stop
        stopping = true;
        try {
            if (id) await api(`/sessions/stop/${id}`, { method: 'POST' });
        } catch {}
        stopping = false;
    }

    async function updateUI(sessionId) {
        const $icon = $btn.find('i');
        const $text = $btn.find('span');

        if (sessionId) {
            // ===== ACTIVE SESSION =====
            $btn.removeClass('color-blue').addClass('color-red');
            $icon.text('stop_circle_fill');
            $text.text('Stop');
            $container.css('background', 'none');

            const src = `${base}/detect/stream?session_id=${sessionId}&_=${Date.now()}`;

            $live.off('load error');
            $live.attr('src', '');
            $live.on('load', () => {
                $container.css('background', 'none');
            });
            $live.on('error', async (e) => {
                console.warn('stream error', e);
                try {
                    await stopSession(sessionId);
                } catch {}

                activeSession = null;
                await updateUI(null);

                // read message from the last failed response if available
                let msg = 'Camera not available';
                try {
                    const res = await fetch(`${base}/detect/stream?session_id=${sessionId}`);
                    const data = await res.json().catch(() => ({}));
                    if (data.detail) msg = data.detail;
                } catch (err) {
                    if (err?.message) msg = err.message;
                }

                app.dialog.alert(msg, 'Error');
            });


            $live.attr('src', src).show();
        } else {
            // ===== STOPPED =====
            $btn.removeClass('color-red').addClass('color-blue');
            $icon.text('play_circle_fill');
            $text.text('Start');

            $live.off('load error');
            $live.attr('src', 'data:,');
            $live.hide();

            $container.css({
                background:
                    "url('./assets/camera_placeholder.png') center center no-repeat",
                'background-size': 'auto',
            });
        }
    }

    $btn.on('click', async () => {
        try {
            if (activeSession) {
                // Stop session manually
                $live.attr('src', 'data:,').hide();
                await stopSession(activeSession.id);
                activeSession = null;
                await updateUI(null);
            } else {
                // Start new session
                const res = await api('/sessions/start', { method: 'POST' });
                activeSession = res;
                await updateUI(activeSession ? activeSession.id : null);
            }
        } catch (err) {
            const msg =
                typeof err === 'string'
                    ? err
                    : err.detail || err.message || 'An unexpected error occurred';
            app.dialog.alert(msg, 'Error');
        }
    });

    checkSession();
}
