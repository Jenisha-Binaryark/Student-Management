document.addEventListener('DOMContentLoaded', () => {
  loadMentorSidebar('notes');
  window.addEventListener('classesUpdated', (e) => populateClassSelect(e.detail || []));
  loadNotes();
  setupNoteForm();
});

function populateClassSelect(classes) {
  const select = document.getElementById('noteClass');
  if (!select) return;

  if (classes.length === 0) {
    select.innerHTML = '<option value="">No classes yet — add one up top first</option>';
    return;
  }

  select.innerHTML = classes
    .map(c => `<option value="${c.id}">${c.class_name}</option>`)
    .join('');
}

function loadNotes() {
  const list = document.getElementById('notesList');
  if (!list) return;

  fetch('/api/notes')
    .then(r => r.json())
    .then(data => {
      const notes = data.notes || [];
      if (notes.length === 0) {
        list.innerHTML = '<p class="empty-hint">No notes posted yet.</p>';
        return;
      }
      list.innerHTML = '';
      notes.forEach(n => {
        const card = document.createElement('div');
        card.className = 'note-card';
        const date = new Date(n.created_at).toLocaleString();
        card.innerHTML = `
          <div class="note-class">${n.class_name}</div>
          <div class="note-title">${n.title}</div>
          <div class="note-content">${n.content}</div>
          <div class="note-date">${date}</div>`;
        list.appendChild(card);
      });
    })
    .catch(err => {
      console.error('Failed to load notes:', err);
      list.innerHTML = '<p class="empty-hint">Could not load notes.</p>';
    });
}

function setupNoteForm() {
  const form = document.getElementById('noteForm');
  const message = document.getElementById('noteMessage');
  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    message.textContent = '';

    const payload = {
      class_id: document.getElementById('noteClass').value,
      title: document.getElementById('noteTitle').value.trim(),
      content: document.getElementById('noteContent').value.trim(),
    };

    if (!payload.class_id) {
      message.textContent = 'Add or select a class first.';
      message.style.color = '#d1567f';
      return;
    }
    if (!payload.title || !payload.content) {
      message.textContent = 'Please fill in the title and note.';
      message.style.color = '#d1567f';
      return;
    }

    try {
      const res = await fetch('/api/notes', {
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

      message.textContent = 'Note posted!';
      message.style.color = '#5aada0';
      form.reset();
      loadNotes();
    } catch (err) {
      console.error(err);
      message.textContent = 'Server error. Please try again.';
      message.style.color = '#d1567f';
    }
  });
}