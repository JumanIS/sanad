import { api } from './api.js';
console.log('students.js loaded');
document.addEventListener('page:init', e => {
    console.log('Global event fired:', e.detail.name);
});
export default function (page) {
    console.log('students.js inside', page.name);
    const app = page.app;
    const $ = app.$;
    const $page = $(page.el);

    async function loadStudents() {
        const list = $page.find('#students-ul');
        list.html('<li><div class="item-inner"><div class="item-title small-muted">Loading...</div></div></li>');
        try {
            const students = await api('/students');
            list.html('');
            if (!students.length) {
                list.html('<li><div class="item-inner"><div class="item-title small-muted">No students yet</div></div></li>');
                return;
            }
            students.forEach(s => {
                const photo = s.photo ? `http://127.0.0.1:8000/images/${s.photo}` : 'img/avatar.png';
                list.append(`
          <li>
            <div class="item-content">
              <div class="item-media"><img src="${photo}" class="avatar" /></div>
              <div class="item-inner">
                <div class="item-title-row">
                  <div class="item-title">${s.full_name}</div>
                  <div class="item-after">${s.class_name || ''}</div>
                </div>
              </div>
            </div>
          </li>
        `);
            });
        } catch (e) {
            list.html('<li><div class="item-inner"><div class="item-title color-red">Failed to load</div></div></li>');
            console.error(e);
        }
    }

    // toggle form
    $page.on('click', '#btn-toggle-form', (e) => {
        e.preventDefault();
        $page.find('#add-student-form').toggleClass('hide');
    });

    // save student
    $page.on('click', '#btn-save-student', async (e) => {
        e.preventDefault();
        const name = $page.find('#st-name').val().trim();
        const className = $page.find('#st-class').val().trim();
        const parent = $page.find('#st-parent').val().trim();
        const photo = $page.find('#st-photo')[0].files[0];
        if (!name || !photo) { app.dialog.alert('Name and photo required'); return; }

        const form = new FormData();
        form.append('full_name', name);
        form.append('class_name', className);
        form.append('parent_email', parent);
        form.append('photo', photo);

        try {
            await api('/students', { method: 'POST', body: form });
            app.toast.create({ text: 'Saved', closeTimeout: 1500 }).open();
            $page.find('#st-name,#st-class,#st-parent').val('');
            $page.find('#st-photo').val('');
            $page.find('#add-student-form').addClass('hide');
            loadStudents();
        } catch (err) {
            app.dialog.alert('Save failed');
            console.error(err);
        }
    });

    loadStudents();
}
