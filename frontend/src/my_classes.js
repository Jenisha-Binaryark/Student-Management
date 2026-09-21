document.addEventListener('DOMContentLoaded', loadClassesPage);

async function loadClassesPage() {
  const root = document.getElementById('student-content');
  if (!root) return;
  root.innerHTML = '<p>Loading your classes…</p>';

  try {
    const res = await fetch('/api/student/content');
    if (res.status === 401) {
      window.location.href = '/login.html';
      return;
    }
    if (!res.ok) throw new Error('Unable to load content');
    const data = await res.json();
    render(root, data);
  } catch {
    root.innerHTML = '<p>Could not load your classes.</p>';
  }
}

function render(root, data) {
  const classes = data.classes || [];
  const timetable = data.timetable || [];
  const exams = data.exams || [];
  const attendance = data.attendance || [];

  root.innerHTML = `
    <section class="classes-section">
      <h1>My Classes</h1>
      <div class="class-grid">
        ${classes.length ? classes.map(c => `
          <article class="class-card">
            <h2>${escapeHtml(c.class_name)}</h2>
            <p>${escapeHtml(c.subject)}</p>
            <span>Mentor: ${escapeHtml(c.mentor_name)}</span>
          </article>
        `).join('') : '<p>No classes assigned yet.</p>'}
      </div>
    </section>
    <section class="classes-section">
      <h2>Regular timetable</h2>
      <div class="schedule-list">
        \${timetable.filter(slot => slot.timetable_type === 'regular').length ? timetable.filter(slot => slot.timetable_type === 'regular').map(slot => \`
          <div class="schedule-item">
            <strong>\${escapeHtml(slot.day_of_week)} · \${escapeHtml(slot.subject)}</strong>
            <span>\${escapeHtml(slot.start_time)} – \${escapeHtml(slot.end_time)} · \${escapeHtml(slot.class_name)}</span>
            \${slot.room ? \`<small>\${escapeHtml(slot.room)}</small>\` : ''}
          </div>
        \`).join('') : '<p>No regular timetable entries yet.</p>'}
      </div>
    </section>
    <section class="classes-section">
      <h2>Exam timetable</h2>
      <div class="schedule-list">
        \${timetable.filter(slot => slot.timetable_type === 'exam').length ? timetable.filter(slot => slot.timetable_type === 'exam').map(slot => \`
          <div class="schedule-item">
            <strong>\${escapeHtml(slot.day_of_week)} · \${escapeHtml(slot.subject)}</strong>
            <span>\${escapeHtml(slot.start_time)} – \${escapeHtml(slot.end_time)} · \${escapeHtml(slot.class_name)}</span>
            \${slot.room ? \`<small>\${escapeHtml(slot.room)}</small>\` : ''}
          </div>
        \`).join('') : '<p>No exam timetable entries yet.</p>'}
      </div>
    </section>
    <section class="classes-section">
      <h2>Attendance history</h2>
      <div class="schedule-list">
        ${attendance.length ? attendance.map(item => `
          <div class="schedule-item">
            <strong>${escapeHtml(item.class_name)} · ${escapeHtml(item.date)}</strong>
            <span class="attendance-status ${item.status === 'present' ? 'present' : 'absent'}">${escapeHtml(item.status.toUpperCase())}</span>
          </div>
        `).join('') : '<p>No attendance records yet.</p>'}
      </div>
    </section>
    <section class="classes-section">
      <h2>Exams & Marks</h2>
      <div class="schedule-list">
        ${exams.length ? exams.map(exam => `
          <div class="schedule-item">
            <strong>${escapeHtml(exam.title)} · ${escapeHtml(exam.class_name)}</strong>
            <span>${escapeHtml(new Date(exam.exam_date).toLocaleDateString())} · ${exam.score === null ? 'Not graded yet' : `${exam.score} / ${exam.max_marks}`}</span>
          </div>
        `).join('') : '<p>No exams have been added yet.</p>'}
      </div>
    </section>
  `;
}

function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>"']/g, char => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[char]));
}