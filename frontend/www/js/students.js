import { api } from './api.js';

export default function studentsPage(page) {
    console.log(page);
    const app = page.app;
    const $ = app.$;

    // DOM references scoped to this page
    const $page = $(page.el);
    const $form = $page.find('#add-student-form');
    const $btnToggleForm = $page.find('#btn-toggle-form');
    const $btnSave = $page.find('#btn-save-student');
    const $list = $page.find('#students-ul');

    let editingId = null;
    let isTeacher = false;

    console.log('students.js loaded');

    // ===========================
    // Role check
    // ===========================
    async function checkRole() {
        try {
            const me = await api('/me');
            if (me.is_teacher) {
                document.getElementById('add_student_btn').style.display = 'inline-flex';
            } else {
                document.getElementById('add_student_btn').style.display = 'none';
            }
        } catch {
            console.warn('Failed to get role');
        }
    }

    // ===========================
    // Load students
    // ===========================
    async function loadStudents() {
        $list.html('<li><div class="item-content"><div class="item-inner"><div class="item-title">Loading...</div></div></div></li>');
        try {
            const data = await api('/students');
            renderList(data);
        } catch {
            $list.html('<li><div class="item-content"><div class="item-inner"><div class="item-title color-red">Failed to load students</div></div></div></li>');
        }
    }

    function renderList(arr) {
        if (!arr.length) {
            $list.html('<li><div class="item-content"><div class="item-inner"><div class="item-title">No students</div></div></div></li>');
            return;
        }
        const html = arr.map(s => `
        <li>
          <a class="item-link item-content" data-id="${s.id}" data-action="details">
            <div class="item-media">
                <img src="${s.photo ? 'http://127.0.0.1:8000/images/' + s.photo : 'https://placehold.co/64x64?text=👤'}" width="48" height="48" style="border-radius:50%" alt="">
            </div>
            <div class="item-inner">
              <div class="item-title">
                <div class="item-header">${s.class_name || ''}</div>
                ${s.full_name}
              </div>
              <div class="item-after"></div>
            </div>
          </a>
        </li>
      <li>
        `).join('');
        $list.html(html);
    }

    // ===========================
    // Add / Edit / Delete / Details
    // ===========================
    async function saveStudent() {
        const form = new FormData();
        form.append('full_name', $page.find('#st-name').val());
        form.append('class_name', $page.find('#st-class').val());
        const parent = $page.find('#st-parent').val();
        const file = $page.find('#st-photo')[0].files[0];
        if (parent) form.append('parent_email', parent);
        if (file) form.append('photo', file);

        let url = '/students';
        let method = 'POST';
        if (editingId) {
            url = `/students/${editingId}`;
            form.append('_method', 'PUT');
        }

        try {
            await api(url, { method, body: form });
            app.toast.show({ text: 'Saved', closeTimeout: 1500 });
            $form.addClass('hide');
            editingId = null;
            loadStudents();
        } catch {
            app.toast.show({ text: 'Save failed', closeTimeout: 1500 });
        }
    }

    async function deleteStudent(id) {
        if (!confirm('Delete student?')) return;
        try {
            await api(`/students/${id}`, { method: 'DELETE' });
            app.toast.show({ text: 'Deleted', closeTimeout: 1500 });
            loadStudents();
        } catch {
            app.toast.show({ text: 'Delete failed', closeTimeout: 1500 });
        }
    }

    async function showDetails(id) {
        try {
            const s = await api(`/students/${id}`);
            const behaviors = s.behaviors?.length
                ? `<ul>${s.behaviors.map(b => `<li>${b.title || 'Behavior'} - ${b.created_at || ''}</li>`).join('')}</ul>`
                : '<div class="block">No behaviors</div>';
            app.dialog.create({
                title: s.full_name,
                text: `<div>Class: ${s.class_name}</div><br>${behaviors}`,
                buttons: [{ text: 'Close', close: true }],
            }).open();
        } catch {
            app.toast.show({ text: 'Failed to load details', closeTimeout: 1500 });
        }
    }

    // ===========================
    // Events (bound inside page)
    // ===========================
    $btnToggleForm.on('click', () => {
        console.log('Add button clicked');
        if (!isTeacher) return app.toast.show({ text: 'Not allowed', closeTimeout: 1500 });
        $form.toggleClass('hide');
        editingId = null;
    });

    $btnSave.on('click', saveStudent);

    $list.on('click', 'a[data-action]', (e) => {
        const $el = $(e.currentTarget);
        const id = $el.data('id');
        const action = $el.data('action');
        if (action === 'edit') {
            if (!isTeacher) return app.toast.show({ text: 'Not allowed', closeTimeout: 1500 });
            editingId = id;
            $form.removeClass('hide');
        } else if (action === 'delete') {
            if (!isTeacher) return app.toast.show({ text: 'Not allowed', closeTimeout: 1500 });
            deleteStudent(id);
        } else if (action === 'details') {
            showDetails(id);
        }
    });
    console.log('studentsPage() executed');

    // ===========================
    // Init page
    // ===========================
    checkRole();
    loadStudents();
}
