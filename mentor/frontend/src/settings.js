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
    setPhotoPreview(profile.profile_photo, profile.fullname);
  } catch {
    setStatus('Unable to load profile details.', true);
  }
  form.addEventListener('submit', saveProfile);
  setupPhotoUpload();
});

async function saveProfile(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const payload = Object.fromEntries(new FormData(form));
  const response = await fetch('/api/profile/details', {method: 'PATCH', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload)});
  const data = await response.json();
  setStatus(response.ok ? 'Profile saved successfully.' : (data.error || 'Unable to save profile.'), !response.ok);
}

function setupPhotoUpload() {
  const form = document.getElementById('mentorPhotoForm');
  const input = document.getElementById('mentorPhoto');
  const status = document.getElementById('mentorPhotoStatus');
  if (!form || !input) return;
  input.addEventListener('change', () => {
    const file = input.files?.[0];
    if (!file) return;
    if (file.size > 2 * 1024 * 1024) { status.textContent = 'Choose an image no larger than 2 MB.'; input.value = ''; return; }
    const reader = new FileReader();
    reader.onload = () => setPhotoPreview(reader.result, document.getElementById('mentorFullname')?.value);
    reader.readAsDataURL(file);
  });
  form.addEventListener('submit', async event => {
    event.preventDefault();
    const file = input.files?.[0];
    if (!file) return;
    status.textContent = 'Uploading…';
    const body = new FormData(); body.append('photo', file);
    const response = await fetch('/api/profile/photo', {method: 'POST', body});
    const data = await response.json();
    status.textContent = response.ok ? 'Profile photo updated.' : (data.error || 'Could not upload photo.');
    status.style.color = response.ok ? 'var(--teal)' : 'var(--pink)';
  });
}

function setPhotoPreview(photo, fullname) {
  const image = document.getElementById('mentorPhotoPreview');
  const placeholder = document.getElementById('mentorPhotoPlaceholder');
  if (!image || !placeholder) return;
  placeholder.textContent = (fullname || 'M').slice(0, 1).toUpperCase();
  if (photo) { image.src = photo; image.hidden = false; placeholder.hidden = true; }
  else { image.hidden = true; placeholder.hidden = false; }
}

function setStatus(message, isError) {
  const status = document.getElementById('settingsMessage');
  if (status) { status.textContent = message; status.style.color = isError ? 'var(--pink)' : 'var(--teal)'; }
}
