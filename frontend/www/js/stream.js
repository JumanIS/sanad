import { api, getBaseURL } from './api.js';
import { getToken } from './auth.js';

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
    let stopping = false;

    async function checkSession() {
        try {
            const sessions = await api('/sessions');
            activeSession = sessions.find((s) => s.active) || null;
            await updateUI(activeSession ? activeSession.id : null);
        } catch (err) {
            const msg = typeof err === 'string' ? err : err.detail || err.message || 'Error';
            app.dialog.alert(msg, 'Error');
        }
    }

    async function stopSession(id) {
        if (stopping) return;
        stopping = true;
        try {
            await api(`/sessions/stop/${id}`, { method: 'POST' });
        } catch (_) {
            // ignore 404/409-like errors from idempotent stop
        } finally {
            stopping = false;
        }
    }

    function chooseSessionType() {
        return new Promise((resolve) => {
            const dlg = app.dialog.create({
                title: 'Start Session',
                content:
                    '<div class="list no-hairlines-md"><ul>' +
                    '<li><label class="item-radio item-content">' +
                    '<input type="radio" name="sessionType" value="normal" checked>' +
                    '<i class="icon icon-radio"></i>' +
                    '<div class="item-inner"><div class="item-title">Normal class</div></div>' +
                    '</label></li>' +
                    '<li><label class="item-radio item-content">' +
                    '<input type="radio" name="sessionType" value="exam">' +
                    '<i class="icon icon-radio"></i>' +
                    '<div class="item-inner"><div class="item-title">Exam</div></div>' +
                    '</label></li>' +
                    '</ul></div>',
                buttons: [
                    { text: 'Cancel', onClick: () => resolve(null) },
                    {
                        text: 'Start',
                        close: true,
                        onClick: (inst) => {
                            const val = $(inst.$el).find('input[name="sessionType"]:checked').val();
                            resolve(val === 'exam');
                        },
                    },
                ],
            });
            dlg.open();
        });
    }

    async function startSessionWithChoice() {
        const pick = await chooseSessionType();
        if (pick === null) return null; // canceled

        // Send multipart form for FastAPI Form(...)
        const fd = new FormData();
        fd.append('is_exam', String(pick));

        const res = await fetch(`${base}/sessions/start`, {
            method: 'POST',
            headers: { Authorization: 'Bearer ' + getToken() },
            body: fd,
        });

        if (!res.ok) {
            let msg = 'Failed to start session';
            try {
                const data = await res.json();
                if (data?.detail) msg = data.detail;
            } catch {}
            throw new Error(msg);
        }

        // Do not trust shape; re-sync from /sessions
        await checkSession();
        return activeSession;
    }

    async function updateUI(sessionId) {
        const $icon = $btn.find('i');
        const $text = $btn.find('span');

        if (sessionId) {
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
                if (stopping || !activeSession) return;
                try {
                    await stopSession(activeSession.id);
                } catch {}
                activeSession = null;
                await updateUI(null);
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
            $btn.removeClass('color-red').addClass('color-blue');
            $icon.text('play_circle_fill');
            $text.text('Start');

            $live.off('load error');
            $live.attr('src', 'data:,');
            $live.hide();

            $container.css({
                background: "url('./assets/camera_placeholder.png') center center no-repeat",
                'background-size': 'auto',
            });
        }
    }

    $btn.on('click', async () => {
        try {
            if (activeSession) {
                // prevent double-stop from <img> error handler
                $live.off('load error');
                $live.attr('src', 'data:,').hide();

                await stopSession(activeSession.id); // idempotent on backend
                activeSession = null;
                await updateUI(null);
            } else {
                await startSessionWithChoice(); // opens modal and posts is_exam
            }
        } catch (err) {
            const msg = typeof err === 'string' ? err : err.detail || err.message || 'Error';
            app.dialog.alert(msg, 'Error');
        }
    });

    checkSession();
}
