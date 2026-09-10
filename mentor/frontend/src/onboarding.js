document.addEventListener("DOMContentLoaded", () => {
  const message = document.getElementById("message");
  const stepper = document.getElementById("stepper");
  const profileStepEl = stepper.querySelector('[data-step="profile"]');
  const classStepEl = stepper.querySelector('[data-step="class"]');
  const panelProfile = document.getElementById("panel-profile");
  const panelClass = document.getElementById("panel-class");
  const profileForm = document.getElementById("profileForm");
  const classForm = document.getElementById("classForm");
  const backBtn = document.getElementById("backBtn");

  function showMessage(text, color) {
    message.textContent = text || "";
    message.style.color = color || "var(--text-muted)";
  }

  function showPanel(name) {
    panelProfile.classList.toggle("active", name === "profile");
    panelClass.classList.toggle("active", name === "class");

    profileStepEl.classList.toggle("current", name === "profile");
    classStepEl.classList.toggle("current", name === "class");
  }

  // ---- figure out where the mentor should start ----
  fetch("/api/profile/status")
    .then((res) => {
      if (res.status === 401) {
        window.location.href = "/login.html?role=mentor";
        return null;
      }
      return res.json();
    })
    .then((status) => {
      if (!status) return;

      if (status.all_complete) {
        window.location.href = "/mentor/dashboard.html";
        return;
      }

      const profileDone = status.steps?.find((s) => s.label === "Profile details")?.done;

      if (profileDone) {
        profileStepEl.classList.add("done");
        profileStepEl.classList.remove("current");
        showPanel("class");
      } else {
        showPanel("profile");
      }
    })
    .catch((err) => {
      console.error("Failed to load onboarding status:", err);
    });

  // ---- step 1: profile details ----
  profileForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    showMessage("");

    const department = document.getElementById("department").value.trim();
    const designation = document.getElementById("designation").value.trim();

    if (!department || !designation) {
      showMessage("Please fill in both fields.", "red");
      return;
    }

    try {
      const res = await fetch("/api/profile/complete", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ department, designation }),
      });

      if (res.status === 401) {
        window.location.href = "/login.html?role=mentor";
        return;
      }

      const data = await res.json();

      if (!res.ok) {
        showMessage(data.error || "Something went wrong.", "red");
        return;
      }

      profileStepEl.classList.add("done");
      profileStepEl.classList.remove("current");
      showMessage("");
      showPanel("class");
    } catch (err) {
      console.error(err);
      showMessage("Server error. Please try again.", "red");
    }
  });

  // ---- step 2: create class ----
  backBtn.addEventListener("click", () => {
    profileStepEl.classList.remove("done");
    showMessage("");
    showPanel("profile");
  });

  classForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    showMessage("");

    const payload = {
      class_name: document.getElementById("class_name").value.trim(),
      university: document.getElementById("university").value.trim(),
      course: document.getElementById("course").value.trim(),
      year: document.getElementById("year").value.trim(),
      subject: document.getElementById("subject").value.trim(),
      role: document.getElementById("role").value,
    };

    if (Object.values(payload).some((v) => !v)) {
      showMessage("Please fill in every field.", "red");
      return;
    }

    try {
      const res = await fetch("/api/classes", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (res.status === 401) {
        window.location.href = "/login.html?role=mentor";
        return;
      }

      const data = await res.json();

      if (!res.ok) {
        showMessage(data.error || "Something went wrong.", "red");
        return;
      }

      classStepEl.classList.add("done");
      classStepEl.classList.remove("current");
      showMessage("Setup complete! Redirecting to your dashboard...", "green");
      setTimeout(() => {
        window.location.href = "/mentor/dashboard.html";
      }, 1200);
    } catch (err) {
      console.error(err);
      showMessage("Server error. Please try again.", "red");
    }
  });
});