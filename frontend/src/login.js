document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("loginForm");
  const message = document.getElementById("message");
  const roleInput = document.getElementById("role");
  const studentBtn = document.getElementById("studentBtn");
  const mentorBtn = document.getElementById("mentorBtn");
  const password = document.getElementById("password");
  const toggleEye = document.getElementById("toggleEye");

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

  // Password visibility toggle
  toggleEye.addEventListener("click", () => {
    const isHidden = password.type === "password";
    password.type = isHidden ? "text" : "password";
    toggleEye.classList.toggle("fa-eye-slash", !isHidden);
    toggleEye.classList.toggle("fa-eye", isHidden);
  });

  // Form submission
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    message.textContent = "";

    const username = form.username.value.trim();
    const passwordVal = password.value;

    if (!username || !passwordVal) {
      message.textContent = "Please fill in both fields.";
      message.style.color = "red";
      return;
    }

    try {
      const response = await fetch("/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password: passwordVal }),
      });

      const data = await response.json();

      if (data.status === "not_found") {
        message.textContent = "User does not exist! Redirecting to signup...";
        message.style.color = "orange";
        setTimeout(() => (window.location.href = "signup.html"), 1500);
      } else if (data.status === "wrong_password") {
        message.textContent = "Incorrect password. Please try again.";
        message.style.color = "red";
      } else if (data.status === "success") {
        message.textContent = "Login successful! Redirecting...";
        message.style.color = "green";
        setTimeout(() => (window.location.href = "/dashboard.html"), 1500);
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