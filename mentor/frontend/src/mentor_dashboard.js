document.addEventListener('DOMContentLoaded', () => {
  loadMentorSidebar('dashboard');
  loadClassList();
});

function loadClassList() {
  const el = document.getElementById('dashboard-class-list');
  if (!el) return;

  fetch('/api/classes')
    .then(r => r.json())
    .then(data => {
      const classes = data.classes || [];
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
          </div>`;
        el.appendChild(row);
      });
    })
    .catch(err => {
      console.error('Failed to load classes:', err);
      el.innerHTML = '<p class="empty-hint">Could not load classes.</p>';
    });
}