document.addEventListener("DOMContentLoaded", () => {
  const greeting = document.getElementById("greeting");
  const loadingState = document.getElementById("loadingState");
  const emptyState = document.getElementById("emptyState");
  const classList = document.getElementById("classList");

  // ---- greeting ----
  fetch("/api/current_user")
    .then((res) => {
      if (res.status === 401) {
        window.location.href = "/login.html?role=mentor";
        return null;
      }
      return res.json();
    })
    .then((data) => {
      if (!data) return;
      const firstName = data.fullname.split(" ")[0];
      greeting.textContent = `Welcome back, ${firstName}`;
    })
    .catch((err) => console.error("Failed to load user info:", err));

  // ---- classes ----
  fetch("/api/classes")
    .then((res) => {
      if (res.status === 401) {
        window.location.href = "/login.html?role=mentor";
        return null;
      }
      return res.json();
    })
    .then((data) => {
      if (!data) return;
      loadingState.style.display = "none";

      const classes = data.classes || [];

      if (classes.length === 0) {
        emptyState.style.display = "block";
        return;
      }

      classList.style.display = "flex";
      classList.innerHTML = "";

      classes.forEach((cls) => {
        const card = document.createElement("div");
        card.className = "class-card";
        card.innerHTML = `
          <div class="class-icon">${cls.class_name.charAt(0).toUpperCase()}</div>
          <div class="class-info">
            <div class="class-name">${cls.class_name}</div>
            <div class="class-meta">${cls.subject} · ${cls.course} · ${cls.university} · ${cls.year}</div>
          </div>
          <div class="class-role-pill">${cls.role}</div>
        `;
        classList.appendChild(card);
      });
    })
    .catch((err) => {
      console.error("Failed to load classes:", err);
      loadingState.textContent = "Couldn't load your classes. Please refresh.";
    });
});