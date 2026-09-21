document.addEventListener('DOMContentLoaded', () => {
  loadMentorSidebar('marks');

  window.addEventListener('classChanged', (e) => {
    activeClass = e.detail || null;
    activeExam = null;
    updateHeading();
    loadExams();
  });

  window.addEventListener('classesUpdated', (e) => {
    if ((e.detail || []).length === 0) {
      activeClass = null;
      activeExam = null;
      updateHeading();
      renderExams([]);
      renderMarks(null, []);
    }
  });

  setupExamForm();
  document.getElementById('saveMarksBtn').addEventListener('click', saveMarks);
});

let activeClass = null;
let activeExam = null;
let currentMarks = [];

function todayISO() {
  const d = new Date();
  const pad = n => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

function formatDate(iso) {
  const [y, m, d] = iso.split('-');
  return `${d}/${m}/${y}`;
}

function updateHeading() {
  const heading = document.getElementById('marksActiveClass');
  if (!heading) return;
  heading.textContent = activeClass
    ? `Managing exams and marks for ${activeClass.class_name}.`
    : 'Add or select a class above to manage exams and marks.';
}

function loadExams() {
  const list = document.getElementById('examsList');
  if (!list) return;

  if (!activeClass) {
    list.innerHTML = '<p class="empty-hint">Select a class above to see its exams.</p>';
    renderMarks(null, []);
    return;
  }

  list.innerHTML = '<p class="empty-hint">Loading…</p>';

  fetch(`/api/exams?class_id=${activeClass.id}`)
    .then(res => {
      if (res.status === 401 || res.status === 403) {
        window.location.href = res.status === 403 ? '/mentor/onboarding.html' : '/login.html?role=mentor';
        return null;
      }
      return res.json();
    })
    .then(data => {
      if (data) renderExams(data.exams || []);
    })
    .catch(err => {
      console.error('Failed to load exams:', err);
      list.innerHTML = '<p class="empty-hint">Could not load exams.</p>';
    });
}

function renderExams(exams) {
  const list = document.getElementById('examsList');
  if (!list) return;
  list.innerHTML = '';

  if (!activeClass) {
    list.innerHTML = '<p class="empty-hint">Select a class above to see its exams.</p>';
    return;
  }
  if (exams.length === 0) {
    list.innerHTML = '<p class="empty-hint">No exams added yet.</p>';
    return;
  }

  if (activeExam && !exams.some(x => x.id === activeExam.id)) {
    activeExam = null;
    renderMarks(null, []);
  }

  exams.forEach(x => {
    const item = document.createElement('div');
    item.className = 'exam-item' + (activeExam && activeExam.id === x.id ? ' active' : '');
    item.dataset.examId = x.id;
    item.innerHTML = `
      <div class="exam-item-top">
        <div class="exam-item-title">${escapeHtml(x.title)}</div>
        <button type="button" class="exam-delete" title="Delete exam" data-id="${x.id}">✕</button>
      </div>
      <div class="exam-item-meta">Out of ${x.max_marks} &nbsp;•&nbsp; ${formatDate(x.exam_date)}</div>
    `;
    item.addEventListener('click', () => selectExam(x));
    item.querySelector('.exam-delete').addEventListener('click', (e) => {
      e.stopPropagation();
      deleteExam(x.id);
    });
    list.appendChild(item);
  });
}

function selectExam(exam) {
  activeExam = exam;
  document.querySelectorAll('.exam-item').forEach(el => {
    el.classList.toggle('active', Number(el.dataset.examId) === exam.id);
  });
  loadMarks();
}

function deleteExam(examId) {
  if (!window.confirm('Delete this exam and its marks?')) return;
  fetch(`/api/exams/${examId}`, { method: 'DELETE' })
    .then(res => {
      if (res.status === 401) {
        window.location.href = r.status === 403 ? '/mentor/onboarding.html' : '/login.html?role=mentor';
        return null;
      }
      return res.json();
    })
    .then(data => {
      if (!data) return;
      if (activeExam && activeExam.id === examId) {
        activeExam = null;
        renderMarks(null, []);
      }
      loadExams();
    })
    .catch(err => console.error('Failed to delete exam:', err));
}

function setupExamForm() {
  const form = document.getElementById('examForm');
  const message = document.getElementById('examMessage');
  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    message.textContent = '';

    if (!activeClass) {
      message.textContent = 'Add or select a class first.';
      message.style.color = '#d1567f';
      return;
    }

    const payload = {
      class_id: activeClass.id,
      title: document.getElementById('examTitle').value.trim(),
      max_marks: document.getElementById('examMaxMarks').value,
      exam_date: document.getElementById('examDate').value,
    };

    if (!payload.title || !payload.max_marks || !payload.exam_date) {
      message.textContent = 'Please fill in title, max marks, and date.';
      message.style.color = '#d1567f';
      return;
    }

    try {
      const res = await fetch('/api/exams', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
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

      message.textContent = 'Exam added!';
      message.style.color = '#5aada0';
      form.reset();
      loadExams();
    } catch (err) {
      console.error(err);
      message.textContent = 'Server error. Please try again.';
      message.style.color = '#d1567f';
    }
  });
}

function loadMarks() {
  const heading = document.getElementById('marksExamHeading');
  const list = document.getElementById('marksList');
  if (!list) return;

  if (!activeExam) {
    if (heading) heading.textContent = 'Enter marks';
    list.innerHTML = '<p class="empty-hint">Select an exam on the left to enter marks.</p>';
    return;
  }

  if (heading) heading.textContent = `Marks — ${activeExam.title} (out of ${activeExam.max_marks})`;
  list.innerHTML = '<p class="empty-hint">Loading…</p>';

  fetch(`/api/marks?exam_id=${activeExam.id}`)
    .then(res => {
      if (res.status === 401) {
        window.location.href = '/login.html?role=mentor';
        return null;
      }
      return res.json();
    })
    .then(data => {
      if (!data) return;
      renderMarks(activeExam, data.records || []);
    })
    .catch(err => {
      console.error('Failed to load marks:', err);
      list.innerHTML = '<p class="empty-hint">Could not load marks.</p>';
    });
}

function renderMarks(exam, records) {
  currentMarks = records.map(r => ({ ...r }));
  const list = document.getElementById('marksList');
  if (!list) return;
  list.innerHTML = '';

  if (!exam) {
    list.innerHTML = '<p class="empty-hint">Select an exam on the left to enter marks.</p>';
    return;
  }
  if (records.length === 0) {
    list.innerHTML = '<p class="empty-hint">Add students to this class\'s roster on the Attendance page first.</p>';
    return;
  }

  records.forEach(r => {
    const row = document.createElement('div');
    row.className = 'marks-row';
    row.innerHTML = `
      <div class="marks-name">${escapeHtml(r.fullname)}</div>
      <div class="marks-score-wrap">
        <input type="number" class="marks-score-input" min="0" max="${exam.max_marks}" step="0.5"
               value="${r.score === null || r.score === undefined ? '' : r.score}"
               placeholder="–">
        <span class="marks-out-of">/ ${exam.max_marks}</span>
      </div>
    `;
    row.querySelector('.marks-score-input').addEventListener('input', (e) => {
      const record = currentMarks.find(m => m.student_id === r.student_id);
      if (record) record.score = e.target.value === '' ? null : Number(e.target.value);
    });
    list.appendChild(row);
  });
}

function saveMarks() {
  const message = document.getElementById('marksMessage');
  message.textContent = '';

  if (!activeExam) {
    message.textContent = 'Select an exam first.';
    message.style.color = '#d1567f';
    return;
  }

  const records = currentMarks
    .filter(r => r.score !== null && r.score !== undefined && r.score !== '')
    .map(r => ({ student_id: r.student_id, score: r.score }));

  if (records.length === 0) {
    message.textContent = 'Enter at least one score before saving.';
    message.style.color = '#d1567f';
    return;
  }

  fetch('/api/marks', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ exam_id: activeExam.id, records }),
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
      message.textContent = 'Marks saved!';
      message.style.color = '#5aada0';
    })
    .catch(err => {
      console.error(err);
      message.textContent = 'Server error. Please try again.';
      message.style.color = '#d1567f';
    });
}