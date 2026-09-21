document.addEventListener('DOMContentLoaded', () => {
  loadMentorSidebar('dashboard');
  window.addEventListener('classChanged', (e) => loadDashboardSummary(e.detail?.id || null));
  loadDashboardSummary(null);
});

const RING_CIRCUMFERENCE = 213.6;

function loadDashboardSummary(classId = null) {
  const containers = [
    document.getElementById('dashboard-class-list'),
    document.getElementById('dashboard-today-schedule'),
    document.getElementById('dashboard-recent-notes')
  ];

  containers.forEach(el => {
    if (el) el.classList.add('dashboard-loading');
  });

  const query = classId ? `?class_id=${encodeURIComponent(classId)}` : '';
  fetch(`/api/dashboard/summary${query}`)
    .then(res => {
      if (res.status === 401) {
        window.location.href = '/login.html?role=mentor';
        return null;
      }
      if (!res.ok) throw new Error(`Dashboard request failed: ${res.status}`);
      return res.json();
    })
    .then(data => {
      if (!data) return;

      renderKpis(data);
      renderClassList(data.classes || [], data.selected_class_id);
      const selected = (data.classes || []).find(c => c.id === data.selected_class_id);
      updateDashboardScope(selected);
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
    })
    .finally(() => {
      containers.forEach(el => {
        if (el) el.classList.remove('dashboard-loading');
      });
    });
}

function renderKpis(data) {
  const students = document.getElementById('totalStudents');
  const attendance = document.getElementById('attendanceKpi');
  const marks = document.getElementById('marksKpi');
  const assignments = document.getElementById('assignmentKpi');
  if (students) students.textContent = Number(data.total_students || 0);
  if (attendance) attendance.textContent = data.attendance ? `${data.attendance.percent}%` : '–';
  if (marks) marks.textContent = data.marks ? `${data.marks.percent}%` : '–';
  if (assignments) assignments.textContent = Number(data.assignments?.upcoming || 0);
}

function updateDashboardScope(selectedClass) {
  const el = document.getElementById('dashboardScope');
  if (el) el.textContent = selectedClass ? `Showing ${selectedClass.class_name}` : 'All classes';
}

function renderClassList(classes, selectedClassId = null) {
  const el = document.getElementById('dashboard-class-list');
  if (!el) return;

  if (classes.length === 0) {
    el.innerHTML = '<p class="empty-hint">No classes yet. Create one to get started.</p>';
    return;
  }

  el.innerHTML = '';
  classes.forEach(c => {
    const row = document.createElement('div');
    row.className = 'person-row dashboard-item-enter' + (selectedClassId === c.id ? ' selected-class' : '');
    row.innerHTML = `
      <div>
        <div class="p-name">${escapeHtml(c.class_name)}</div>
        <div class="p-sub">${escapeHtml(c.course)} · ${escapeHtml(c.subject)}</div>
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

  const clamped = Math.max(0, Math.min(100, Number(percent)));
  const targetOffset = RING_CIRCUMFERENCE * (1 - clamped / 100);

  ring.setAttribute('stroke', color);
  animateRing(ring, pctEl, targetOffset, clamped);
}

function animateRing(ring, pctEl, targetOffset, targetPercent) {
  const startOffset = RING_CIRCUMFERENCE;
  const startTime = performance.now();
  const duration = 850;

  function frame(now) {
    const progress = Math.min(1, (now - startTime) / duration);
    const eased = 1 - Math.pow(1 - progress, 3);
    const offset = startOffset + (targetOffset - startOffset) * eased;

    ring.setAttribute('stroke-dashoffset', offset.toFixed(1));
    pctEl.textContent = `${Math.round(targetPercent * eased)}%`;

    if (progress < 1) {
      requestAnimationFrame(frame);
    }
  }

  requestAnimationFrame(frame);
}

function renderAssignmentCounts(assignments) {
  const upcomingEl = document.getElementById('assignUpcoming');
  const overdueEl = document.getElementById('assignOverdue');
  if (upcomingEl) animateNumber(upcomingEl, assignments.upcoming ?? 0);
  if (overdueEl) animateNumber(overdueEl, assignments.overdue ?? 0);
}

function animateNumber(element, target) {
  const end = Math.max(0, Number(target) || 0);
  const start = 0;
  const duration = 500;
  const startTime = performance.now();

  function frame(now) {
    const progress = Math.min(1, (now - startTime) / duration);
    const eased = 1 - Math.pow(1 - progress, 3);
    element.textContent = Math.round(start + (end - start) * eased);

    if (progress < 1) requestAnimationFrame(frame);
  }

  requestAnimationFrame(frame);
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
    item.className = 'lesson-item dashboard-item-enter';
    item.innerHTML = `
      <div>
        <div class="lesson-title">${escapeHtml(s.subject)} · ${escapeHtml(s.class_name)}</div>
        <div class="lesson-time">${escapeHtml(s.start_time)} – ${escapeHtml(s.end_time)}${s.room ? ' · ' + escapeHtml(s.room) : ''}</div>
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
    card.className = 'note-card dashboard-item-enter';
    const date = new Date(n.created_at).toLocaleDateString();
    card.innerHTML = `
      <div class="note-class">${escapeHtml(n.class_name)}</div>
      <div class="note-title">${escapeHtml(n.title)}</div>
      <div class="note-content">${escapeHtml(n.content)}</div>
      <div class="note-date">${escapeHtml(date)}</div>`;
    el.appendChild(card);
  });
}

function escapeHtml(value) {
  return String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}