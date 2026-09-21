document.addEventListener('DOMContentLoaded', () => {
  initSidebar();
  loadDashboardSummary();
  initCalendar();
});

async function initSidebar() {
  try {
    const sidebarRes = await fetch('/sidebar.html');
    if (sidebarRes.status === 401) {
      window.location.href = '/login.html';
      return;
    }
    if (!sidebarRes.ok) throw new Error('Sidebar unavailable');
    document.getElementById('sidebar-placeholder').innerHTML = await sidebarRes.text();

    const userRes = await fetch('/api/current_user');
    if (userRes.status === 401) {
      window.location.href = '/login.html';
      return;
    }
    const user = await userRes.json();
    const name = user.fullname || 'Student';
    const sidebarName = document.getElementById('sidebar-username');
    const firstName = document.getElementById('user-first-name');
    if (sidebarName) sidebarName.textContent = name;
    if (firstName) firstName.textContent = name.split(' ')[0];

    const logoutBtn = document.getElementById('logout-Btn');
    if (logoutBtn) {
      logoutBtn.addEventListener('click', async () => {
        await fetch('/logout', { method: 'POST' });
        window.location.href = '/login.html';
      });
    }
  } catch (error) {
    const sidebar = document.getElementById('sidebar-placeholder');
    if (sidebar) sidebar.innerHTML = '<div class="sidebar-error">Unable to load navigation.</div>';
  }
}

async function loadDashboardSummary() {
  try {
    const res = await fetch('/api/student/dashboard/summary');
    if (res.status === 401) {
      window.location.href = '/login.html';
      return;
    }
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Unable to load dashboard');
    renderTeacherList(data.teachers || []);
    renderRecentNotes(data.recent_notes || []);
    renderAttendanceHistory(data.recent_attendance || []);
    renderRing('attendanceRing', 'attendancePct', data.attendance?.percent);
    renderRing('homeworkRing', 'homeworkPct', data.homework?.percent);
    renderRing('performanceRing', 'performancePct', data.performance?.percent);
    renderTodaySchedule(data.today_schedule || []);
  } catch (error) {
    document.querySelectorAll('.empty-hint').forEach(el => {
      if (el.textContent.includes('Loading')) el.textContent = 'Unable to load data right now.';
    });
  }
}

function initCalendar() {
  const table = document.getElementById('cal-table');
  const label = document.getElementById('cal-month-label');
  const prev = document.getElementById('cal-prev');
  const next = document.getElementById('cal-next');
  if (!table || !label || !prev || !next) return;

  const months = ['January','February','March','April','May','June','July','August','September','October','November','December'];
  const today = new Date();
  let year = today.getFullYear();
  let month = today.getMonth();

  function render() {
    table.querySelectorAll('tr:not(:first-child)').forEach(row => row.remove());
    label.textContent = months[month] + ' ' + year;
    const first = new Date(year, month, 1);
    const offset = (first.getDay() + 6) % 7;
    const days = new Date(year, month + 1, 0).getDate();
    let day = 1;
    for (let row = 0; row < 6 && day <= days; row++) {
      const tr = document.createElement('tr');
      for (let col = 0; col < 7; col++) {
        const td = document.createElement('td');
        if (!((row === 0 && col < offset) || day > days)) {
          td.textContent = day;
          if (day === today.getDate() && month === today.getMonth() && year === today.getFullYear()) td.className = 'active';
          day++;
        }
        tr.appendChild(td);
      }
      table.appendChild(tr);
    }
  }

  prev.addEventListener('click', () => { month--; if (month < 0) { month = 11; year--; } render(); });
  next.addEventListener('click', () => { month++; if (month > 11) { month = 0; year++; } render(); });
  render();
}

function renderRing(ringId, pctId, percent) {
  const ring = document.getElementById(ringId);
  const label = document.getElementById(pctId);
  if (!ring || !label) return;
  const value = Number(percent);
  if (!Number.isFinite(value)) {
    ring.style.strokeDashoffset = '213.6';
    label.textContent = '—';
    return;
  }
  const clamped = Math.max(0, Math.min(100, value));
  ring.style.strokeDashoffset = String(213.6 * (1 - clamped / 100));
  label.textContent = Math.round(clamped) + '%';
}

function renderTeacherList(teachers) {
  const el = document.getElementById('dashboard-teacher-list');
  if (!el) return;
  el.innerHTML = teachers.length ? teachers.map(t => '<div class="person-row"><div><div class="p-name">' + escapeHtml(t.mentor_name) + '</div><div class="p-sub">' + escapeHtml(t.class_name) + ' · ' + escapeHtml(t.subject) + '</div></div></div>').join('') : '<p class="empty-hint">No classes assigned yet.</p>';
}

function renderAttendanceHistory(records) {
  const el = document.getElementById('dashboard-attendance-history');
  if (!el) return;
  el.innerHTML = records.length ? records.map(item => '<div class="lesson-item"><div><div class="lesson-title">' + escapeHtml(item.class_name) + '</div><div class="lesson-time">' + escapeHtml(item.date) + ' · ' + escapeHtml(String(item.status || '').toUpperCase()) + '</div></div></div>').join('') : '<p class="empty-hint">No attendance records yet.</p>';
}

function renderRecentNotes(notes) {
  const el = document.getElementById('dashboard-recent-notes');
  if (!el) return;
  el.innerHTML = notes.length ? notes.map(n => '<div class="note-card"><div class="note-class">' + escapeHtml(n.class_name) + ' · ' + escapeHtml(n.mentor_name) + '</div><div class="note-title">' + escapeHtml(n.title) + '</div><div class="note-content">' + escapeHtml(n.content) + '</div><div class="note-date">' + escapeHtml(new Date(n.created_at).toLocaleDateString()) + '</div></div>').join('') : '<p class="empty-hint">No notes posted yet.</p>';
}

function renderTodaySchedule(slots) {
  const el = document.getElementById('dashboard-today-schedule');
  if (!el) return;
  el.innerHTML = slots.length ? slots.map(s => '<div class="lesson-item"><div><div class="lesson-title">' + escapeHtml(s.subject) + ' · ' + escapeHtml(s.class_name) + '</div><div class="lesson-time">' + escapeHtml(s.start_time) + ' – ' + escapeHtml(s.end_time) + (s.room ? ' · ' + escapeHtml(s.room) : '') + '</div></div></div>').join('') : '<p class="empty-hint">No classes scheduled for today.</p>';
}

function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
}
