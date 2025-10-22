export default [
    { path: '/', redirect: '/students/' },
    { path: '/login/', url: './pages/login.html' },
    { path: '/stream/', url: './pages/stream.html' },
    { path: '/reports/', url: './pages/reports.html' },

    { path: '/students/', url: './pages/students/list.html' },
    { path: '/student-add/', url: './pages/students/add.html' },
    { path: '/student-edit/:id/', url: './pages/students/edit.html' },
    { path: '/student-view/:id/', url: './pages/students/view.html' },

    { path: '/users/', url: './pages/users/list.html' },
    { path: '/user-add/', url: './pages/users/add.html' },
    { path: '/user-edit/:id/', url: './pages/users/edit.html' },
    { path: '/user-view/:id/', url: './pages/users/view.html' },
];
