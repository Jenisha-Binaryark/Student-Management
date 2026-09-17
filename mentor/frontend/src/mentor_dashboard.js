document.addEventListener('DOMContentLoaded', () => {
  loadMentorSidebar('dashboard');
  loadDashboardSummary();
});

const RING_CIRCUMFERENCE = 213.6;

function loadDashboardSummary() {
  fetch('/api/dashboard/summary')
    .then(res => {
      if (res.status === 401) {
        window.location.href = '/login.html?role=mentor';
        return null;
      }
      return res.json();
    })
    .then(data => {
      if (!data) return;
      renderClassList(data.classes || []);
      renderRing('attendanceRing', 'attendancePct', data.attendance ? data.attendance.percent : null, '#d1567f');
      renderRing('marksRing', 'marksPct', data.marks ? data.marks.percent : null, '#e0aa4e');
      renderAssignmentCounts(data.assignments || { upcoming: 0, overdue: 0 });
      renderTodaySchedule(data.today_schedule || []);
      renderRecentNotes(data.recent_notes || []);
    })
    .catch(err => {
      console.error('Failed to load dashboard summary:', err);
      const classList = document.getElementById('dashboard-class-list');
      if (classList) classList.innerHTML = '<p class="empty-hint">Could not load dashboard data.</p>';
    });
}

function renderClassList(classes) {
  const el = document.getElementById('dashboard-class-list');
  if (!el) return;

  if (classes.length === 0) {
    el.innerHTML = '<p class="empty-hint">No classes yet. Create one to get started.</p>';
    return;
  }

  el.innerHTML = '';
  classes.forEach(c => {
    const row = document.createElement('div');
    row.className = 'person-row';
    row.innerHTML = `
      <div>
        <div class="p-name">${c.class_name}</div>
        <div class="p-sub">${c.course} · ${c.subject}</div>
      </div>
      <span class="class-row-count">${c.student_count} student${c.student_count === 1 ? '' : 's'}</span>`;
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

function renderAssignmentCounts(assignments) {
  const upcomingEl = document.getElementById('assignUpcoming');
  const overdueEl = document.getElementById('assignOverdue');
  if (upcomingEl) upcomingEl.textContent = assignments.upcoming ?? 0;
  if (overdueEl) overdueEl.textContent = assignments.overdue ?? 0;
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
      <div class="note-class">${n.class_name}</div>
      <div class="note-title">${n.title}</div>
      <div class="note-content">${n.content}</div>
      <div class="note-date">${date}</div>`;
    el.appendChild(card);
  });
}