let token = null;
let streaming = false;

function showPage(id){
    document.querySelectorAll('main section').forEach(s => s.classList.remove('active'));
    document.getElementById(id).classList.add('active');

    if (id === 'students') {
        // Always reset to list view
        document.getElementById('student-form').style.display = 'none';
        document.getElementById('student-view').style.display = 'none';
        document.getElementById('students-list').style.display = 'block';
        loadStudents();
        stopStream(); // make sure stream is stopped when switching
    }

    if (id === 'stream') {
        startStream(); // always auto-start
    }

    if (id !== 'stream') {
        stopStream();
    }
}


document.getElementById('btn-login').onclick = async () => {
    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value.trim();
    const res = await fetch('/auth/login', {
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body: JSON.stringify({email, password})
    });
    const data = await res.json();
    if (res.ok) {
        token = data.token;
        document.getElementById('login').classList.remove('active');
        document.getElementById('navbar').style.display = 'flex';
        showPage('students');
        loadStudents();
    } else {
        alert(data.message || 'login failed');
    }
};

document.getElementById('btn-toggle').onclick = () => {
    if (streaming) stopStream();
    else startStream();
};

function startStream(){
    if (!token) { alert('login first'); return; }
    const img = document.getElementById('stream-img');
    img.src = `/detect/stream?auth=Bearer%20${encodeURIComponent(token)}`;
    document.getElementById('btn-toggle').innerText = 'Stop Stream';
    streaming = true;
}

function stopStream(){
    const img = document.getElementById('stream-img');
    img.src = '';
    document.getElementById('btn-toggle').innerText = 'Start Stream';
    streaming = false;
}

async function loadStudents(){
    const res = await fetch('/students', {headers:{Authorization:`Bearer ${token}`}});
    const data = await res.json();
    const tbody = document.querySelector('#students-table tbody');
    tbody.innerHTML = '';
    data.forEach(st=>{
        const tr = document.createElement('tr');
        tr.innerHTML = `
      <td>${st.full_name}</td>
      <td>${st.class_name||''}</td>
      <td>
        <button onclick="viewStudent(${st.id})">View</button>
        <button onclick="deleteStudent(${st.id})">Delete</button>
      </td>`;
        tbody.appendChild(tr);
    });
}

async function viewStudent(id){
    const res = await fetch(`/students/${id}`, {headers:{Authorization:`Bearer ${token}`}});
    const st = await res.json();
    let html = `<h4>${st.full_name}</h4>
    <img src="/images/${st.photo}" width="160">
    <p>Class: ${st.class_name||''}</p>
    <h5>Behaviors</h5>
    <table class="behaviors-table">
      <thead><tr><th>Time</th><th>Behavior</th><th>Confidence</th></tr></thead>
      <tbody>`;
    st.behaviors.forEach(b=>{
        html += `<tr><td>${b.timestamp}</td><td>${b.behavior}</td><td>${b.confidence.toFixed(2)}</td></tr>`;
    });
    html += '</tbody></table>';
    document.getElementById('student-detail').innerHTML = html;

    document.getElementById('students-list').style.display = 'none';
    document.getElementById('student-form').style.display = 'none';
    document.getElementById('student-view').style.display = 'block';
}

function showAddStudent(){
    document.getElementById('students-list').style.display = 'none';
    document.getElementById('student-view').style.display = 'none';
    document.getElementById('student-form').style.display = 'block';
}

function cancelAdd(){
    document.getElementById('student-form').style.display = 'none';
    document.getElementById('students-list').style.display = 'block';
}


function backToList(){
    document.getElementById('student-form').style.display = 'none';
    document.getElementById('student-view').style.display = 'none';
    document.getElementById('students-list').style.display = 'block';
}

async function submitStudent(){
    const name = document.getElementById('new-name').value.trim();
    const className = document.getElementById('new-class').value.trim();
    const photo = document.getElementById('new-photo').files[0];
    if (!name || !photo) { alert("Name and photo required"); return; }

    const formData = new FormData();
    formData.append("full_name", name);
    formData.append("class_name", className);
    formData.append("photo", photo);

    const res = await fetch('/students', {
        method:'POST',
        headers:{Authorization:`Bearer ${token}`},
        body: formData
    });
    if (res.ok) {
        alert("Student added");
        cancelAdd();
        loadStudents();
    } else {
        const data = await res.json();
        alert(data.message || "Error");
    }
}

async function deleteStudent(id){
    if (!confirm('Delete student?')) return;
    await fetch(`/students/${id}`, {
        method:'DELETE',
        headers:{Authorization:`Bearer ${token}`}
    });
    loadStudents();
}
