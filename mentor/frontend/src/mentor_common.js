function loadMentorSidebar(activePage) {
  // NOTE: this must be an absolute path. A relative 'mentor/sidebar.html' resolves
  // against the current page's URL, so on /mentor/dashboard.html it was requesting
  // /mentor/mentor/sidebar.html and silently failing (this was why the sidebar
  // never rendered).
  fetch('/mentor/sidebar.html')
    .then(res => {
      if (res.status === 401 || res.status === 403) {
        window.location.href = res.status === 403 ? '/mentor/onboarding.html' : '/login.html?role=mentor';
        return null;
      }
      return res.text();
    })
    .then(html => {
      if (!html) return;
      document.getElementById('sidebar-placeholder').innerHTML = html;
      initMentorSidebar(activePage);
    })
    .catch(err => console.error('Failed to load mentor sidebar:', err));
}

function initMentorSidebar(activePage) {
  document.querySelectorAll('nav a[data-page]').forEach(a => {
    a.classList.toggle('active', a.dataset.page === activePage);
  });

  fetch('/api/current_user')
    .then(r => r.json())
    .then(u => {
      if (u.status === 'success') {
        document.getElementById('sidebar-username').textContent = u.fullname;
        document.getElementById('user-first-name').textContent =
          u.fullname.split(' ')[0].toUpperCase();
      }
    })
    .catch(err => console.error('Failed to load user info:', err));

  loadClassTabs();
  setupAddClassModal();

  // logout
  const logoutBtn = document.getElementById('logout-Btn');
  if (logoutBtn) {
    logoutBtn.addEventListener('click', () => {
      fetch('/logout', { method: 'POST' })
        .then(() => window.location.href = '/login.html');
    });
  }
}

function loadClassTabs(selectClassId) {
  const container = document.getElementById('class-tabs');
  if (!container) return;

  fetch('/api/classes')
    .then(r => r.json())
    .then(data => {
      const classes = data.classes || [];
      container.innerHTML = '';

      if (classes.length === 0) {
        const hint = document.createElement('span');
        hint.className = 'no-classes-msg';
        hint.textContent = 'No classes yet —';
        container.appendChild(hint);
      }

      let activeClass = null;

      classes.forEach((c) => {
        const btn = document.createElement('button');
        const isActive = selectClassId ? c.id === selectClassId : c === classes[0];
        btn.className = 'class-tab' + (isActive ? ' active' : '');
        btn.textContent = c.class_name;
        btn.dataset.classId = c.id;
        btn.addEventListener('click', () => {
          container.querySelectorAll('.class-tab').forEach(t => t.classList.remove('active'));
          btn.classList.add('active');
          window.dispatchEvent(new CustomEvent('classChanged', { detail: c }));
        });
        container.appendChild(btn);
        if (isActive) activeClass = c;
      });

      const addBtn = document.createElement('button');
      addBtn.type = 'button';
      addBtn.className = 'class-tab add-class-tab';
      addBtn.title = 'Add a class';
      addBtn.textContent = '+';
      addBtn.addEventListener('click', openAddClassModal);
      container.appendChild(addBtn);

      if (activeClass) {
        window.dispatchEvent(new CustomEvent('classChanged', { detail: activeClass }));
      }
      window.dispatchEvent(new CustomEvent('classesUpdated', { detail: classes }));
    })
    .catch(err => {
      console.error('Failed to load classes:', err);
      container.innerHTML = '<span class="no-classes-msg">Could not load classes</span>';
    });
}

function setupAddClassModal() {
  const overlay = document.getElementById('add-class-overlay');
  const form = document.getElementById('addClassForm');
  const cancelBtn = document.getElementById('addClassCancel');
  const message = document.getElementById('addClassMessage');
  if (!overlay || !form) return;

  cancelBtn.addEventListener('click', closeAddClassModal);
  overlay.addEventListener('click', (e) => {
    if (e.target === overlay) closeAddClassModal();
  });

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    message.textContent = '';

    const payload = {
      class_name: document.getElementById('addClassName').value.trim(),
      university: document.getElementById('addClassUniversity').value.trim(),
      course: document.getElementById('addClassCourse').value.trim(),
      year: document.getElementById('addClassYear').value.trim(),
      subject: document.getElementById('addClassSubject').value.trim(),
      role: document.getElementById('addClassRole').value,
    };

    if (Object.values(payload).some(v => !v)) {
      message.textContent = 'Please fill in every field.';
      message.style.color = '#d1567f';
      return;
    }

    try {
      const res = await fetch('/api/classes', {
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

      form.reset();
      closeAddClassModal();
      loadClassTabs(data.class_id);
    } catch (err) {
      console.error(err);
      message.textContent = 'Server error. Please try again.';
      message.style.color = '#d1567f';
    }
  });
}

function openAddClassModal() {
  const overlay = document.getElementById('add-class-overlay');
  const message = document.getElementById('addClassMessage');
  if (message) message.textContent = '';
  if (overlay) overlay.classList.add('open');
}

function closeAddClassModal() {
  const overlay = document.getElementById('add-class-overlay');
  if (overlay) overlay.classList.remove('open');
}

function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>"']/g, char => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[char]));
}
