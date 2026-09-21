document.addEventListener('DOMContentLoaded', () => {
  loadMentorSidebar('attendance');

  const dateInput = document.getElementById('attendanceDate');
  dateInput.value = todayISO();
  dateInput.addEventListener('change', loadAttendance);

  window.addEventListener('classChanged', (e) => {
    activeClass = e.detail || null;
    updateHeading();
    loadRoster();
  });

  window.addEventListener('classesUpdated', (e) => {
    if ((e.detail || []).length === 0) {
      activeClass = null;
      updateHeading();
      renderRoster([]);
      renderAttendance([]);
    }
  });

  setupAddStudentForm();
  document.getElementById('saveAttendanceBtn').addEventListener('click', saveAttendance);
});

let activeClass = null;
let currentRecords = []; // [{student_id, fullname, email, status}]

function todayISO() {
  const d = new Date();
  const pad = n => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

function updateHeading() {
  const heading = document.getElementById('attendanceActiveClass');
  if (!heading) return;
  heading.textContent = activeClass
    ? `Managing roster and attendance for ${activeClass.class_name}.`
    : 'Add or select a class above to take attendance.';
}

function loadRoster() {
  const list = document.getElementById('rosterList');
  if (!list) return;

  if (!activeClass) {
    list.innerHTML = '<p class="empty-hint">Select a class above to see its roster.</p>';
    renderAttendance([]);
    return;
  }

  list.innerHTML = '<p class="empty-hint">Loading…</p>';

  fetch(`/api/classes/${activeClass.id}/students`)
    .then(res => {
      if (res.status === 401 || res.status === 403) {
        window.location.href = res.status === 403 ? '/mentor/onboarding.html' : '/login.html?role=mentor';
        return null;
      }
      return res.json();
    })
    .then(data => {
      if (!data) return;
      renderRoster(data.students || []);
      loadAttendance();
    })
    .catch(err => {
      console.error('Failed to load roster:', err);
      list.innerHTML = '<p class="empty-hint">Could not load roster.</p>';
    });
}

function renderRoster(students) {
  const list = document.getElementById('rosterList');
  if (!list) return;
  list.innerHTML = '';

  if (!activeClass) {
    list.innerHTML = '<p class="empty-hint">Select a class above to see its roster.</p>';
    return;
  }
  if (students.length === 0) {
    list.innerHTML = '<p class="empty-hint">No students added yet.</p>';
    return;
  }

  students.forEach(s => {
    const row = document.createElement('div');
    row.className = 'roster-row';
    row.innerHTML = `
      <div>
        <div class="roster-name">${escapeHtml(s.fullname)}</div>
        <div class="roster-email">${escapeHtml(s.email)}</div>
      </div>
      <button type="button" class="roster-remove" title="Remove student" data-id="${s.id}">✕</button>
    `;
    row.querySelector('.roster-remove').addEventListener('click', () => removeStudent(s.id));
    list.appendChild(row);
  });
}

function removeStudent(studentId) {
  if (!activeClass) return;
  if (!window.confirm('Remove this student from the selected class?')) return;
  fetch(`/api/classes/${activeClass.id}/students/${studentId}`, { method: 'DELETE' })
    .then(res => {
      if (res.status === 401) {
        window.location.href = r.status === 403 ? '/mentor/onboarding.html' : '/login.html?role=mentor';
        return null;
      }
      return res.json();
    })
    .then(data => {
      if (data) loadRoster();
    })
    .catch(err => console.error('Failed to remove student:', err));
}

function setupAddStudentForm() {
  const form = document.getElementById('addStudentForm');
  const message = document.getElementById('rosterMessage');
  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    message.textContent = '';

    if (!activeClass) {
      message.textContent = 'Add or select a class first.';
      message.style.color = '#d1567f';
      return;
    }

    const email = document.getElementById('studentEmail').value.trim();
    if (!email) {
      message.textContent = 'Enter a student email.';
      message.style.color = '#d1567f';
      return;
    }

    try {
      const res = await fetch(`/api/classes/${activeClass.id}/students`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
      });

      if (res.status === 401) {
        window.location.href = '/login.html?role=mentor';
        return;
      }

      const data = await res.json();

      if (!res.ok) {
        message.textContent = data.error || 'Something went wrong.';
        message.style.color = '#d1567f';
        return;
      }

      message.textContent = 'Student added!';
      message.style.color = '#5aada0';
      form.reset();
      loadRoster();
    } catch (err) {
      console.error(err);
      message.textContent = 'Server error. Please try again.';
      message.style.color = '#d1567f';
    }
  });
}

function loadAttendance() {
  const list = document.getElementById('attendanceList');
  if (!list) return;

  if (!activeClass) {
    list.innerHTML = '<p class="empty-hint">Select a class above to take attendance.</p>';
    return;
  }

  const date = document.getElementById('attendanceDate').value || todayISO();
  list.innerHTML = '<p class="empty-hint">Loading…</p>';

  fetch(`/api/attendance?class_id=${activeClass.id}&date=${date}`)
    .then(res => {
      if (res.status === 401) {
        window.location.href = '/login.html?role=mentor';
        return null;
      }
      return res.json();
    })
    .then(data => {
      if (!data) return;
      renderAttendance(data.records || []);
    })
    .catch(err => {
      console.error('Failed to load attendance:', err);
      list.innerHTML = '<p class="empty-hint">Could not load attendance.</p>';
    });
}

function renderAttendance(records) {
  currentRecords = records.map(r => ({ ...r }));
  const list = document.getElementById('attendanceList');
  if (!list) return;
  list.innerHTML = '';

  if (!activeClass) {
    list.innerHTML = '<p class="empty-hint">Select a class above to take attendance.</p>';
    return;
  }
  if (records.length === 0) {
    list.innerHTML = '<p class="empty-hint">Add students to the roster first.</p>';
    return;
  }

  records.forEach(r => {
    const row = document.createElement('div');
    row.className = 'attendance-row';
    row.dataset.studentId = r.student_id;
    row.innerHTML = `
      <div class="attendance-name">${r.fullname}</div>
      <div class="attendance-toggle">
        <button type="button" class="attendance-btn present${r.status === 'present' ? ' active' : ''}" data-status="present">Present</button>
        <button type="button" class="attendance-btn absent${r.status === 'absent' ? ' active' : ''}" data-status="absent">Absent</button>
      </div>
    `;
    row.querySelectorAll('.attendance-btn').forEach(btn => {
      btn.addEventListener('click', () => setStatus(r.student_id, btn.dataset.status, row));
    });
    list.appendChild(row);
  });
}

function setStatus(studentId, status, row) {
  const record = currentRecords.find(r => r.student_id === studentId);
  if (record) record.status = status;
  row.querySelectorAll('.attendance-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.status === status);
  });
}

function saveAttendance() {
  const message = document.getElementById('attendanceMessage');
  message.textContent = '';

  if (!activeClass) {
    message.textContent = 'Select a class first.';
    message.style.color = '#d1567f';
    return;
  }

  const date = document.getElementById('attendanceDate').value || todayISO();
  const records = currentRecords
    .filter(r => r.status === 'present' || r.status === 'absent')
    .map(r => ({ student_id: r.student_id, status: r.status }));

  if (records.length === 0) {
    message.textContent = 'Mark at least one student before saving.';
    message.style.color = '#d1567f';
    return;
  }

  fetch('/api/attendance', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ class_id: activeClass.id, date, records }),
  })
    .then(res => {
      if (res.status === 401) {
        window.location.href = '/login.html?role=mentor';
        return null;
      }
      return res.json().then(data => ({ ok: res.ok, data }));
    })
    .then(result => {
      if (!result) return;
      if (!result.ok) {
        message.textContent = result.data.error || 'Something went wrong.';
        message.style.color = '#d1567f';
        return;
      }
      message.textContent = 'Attendance saved!';
      message.style.color = '#5aada0';
    })
    .catch(err => {
      console.error(err);
      message.textContent = 'Server error. Please try again.';
      message.style.color = '#d1567f';
    });
}