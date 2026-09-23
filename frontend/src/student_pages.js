const pageName = document.body.dataset.page || 'grades';

document.addEventListener('DOMContentLoaded', async () => {
  const user = await loadSidebar();
  if (!user) return;
  if (pageName === 'settings') await loadSettings();
  else await loadContentPage();
});

async function loadSidebar() {
  try {
    const response = await fetch('/sidebar.html');
    if (!response.ok || response.redirected) throw new Error('Navigation unavailable');
    document.getElementById('sidebar-placeholder').innerHTML = await response.text();
    const userResponse = await fetch('/api/current_user');
    if (!userResponse.ok) throw new Error('User unavailable');
    const user = await userResponse.json();
    const name = user.fullname || 'Student';
    const sidebarName = document.getElementById('sidebar-username');
    const firstName = document.getElementById('user-first-name');
    if (sidebarName) sidebarName.textContent = name;
    if (firstName) firstName.textContent = name.split(' ')[0];
    document.querySelectorAll('.sidebar nav a').forEach(link => link.classList.remove('active'));
    document.querySelector(`.sidebar nav a[data-page="${pageName}"]`)?.classList.add('active');
    document.getElementById('logout-Btn')?.addEventListener('click', async () => {
      await fetch('/logout', {method: 'POST'});
      window.location.href = '/login.html?role=student';
    });
    return user;
  } catch {
    window.location.href = '/login.html?role=student';
    return null;
  }
}

async function loadContentPage() {
  const root = document.getElementById('student-content');
  try {
    const response = await fetch('/api/student/content');
    if (!response.ok) throw new Error('Content unavailable');
    const data = await response.json();
    if (pageName === 'grades') renderGrades(root, data.exams || []);
    if (pageName === 'schedule') renderSchedule(root, data.timetable || []);
    if (pageName === 'messages') renderMessages(root, data.notes || []);
  } catch {
    root.innerHTML = '<section class="page-card empty-state"><h1>Unable to load this page</h1><p>Please refresh and try again.</p></section>';
  }
}

function renderGrades(root, exams) {
  const graded = exams.filter(exam => exam.score !== null);
  const totalScore = graded.reduce((sum, exam) => sum + exam.score, 0);
  const totalMax = graded.reduce((sum, exam) => sum + exam.max_marks, 0);
  const percentage = totalMax ? Math.round(totalScore / totalMax * 100) : null;
  root.innerHTML = `
    <header class="page-heading"><div><span class="eyebrow">Academic progress</span><h1>My Grades</h1><p>Track your exam scores and progress across all classes.</p></div><div class="heading-badge">${percentage === null ? '—' : `${percentage}%`}<small>overall</small></div></header>
    <section class="summary-grid"><div class="summary-card"><span>Exams recorded</span><strong>${graded.length}</strong></div><div class="summary-card"><span>Pending results</span><strong>${exams.length - graded.length}</strong></div><div class="summary-card accent"><span>Overall average</span><strong>${percentage === null ? '—' : `${percentage}%`}</strong></div></section>
    <section class="page-card"><div class="section-title"><div><span class="eyebrow">Results</span><h2>Exam performance</h2></div></div>${exams.length ? `<div class="data-list">${exams.map(exam => `<article class="data-row"><div><strong>${escapeHtml(exam.title)}</strong><span>${escapeHtml(exam.class_name)} · ${formatDate(exam.exam_date)}</span></div><b class="score-pill ${exam.score === null ? 'pending' : ''}">${exam.score === null ? 'Pending' : `${exam.score} / ${exam.max_marks}`}</b></article>`).join('')}</div>` : emptyMessage('No grades yet', 'Your exam results will appear here once your mentor records them.')}</section>`;
}

function renderSchedule(root, timetable) {
  const regular = timetable.filter(slot => slot.timetable_type !== 'exam');
  const exams = timetable.filter(slot => slot.timetable_type === 'exam');
  root.innerHTML = `
    <header class="page-heading"><div><span class="eyebrow">Plan your week</span><h1>My Schedule</h1><p>See your regular classes and upcoming exam timetable in one place.</p></div><div class="heading-icon">📅</div></header>
    <section class="schedule-columns"><section class="page-card"><div class="section-title"><div><span class="eyebrow">Weekly plan</span><h2>Regular classes</h2></div><span class="count-badge">${regular.length}</span></div>${regular.length ? `<div class="timeline">${regular.map(slot => scheduleRow(slot, false)).join('')}</div>` : emptyMessage('No regular classes yet', 'Your mentor will publish the weekly timetable here.')}</section><section class="page-card"><div class="section-title"><div><span class="eyebrow">Important dates</span><h2>Exam timetable</h2></div><span class="count-badge">${exams.length}</span></div>${exams.length ? `<div class="timeline">${exams.map(slot => scheduleRow(slot, true)).join('')}</div>` : emptyMessage('No exams scheduled', 'Exam timetable entries will appear here when they are published.')}</section></section>`;
}

function scheduleRow(slot, isExam) {
  return `<article class="timeline-row"><div class="time-dot ${isExam ? 'exam' : ''}"></div><div><strong>${escapeHtml(slot.subject || slot.class_name)}</strong><span>${escapeHtml(slot.class_name)} · ${escapeHtml(slot.day_of_week)} · ${escapeHtml(slot.start_time)}–${escapeHtml(slot.end_time)}</span>${slot.room ? `<small>Room ${escapeHtml(slot.room)}</small>` : ''}${slot.exam_date ? `<small>${formatDate(slot.exam_date)}</small>` : ''}</div></article>`;
}

function renderMessages(root, notes) {
  root.innerHTML = `
    <header class="page-heading"><div><span class="eyebrow">Stay connected</span><h1>Messages</h1><p>Updates and notes shared by your mentors.</p></div><div class="heading-icon">✉</div></header>
    <section class="page-card"><div class="section-title"><div><span class="eyebrow">Inbox</span><h2>Mentor updates</h2></div><span class="count-badge">${notes.length}</span></div>${notes.length ? `<div class="message-list">${notes.map(note => `<article class="message-card"><div class="message-icon">✦</div><div><div class="message-meta">${escapeHtml(note.mentor_name)} · ${formatDate(note.created_at)}</div><h3>${escapeHtml(note.title)}</h3><p>${escapeHtml(note.content)}</p><span class="message-class">${escapeHtml(note.class_name)}</span></div></article>`).join('')}</div>` : emptyMessage('No messages yet', 'Mentor announcements and notes will appear here.')}</section>`;
}

async function loadSettings() {
  const root = document.getElementById('student-content');
  try {
    const response = await fetch('/api/student/profile');
    if (!response.ok) throw new Error('Profile unavailable');
    const profile = await response.json();
    root.innerHTML = `<header class="page-heading"><div><span class="eyebrow">Your account</span><h1>Settings</h1><p>Keep your student profile up to date.</p></div><div class="heading-icon">⚙</div></header><section class="page-card settings-card"><div class="section-title"><div><span class="eyebrow">Profile details</span><h2>Personal information</h2></div></div><form id="settings-form" class="settings-form"><label>Full name<input name="fullname" value="${escapeAttribute(profile.fullname)}" required></label><label>Email address<input value="${escapeAttribute(profile.email)}" disabled></label><label>Phone number<input name="phone" value="${escapeAttribute(profile.phone)}" required></label><div class="form-actions"><span id="settings-status" role="status"></span><button class="primary-button" type="submit">Save changes</button></div></form></section>`;
    document.getElementById('settings-form').addEventListener('submit', saveSettings);
  } catch {
    root.innerHTML = '<section class="page-card empty-state"><h1>Unable to load settings</h1><p>Please refresh and try again.</p></section>';
  }
}

async function saveSettings(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const status = document.getElementById('settings-status');
  status.textContent = 'Saving…';
  const response = await fetch('/api/student/profile', {method: 'PATCH', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(Object.fromEntries(new FormData(form)))});
  const data = await response.json();
  status.textContent = response.ok ? 'Saved successfully.' : (data.error || 'Could not save changes.');
  status.className = response.ok ? 'success-text' : 'error-text';
}

function emptyMessage(title, copy) { return `<div class="empty-state"><strong>${title}</strong><p>${copy}</p></div>`; }
function formatDate(value) { return value ? new Date(value).toLocaleDateString(undefined, {month: 'short', day: 'numeric', year: 'numeric'}) : ''; }
function escapeAttribute(value) { return escapeHtml(value).replace(/`/g, '&#96;'); }
function escapeHtml(value) { return String(value ?? '').replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char])); }
