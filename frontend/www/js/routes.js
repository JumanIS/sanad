export default [
    { path: '/', url: './pages/students.html' },
    { path: '/login/', url: './pages/login.html' },
    { path: '/users/', url: './pages/users.html' },
    // { path: '/students/', url: './pages/students.html' },
    { path: '/stream/', url: './pages/stream.html' },
    { path: '/reports/', url: './pages/reports.html' },

    { path: '/students/', url: './pages/students/list.html' },
    { path: '/student-add/', url: './pages/students/add.html' },
    { path: '/student-edit/:id/', url: './pages/students/edit.html' },
    { path: '/student-view/:id/', url: './pages/students/view.html' },
];
