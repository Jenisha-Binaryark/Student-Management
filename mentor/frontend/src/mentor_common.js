function loadMentorSidebar(activePage){
    fetch('mentor/sidebar.html')
    .then(res => {
        if (res.status === 401) {
            window.location.href = '/login.html?role=mentor';
            return null;
        }
        return res.text();
    })
    .then(html => {
        if(!html) return;
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

    fetch('/api/classes')
        .then(r => r.json())
        .then(data => {
            const container = document.getElementById('class-tabs');
            if (!container) return;
            const classes = data.classes || [];

        if (classes.length === 0) {
            container.innerHTML = '<span class="no-classes-msg">No classes yet</span>';
            return;
        }

        container.innerHTML = '';
        classes.forEach((c, i) => {
            const btn = document.createElement('button');
            btn.className = 'class-tab' + (i === 0 ? ' active' : '');
            btn.textContent = c.class_name;
            btn.dataset.classId = c.id;
            btn.addEventListener('click', () => {
                container.querySelectorAll('.class-tab').forEach(t => t.classList.remove('active'));
                btn.classList.add('active');
                window.dispatchEvent(new CustomEvent('classChanged', { detail: c }));
            });
            container.appendChild(btn);
        });

        if (classes.length) {
            window.dispatchEvent(new CustomEvent('classChanged', { detail: classes[0] }));
        }
    })
    .catch(err => {
      console.error('Failed to load classes:', err);
      const container = document.getElementById('class-tabs');
      if (container) container.innerHTML = '<span class="no-classes-msg">Could not load classes</span>';
    });

  // logout
    const logoutBtn = document.getElementById('logout-Btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', () => {
            fetch('/logout', { method: 'POST' })
                .then(() => window.location.href = '/login.html');
        });
    }
}