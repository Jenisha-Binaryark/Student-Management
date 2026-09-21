document.addEventListener('DOMContentLoaded', () => {
  loadHomework();
  setupTabs();
  loadSidebar();
});

function loadSidebar() {
  fetch('/sidebar.html')
    .then(res => {
      if (res.status === 401) {
        window.location.href = '/login.html';
        return null;
      }
      return res.text();
    })
    .then(html => {
      if (!html) return;
      const placeholder = document.getElementById('sidebar-placeholder');
      if (placeholder) {
        placeholder.innerHTML = html;
        const usernameEl = document.getElementById('sidebar-username');
        fetch('/api/current_user')
          .then(res => res.json())
          .then(user => {
            if (user.status === 'success' && usernameEl) usernameEl.textContent = user.fullname;
          });
        const logoutBtn = document.getElementById('logout-Btn');
        if (logoutBtn) {
          logoutBtn.addEventListener('click', () => {
            fetch('/logout', { method: 'POST' })
              .then(() => { window.location.href = '/login.html'; });
          });
        }
      }
    })
    .catch(() => {});
}

function setupTabs() {
  document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => {
      document.querySelectorAll('.tab').forEach(item => item.classList.remove('active'));
      document.querySelectorAll('.panel').forEach(panel => panel.classList.remove('active'));
      tab.classList.add('active');
      const panel = document.getElementById(`panel-${tab.dataset.tab}`);
      if (panel) panel.classList.add('active');
    });
  });
}

async function loadHomework() {
  const panels = ['assigned', 'missing', 'done'];
  panels.forEach(name => {
    const panel = document.getElementById(`panel-${name}`);
    if (panel) panel.innerHTML = '<p class="empty-state">Loading…</p>';
  });

  try {
    const res = await fetch('/api/student/content');
    if (res.status === 401) {
      window.location.href = '/login.html';
      return;
    }
    if (!res.ok) throw new Error('Unable to load student content');
    const data = await res.json();
    renderAll(data.assignments || []);
  } catch (err) {
    panels.forEach(name => {
      const panel = document.getElementById(`panel-${name}`);
      if (panel) panel.innerHTML = '<p class="empty-state">Could not load assignments.</p>';
    });
  }
}

function renderAll(assignments) {
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const assigned = [];
  const missing = [];
  const done = [];

  assignments.forEach(item => {
    const due = new Date(`${item.due_date}T23:59:59`);
    const submitted = Boolean(item.submission);
    if (submitted) {
      done.push(item);
    } else if (due < today) {
      missing.push(item);
    } else {
      assigned.push(item);
    }
  });

  renderPanel('assigned', assigned);
  renderPanel('missing', missing);
  renderPanel('done', done);
  updateBadge('assigned', assigned.length);
  updateBadge('missing', missing.length);
  updateBadge('done', done.length);
}

function renderPanel(tabName, items) {
  const panel = document.getElementById(`panel-${tabName}`);
  if (!panel) return;
  panel.innerHTML = '';

  if (items.length === 0) {
    panel.innerHTML = '<p class="empty-state">Nothing here yet.</p>';
    return;
  }

  items.forEach(item => {
    const card = document.createElement('div');
    card.className = 'assignment-card' + (tabName === 'missing' ? ' overdue' : '') + (tabName === 'done' ? ' done' : '');
    const dueDate = new Date(item.due_date).toLocaleDateString();
    const submission = item.submission;
    const action = tabName === 'done'
      ? '<div class="assignment-footer"><span class="points-pill">Submitted</span></div>'
      : '<div class="assignment-footer"><button type="button" class="submit-assignment-btn">Submit work</button></div>';

    card.innerHTML = `
      <div class="icon-badge">${tabName === 'done' ? '✓' : tabName === 'missing' ? '!' : '📘'}</div>
      <div class="assignment-body">
        <div class="assignment-top">
          <div class="assignment-title${tabName === 'done' ? ' done-title' : ''}">${escapeHtml(item.title)}</div>
          <div class="due-wrap"><div class="assignment-due${tabName === 'missing' ? ' overdue-text' : ''}">Due ${escapeHtml(dueDate)}</div></div>
        </div>
        <div class="assignment-meta">${escapeHtml(item.class_name)}</div>
        ${item.description ? `<div class="assignment-description">${escapeHtml(item.description)}</div>` : ''}
        ${submission ? `<div class="assignment-description">Submitted ${escapeHtml(new Date(submission.submitted_at).toLocaleString())}${submission.url ? ` · <a href="${escapeHtml(submission.url)}" target="_blank" rel="noopener">Open submission</a>` : ''}</div>` : ''}
        ${action}
      </div>
    `;

    const button = card.querySelector('.submit-assignment-btn');
    if (button) button.addEventListener('click', () => submitAssignment(item));
    panel.appendChild(card);
  });
}

async function submitAssignment(item) {
  const text = window.prompt('Enter your submission text or paste your answer.');
  if (text === null) return;
  const url = window.prompt('Optional: paste a link to your submitted file or project.');
  try {
    const res = await fetch(`/api/student/assignments/${item.id}/submission`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, url: url || '' })
    });
    if (res.status === 401) {
      window.location.href = '/login.html';
      return;
    }
    const data = await res.json();
    if (!res.ok) {
      window.alert(data.error || 'Could not submit assignment.');
      return;
    }
    loadHomework();
  } catch {
    window.alert('Could not submit assignment.');
  }
}

function updateBadge(tabName, count) {
  const badge = document.getElementById(`badge-${tabName}`);
  if (badge) badge.textContent = count;
}

function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>"']/g, char => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[char]));
}