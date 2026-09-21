document.addEventListener("DOMContentLoaded", async () => {

fetch('/sidebar.html')
  .then(res => {
    if (res.status === 401) {
      window.location.href = '/login.html';
      return null;
    }
    return res.text();
  })
  .then(data => {
    if (!data) return;
    document.getElementById('sidebar-placeholder').innerHTML = data;
    initSidebar();
  })
  .catch(err => console.error('Failed to load sidebar:', err));

function initSidebar() {
  const usernameEl = document.getElementById('sidebar-username');
  if (usernameEl) {
    fetch('/api/current_user')
      .then(r => r.json())
      .then(u => {
        if (u.status === 'success') usernameEl.textContent = u.fullname;
      });
  }

  const logoutBtn = document.getElementById('logout-Btn');
  if (logoutBtn) {
    logoutBtn.addEventListener('click', () => {
      fetch('/logout', { method: 'POST' })
        .then(() => window.location.href = '/login.html');
    });
  }
}

  // ---- username fetch ----
  try {
    const res = await fetch("/api/current_user");
    if (res.status === 401) {
      window.location.href = "/login.html";
      return;
    }
    const data = await res.json();
    document.getElementById("sidebar-username").textContent = data.fullname;
    document.getElementById("user-first-name").textContent =
      data.fullname.split(" ")[0].toUpperCase();
  } catch (err) {
    console.error("Failed to load user info:", err);
  }

  // ---- dashboard summary ----
  loadDashboardSummary();

  const monthNames = ["January","February","March","April","May","June",
    "July","August","September","October","November","December"];

  let today = new Date();
  let viewYear = today.getFullYear();
  let viewMonth = today.getMonth();

  function renderCalendar(year, month) {
    const table = document.getElementById('cal-table');
    const label = document.getElementById('cal-month-label');

    table.querySelectorAll('tr:not(:first-child)').forEach(row => row.remove());
    label.textContent = `${monthNames[month]} ${year}`;

    const firstDay = new Date(year, month, 1);
    let startOffset = (firstDay.getDay() + 6) % 7;
    const daysInMonth = new Date(year, month + 1, 0).getDate();

    let date = 1;
    for (let row = 0; row < 6 && date <= daysInMonth; row++) {
      const tr = document.createElement('tr');
      for (let col = 0; col < 7; col++) {
        const td = document.createElement('td');
        if (row === 0 && col < startOffset) {
          td.textContent = '';
        } else if (date > daysInMonth) {
          td.textContent = '';
        } else {
          td.textContent = date;
          const isToday = date === today.getDate() &&
                           month === today.getMonth() &&
                           year === today.getFullYear();
          if (isToday) td.classList.add('active');
          date++;
        }
        tr.appendChild(td);
      }
      table.appendChild(tr);
    }
  }

  document.getElementById('cal-prev').addEventListener('click', () => {
    viewMonth--;
    if (viewMonth < 0) { viewMonth = 11; viewYear--; }
    renderCalendar(viewYear, viewMonth);
  });

  document.getElementById('cal-next').addEventListener('click', () => {
    viewMonth++;
    if (viewMonth > 11) { viewMonth = 0; viewYear++; }
    renderCalendar(viewYear, viewMonth);
  });

  renderCalendar(viewYear, viewMonth);

  document.getElementById("logout-Btn").addEventListener('click', function(){
    fetch("/logout", {method:"POST"})
        .then(function(response){
            return response.json();
        })
        .then(function(data){
            if(data.status === "success"){
                window.location.href = "/login.html";
            }
        })
  });
});

const RING_CIRCUMFERENCE = 213.6;

function loadDashboardSummary() {
  fetch('/api/student/dashboard/summary')
    .then(res => {
      if (res.status === 401) {
        window.location.href = '/login.html';
        return null;
      }
      return res.json();
    })
    .then(data => {
      if (!data) return;
      renderTeacherList(data.teachers || []);
      renderRecentNotes(data.recent_notes || []);
      renderAttendanceHistory(data.recent_attendance || []);
      renderRing('attendanceRing', 'attendancePct', data.attendance ? data.attendance.percent : null, '#d1567f');
      renderRing('homeworkRing', 'homeworkPct', data.homework ? data.homework.percent : null, '#5aada0');
      renderRing('performanceRing', 'performancePct', data.performance ? data.performance.percent : null, '#e0aa4e');
      renderTodaySchedule(data.today_schedule || []);
    })
    .catch(err => {
      console.error('Failed to load dashboard summary:', err);
      const teacherList = document.getElementById('dashboard-teacher-list');
      if (teacherList) teacherList.innerHTML = '<p class="empty-hint">Could not load dashboard data.</p>';
    });
}

function renderTeacherList(teachers) {
  const el = document.getElementById('dashboard-teacher-list');
  if (!el) return;

  if (teachers.length === 0) {
    el.innerHTML = '<p class="empty-hint">You\'re not enrolled in any classes yet.</p>';
    return;
  }

  el.innerHTML = '';
  teachers.forEach(t => {
    const row = document.createElement('div');
    row.className = 'person-row';
    row.innerHTML = `
      <div>
        <div class="p-name">${t.mentor_name}</div>
        <div class="p-sub">${t.class_name} · ${t.subject}</div>
      </div>`;
    el.appendChild(row);
  });
}

function renderRing(ringId, pctId, percent, color) {
  const ring = document.getElementById(ringId);
  const pctEl = document.getElementById(pctId);
  if (!ring || !pctEl) return;

  if (percent === null || percent === undefined) {
    ring.setAttribute('stroke-dashoffset', RING_CIRCUMFERENCE);
    pctEl.textContent = '–';
    return;
  }

  const clamped = Math.max(0, Math.min(100, percent));
  const offset = RING_CIRCUMFERENCE * (1 - clamped / 100);
  ring.setAttribute('stroke-dashoffset', offset.toFixed(1));
  ring.setAttribute('stroke', color);
  pctEl.textContent = `${Math.round(clamped)}%`;
}

function renderTodaySchedule(slots) {
  const el = document.getElementById('dashboard-today-schedule');
  if (!el) return;

  if (slots.length === 0) {
    el.innerHTML = '<p class="empty-hint">No classes scheduled for today.</p>';
    return;
  }

  el.innerHTML = '';
  slots.forEach(s => {
    const item = document.createElement('div');
    item.className = 'lesson-item';
    item.innerHTML = `
      <div>
        <div class="lesson-title">${s.subject} · ${s.class_name}</div>
        <div class="lesson-time">${s.start_time} – ${s.end_time}${s.room ? ' · ' + s.room : ''}</div>
      </div>`;
    el.appendChild(item);
  });
}


function renderAttendanceHistory(records) {
  const el = document.getElementById('dashboard-attendance-history');
  if (!el) return;
  if (!records.length) {
    el.innerHTML = '<p class="empty-hint">No attendance records yet.</p>';
    return;
  }
  el.innerHTML = records.map(item => `
    <div class="lesson-item">
      <div class="lesson-title">${escapeHtml(item.class_name)}</div>
      <div class="lesson-time">${escapeHtml(item.date)} · ${escapeHtml(item.status)}</div>
    </div>
  `).join('');
}

function renderRecentNotes(notes) {
  const el = document.getElementById('dashboard-recent-notes');
  if (!el) return;

  if (notes.length === 0) {
    el.innerHTML = '<p class="empty-hint">No notes posted yet.</p>';
    return;
  }

  el.innerHTML = '';
  notes.forEach(n => {
    const card = document.createElement('div');
    card.className = 'note-card';
    const date = new Date(n.created_at).toLocaleDateString();
    card.innerHTML = `
      <div class="note-class">${n.class_name} · ${n.mentor_name}</div>
      <div class="note-title">${n.title}</div>
      <div class="note-content">${n.content}</div>
      <div class="note-date">${date}</div>`;
    el.appendChild(card);
  });
}