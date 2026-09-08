document.addEventListener("DOMContentLoaded", async () => {
  loadHomework();
  setupTabs();
  // setupLogout();

fetch('/sidebar.html')
  .then(res => {
    if (res.status === 401) {
      window.location.href = '/login.html';
      return null;
    }
    return res.text();
  })
  .then(data => {
    if (!data) return;
    document.getElementById('sidebar-placeholder').innerHTML = data;
    initSidebar();
  })
  .catch(err => console.error('Failed to load sidebar:', err));

function initSidebar() {
  const usernameEl = document.getElementById('sidebar-username');
  if (usernameEl) {
    fetch('/api/current_user')
      .then(r => r.json())
      .then(u => {
        if (u.status === 'success') usernameEl.textContent = u.fullname;
      });
  }

  const logoutBtn = document.getElementById('logout-Btn');
  if (logoutBtn) {
    logoutBtn.addEventListener('click', () => {
      fetch('/logout', { method: 'POST' })
        .then(() => window.location.href = '/login.html');
    });
  }
}
  try {
    const res = await fetch("/api/current_user");
    if (res.status === 401) {
      window.location.href = "/login.html";
      return;
    }
    const data = await res.json();
    document.getElementById("sidebar-username").textContent = data.fullname;
    document.getElementById("user-first-name").textContent =
      data.fullname.split(" ")[0].toUpperCase();
  } catch (err) {
    console.error("Failed to load user info:", err);
  }

  function setupTabs() {
    const tabs = document.querySelectorAll('.tab');
    const panels = document.querySelectorAll('.panel');
    tabs.forEach(tab => {
      tab.addEventListener('click', () => {
        tabs.forEach(t => t.classList.remove('active'));
        panels.forEach(p => p.classList.remove('active'));
        tab.classList.add('active');
        const target = tab.dataset.tab;
        document.getElementById(`panel-${target}`).classList.add('active');
      });
    });
  }

  async function loadHomework() {
    try {
      const res = await fetch('/api/homework');
      if (!res.ok) throw new Error('Bad response');
      const homework = await res.json();
      renderAll(homework);
    } catch (err) {
      console.error('Failed to load homework, using demo data:', err);
      const demo = [
        { title: 'Robotics worksheet', subject: 'Robotics', due: '18 Sep', status: 'assigned' },
        { title: 'Electronics report', subject: 'Electronics', due: '19 Sep', status: 'assigned' },
        { title: 'Minecraft webinar notes', subject: 'IT', due: '12 Sep', status: 'missing' },
        { title: 'Math problem set 3', subject: 'Math', due: '10 Sep', status: 'done' },
      ];
      renderAll(demo);
    }
  }

  function renderAll(homework) {
    const assigned = homework.filter(h => h.status === 'assigned');
    const missing = homework.filter(h => h.status === 'missing');
    const done = homework.filter(h => h.status === 'done');

    renderPanel('assigned', assigned);
    renderPanel('missing', missing);
    renderPanel('done', done);

    updateBadge('assigned', assigned.length);
    updateBadge('missing', missing.length);
    updateBadge('done', done.length);
  }

  function renderPanel(tabName, items) {
    const panel = document.getElementById(`panel-${tabName}`);
    panel.innerHTML = '';

    if (items.length === 0) {
      panel.innerHTML = `<p class="empty-state">Nothing here yet.</p>`;
      return;
    }

    items.forEach(item => {
  const isOverdue = item.status === 'missing';
  const isDone = item.status === 'done';

  const card = document.createElement('div');
  card.className = `assignment-card${isOverdue ? ' overdue' : ''}${isDone ? ' done' : ''}`;

  card.innerHTML = `
    <div class="icon-badge">${isDone ? '✓' : isOverdue ? '!' : '📘'}</div>
    <div class="assignment-body">
      <div class="assignment-top">
        <div class="assignment-title${isDone ? ' done-title' : ''}">${item.title}</div>
        <div class="due-wrap">
          <div class="assignment-due${isOverdue ? ' overdue-text' : ''}">Due ${item.due}</div>
          ${!isDone ? `<button type="button" class="attach-btn" aria-label="Attach file"><i class="fa-solid fa-plus"></i></button>` : ''}
        </div>
      </div>
      <div class="assignment-meta">${item.subject}</div>
      <div class="assignment-footer">
        <span class="points-pill">${item.status}</span>
      </div>
    </div>
  `;
  panel.appendChild(card);
});
  }

  function updateBadge(tabName, count) {
    document.getElementById(`badge-${tabName}`).textContent = count;
  }

  document.getElementById("logout-Btn").addEventListener('click', function(){
    fetch("/logout", {method:"POST"})
        .then(function(response){
            return response.json();
        })
        .then(function(data){
            if(data.status === "success"){
                window.location.href = "/login.html";
            }
        })
  });
});