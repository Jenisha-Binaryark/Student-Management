document.addEventListener('DOMContentLoaded', () => {
  loadMentorSidebar('timetable');

  window.addEventListener('classChanged', (e) => {
    activeClass = e.detail || null;
    updateHeading();
    loadTimetable();
  });

  window.addEventListener('classesUpdated', (e) => {
    if ((e.detail || []).length === 0) {
      activeClass = null;
      updateHeading();
      renderWeek([]);
    }
  });

  setupSlotForm();
  document.querySelectorAll('[data-timetable-type]').forEach(btn => btn.addEventListener('click', () => {
    document.querySelectorAll('[data-timetable-type]').forEach(item => item.classList.remove('active'));
    btn.classList.add('active');
    activeTimetableType = btn.dataset.timetableType;
    loadTimetable();
  }));
});

let activeClass = null;
let activeTimetableType = 'regular';

const DAY_LABELS = {
  Mon: 'Monday', Tue: 'Tuesday', Wed: 'Wednesday', Thu: 'Thursday',
  Fri: 'Friday', Sat: 'Saturday', Sun: 'Sunday',
};
const DAY_ORDER = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

function updateHeading() {
  const heading = document.getElementById('timetableActiveClass');
  if (!heading) return;
  heading.textContent = activeClass
    ? `Showing schedule for ${activeClass.class_name}.`
    : 'Add or select a class above to see its schedule.';
}

function loadTimetable() {
  const container = document.getElementById('timetableWeek');
  if (!container) return;

  if (!activeClass) {
    container.innerHTML = '<p class="empty-hint">Select a class above to see its schedule.</p>';
    return;
  }

  container.innerHTML = '<p class="empty-hint">Loading…</p>';

  fetch(`/api/timetable?class_id=${activeClass.id}&timetable_type=${activeTimetableType}`)
    .then(res => {
      if (res.status === 401 || res.status === 403) {
        window.location.href = res.status === 403 ? '/mentor/onboarding.html' : '/login.html?role=mentor';
        return null;
      }
      return res.json();
    })
    .then(data => {
      if (data) renderWeek(data.slots || []);
    })
    .catch(err => {
      console.error('Failed to load timetable:', err);
      container.innerHTML = '<p class="empty-hint">Could not load timetable.</p>';
    });
}

function renderWeek(slots) {
  const container = document.getElementById('timetableWeek');
  if (!container) return;
  container.innerHTML = '';

  if (!activeClass) {
    container.innerHTML = '<p class="empty-hint">Select a class above to see its schedule.</p>';
    return;
  }

  if (slots.length === 0) {
    container.innerHTML = '<p class="empty-hint">No slots yet for this class.</p>';
    return;
  }

  const byDay = {};
  slots.forEach(s => {
    (byDay[s.day_of_week] = byDay[s.day_of_week] || []).push(s);
  });

  DAY_ORDER.forEach(day => {
    const daySlots = byDay[day];
    if (!daySlots || daySlots.length === 0) return;

    const group = document.createElement('div');
    group.className = 'timetable-day-group';

    const heading = document.createElement('div');
    heading.className = 'timetable-day-heading';
    heading.textContent = DAY_LABELS[day];
    group.appendChild(heading);

    daySlots.forEach(s => {
      const row = document.createElement('div');
      row.className = 'timetable-slot';
      row.innerHTML = `
        <div class="timetable-slot-time">${s.start_time} – ${s.end_time}</div>
        <div class="timetable-slot-body">
          <div class="timetable-slot-subject">${escapeHtml(s.subject)}</div>
          ${s.room ? `<div class="timetable-slot-room">${escapeHtml(s.room)}</div>` : ''}
        </div>
        <button type="button" class="timetable-slot-delete" title="Remove slot" data-id="${s.id}">✕</button>
      `;
      row.querySelector('.timetable-slot-delete').addEventListener('click', () => deleteSlot(s.id));
      group.appendChild(row);
    });

    container.appendChild(group);
  });
}

function deleteSlot(id) {
  if (!window.confirm('Remove this timetable slot?')) return;
  fetch(`/api/timetable/${id}`, { method: 'DELETE' })
    .then(res => {
      if (res.status === 401) {
        window.location.href = r.status === 403 ? '/mentor/onboarding.html' : '/login.html?role=mentor';
        return null;
      }
      return res.json();
    })
    .then(data => {
      if (data) loadTimetable();
    })
    .catch(err => console.error('Failed to delete slot:', err));
}

function setupSlotForm() {
  const form = document.getElementById('slotForm');
  const message = document.getElementById('slotMessage');
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
      day_of_week: document.getElementById('slotDay').value,
      subject: document.getElementById('slotSubject').value.trim(),
      start_time: document.getElementById('slotStart').value,
      end_time: document.getElementById('slotEnd').value,
      room: document.getElementById('slotRoom').value.trim(),
      timetable_type: activeTimetableType,
    };

    if (!payload.subject || !payload.start_time || !payload.end_time) {
      message.textContent = 'Please fill in subject, start time, and end time.';
      message.style.color = '#d1567f';
      return;
    }
    if (payload.end_time <= payload.start_time) {
      message.textContent = 'End time must be after start time.';
      message.style.color = '#d1567f';
      return;
    }

    try {
      const res = await fetch('/api/timetable', {
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

      message.textContent = 'Slot added!';
      message.style.color = '#5aada0';
      form.reset();
      loadTimetable();
    } catch (err) {
      console.error(err);
      message.textContent = 'Server error. Please try again.';
      message.style.color = '#d1567f';
    }
  });
}