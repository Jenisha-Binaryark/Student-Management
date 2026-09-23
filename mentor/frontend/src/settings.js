document.addEventListener('DOMContentLoaded', async () => {
  const form = document.getElementById('mentorSettingsForm');
  if (!form) return;
  try {
    const response = await fetch('/api/profile/details');
    if (!response.ok) throw new Error('Profile unavailable');
    const profile = await response.json();
    for (const [name, value] of Object.entries(profile)) {
      const field = form.elements[name];
      if (field) field.value = value || '';
    }
  } catch {
    setStatus('Unable to load profile details.', true);
  }
  form.addEventListener('submit', saveProfile);
});

async function saveProfile(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const payload = Object.fromEntries(new FormData(form));
  const response = await fetch('/api/profile/details', {
    method: 'PATCH',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(payload)
  });
  const data = await response.json();
  setStatus(response.ok ? 'Profile saved successfully.' : (data.error || 'Unable to save profile.'), !response.ok);
}

function setStatus(message, isError) {
  const status = document.getElementById('settingsMessage');
  if (status) {
    status.textContent = message;
    status.style.color = isError ? 'var(--pink)' : 'var(--teal)';
  }
}
