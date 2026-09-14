document.addEventListener('DOMContentLoaded', () => {
  loadMentorSidebar('assignments');

  window.addEventListener('classChanged', (e) => {
    activeClass = e.detail || null;
    updateHeading();
    loadAssignments();
  });

  window.addEventListener('classesUpdated', (e) => {
    if ((e.detail || []).length === 0) {
      activeClass = null;
      updateHeading();
      renderAssignments([]);
    }
  });

  setupAssignmentForm();
});

let activeClass = null;

function updateHeading() {
  const heading = document.getElementById('assignmentsActiveClass');
  if (!heading) return;
  heading.textContent = activeClass
    ? `Showing assignments for ${activeClass.class_name}.`
    : 'Add or select a class above to post an assignment.';
}

function todayISO() {
  const d = new Date();
  const pad = n => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

function loadAssignments() {
  const list = document.getElementById('assignmentsList');
  if (!list) return;

  if (!activeClass) {
    list.innerHTML = '<p class="empty-hint">Select a class above to see its assignments.</p>';
    return;
  }

  list.innerHTML = '<p class="empty-hint">Loading…</p>';

  fetch(`/api/assignments?class_id=${activeClass.id}`)
    .then(res => {
      if (res.status === 401) {
        window.location.href = '/login.html?role=mentor';
        return null;
      }
      return res.json();
    })
    .then(data => {
      if (data) renderAssignments(data.assignments || []);
    })
    .catch(err => {
      console.error('Failed to load assignments:', err);
      list.innerHTML = '<p class="empty-hint">Could not load assignments.</p>';
    });
}

function renderAssignments(assignments) {
  const list = document.getElementById('assignmentsList');
  if (!list) return;
  list.innerHTML = '';

  if (!activeClass) {
    list.innerHTML = '<p class="empty-hint">Select a class above to see its assignments.</p>';
    return;
  }
  if (assignments.length === 0) {
    list.innerHTML = '<p class="empty-hint">No assignments posted yet.</p>';
    return;
  }

  const today = todayISO();

  assignments.forEach(a => {
    const isOverdue = a.due_date < today;
    const card = document.createElement('div');
    card.className = 'assignment-card' + (isOverdue ? ' overdue' : '');
    card.innerHTML = `
      <div class="assignment-card-top">
        <div class="assignment-card-title">${a.title}</div>
        <button type="button" class="assignment-delete" title="Delete assignment" data-id="${a.id}">✕</button>
      </div>
      ${a.description ? `<div class="assignment-card-desc">${a.description}</div>` : ''}
      <div class="assignment-card-due${isOverdue ? ' overdue-text' : ''}">Due ${formatDate(a.due_date)}</div>
    `;
    card.querySelector('.assignment-delete').addEventListener('click', () => deleteAssignment(a.id));
    list.appendChild(card);
  });
}

function formatDate(iso) {
  const [y, m, d] = iso.split('-');
  return `${d}/${m}/${y}`;
}

function deleteAssignment(id) {
  fetch(`/api/assignments/${id}`, { method: 'DELETE' })
    .then(res => {
      if (res.status === 401) {
        window.location.href = '/login.html?role=mentor';
        return null;
      }
      return res.json();
    })
    .then(data => {
      if (data) loadAssignments();
    })
    .catch(err => console.error('Failed to delete assignment:', err));
}

function setupAssignmentForm() {
  const form = document.getElementById('assignmentForm');
  const message = document.getElementById('assignmentMessage');
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
      title: document.getElementById('assignmentTitle').value.trim(),
      description: document.getElementById('assignmentDescription').value.trim(),
      due_date: document.getElementById('assignmentDue').value,
    };

    if (!payload.title || !payload.due_date) {
      message.textContent = 'Please fill in the title and due date.';
      message.style.color = '#d1567f';
      return;
    }

    try {
      const res = await fetch('/api/assignments', {
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

      message.textContent = 'Assignment posted!';
      message.style.color = '#5aada0';
      form.reset();
      loadAssignments();
    } catch (err) {
      console.error(err);
      message.textContent = 'Server error. Please try again.';
      message.style.color = '#d1567f';
    }
  });
}