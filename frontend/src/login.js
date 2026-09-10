document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("loginForm");
  const message = document.getElementById("message");
  const roleInput = document.getElementById("role");
  const studentBtn = document.getElementById("studentBtn");
  const mentorBtn = document.getElementById("mentorBtn");
  const password = document.getElementById("password");
  const toggleEye = document.getElementById("toggleEye");

  const urlParams = new URLSearchParams(window.location.search);
  const selectedRole = urlParams.get("role");

  if (selectedRole === "mentor") {
    roleInput.value = "mentor";
    mentorBtn.classList.add("active");
    studentBtn.classList.remove("active");
  } else {
    roleInput.value = "student";
    studentBtn.classList.add("active");
    mentorBtn.classList.remove("active");
  }

  studentBtn.addEventListener("click", () => {
    roleInput.value = "student";
    studentBtn.classList.add("active");
    mentorBtn.classList.remove("active");
  });

  mentorBtn.addEventListener("click", () => {
    roleInput.value = "mentor";
    mentorBtn.classList.add("active");
    studentBtn.classList.remove("active");
  });

  toggleEye.addEventListener("click", () => {
    const isHidden = password.type === "password";
    password.type = isHidden ? "text" : "password";
    toggleEye.classList.toggle("fa-eye-slash", !isHidden);
    toggleEye.classList.toggle("fa-eye", isHidden);
  });

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    message.textContent = "";

    const username = form.username.value.trim();
    const passwordVal = password.value;
    const role = roleInput.value;

    if (!username || !passwordVal) {
      message.textContent = "Please fill in both fields.";
      message.style.color = "red";
      return;
    }

    try {
      const response = await fetch("/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          username,
          password: passwordVal,
          role
        }),
      });

      const data = await response.json();

      if (data.status === "not_found") {
        message.textContent = "User does not exist! Redirecting to signup...";
        message.style.color = "orange";
        setTimeout(() => (window.location.href = "/?role=" + role), 1500);
      } else if (data.status === "wrong_password") {
        message.textContent = "Incorrect password. Please try again.";
        message.style.color = "red";
      } else if (data.status === "success") {
        message.textContent = "Login successful! Redirecting...";
        message.style.color = "green";

        setTimeout(() => {
          if (data.role === "mentor") {
            window.location.href = "/mentor/onboarding.html";
          } else {
            window.location.href = "/dashboard.html";
          }
        }, 1500);
      } else {
        message.textContent = data.message || "Something went wrong.";
        message.style.color = "red";
      }
    } catch (err) {
      console.error(err);
      message.textContent = "Server error. Please try again later.";
      message.style.color = "red";
    }
  });
});