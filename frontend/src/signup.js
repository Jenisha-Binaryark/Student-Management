document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("signupForm");
  const message = document.getElementById("message");
  const roleInput = document.getElementById("role");
  const studentBtn = document.getElementById("studentBtn");
  const mentorBtn = document.getElementById("mentorBtn");
  const password = document.getElementById("password");
  const confirmPassword = document.getElementById("confirmPassword");
  const toggleEye = document.getElementById("toggleEye");
  const confirmToggleEye = document.getElementById("confirmToggleEye");
  const mentorIdGroup = document.getElementById("mentorIdGroup");
  const mentorId = document.getElementById("mentorId");

  studentBtn.addEventListener("click", () => {
    roleInput.value = "student";
    studentBtn.classList.add("active");
    mentorBtn.classList.remove("active");

    mentorIdGroup.style.display = "none";
    mentorId.value = "";
  });

  mentorBtn.addEventListener("click", () => {
    roleInput.value = "mentor";
    mentorBtn.classList.add("active");
    studentBtn.classList.remove("active");

    mentorIdGroup.style.display = "block";
  });

  

  function setupToggle(inputEl, iconEl) {
    iconEl.addEventListener("click", () => {
      const isHidden = inputEl.type === "password";
      inputEl.type = isHidden ? "text" : "password";
      iconEl.classList.toggle("fa-eye-slash", !isHidden);
      iconEl.classList.toggle("fa-eye", isHidden);
    });
  }

  setupToggle(password, toggleEye);
  setupToggle(confirmPassword, confirmToggleEye);

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    message.textContent = "";

    const fullname = form.fullname.value.trim();
    const email = form.email.value.trim();
    const phone = form.phone.value.trim();
    const passwordVal = password.value;
    const confirmVal = confirmPassword.value;
    const role = roleInput.value;
    const referral = form.referral.value.trim();
    const mentorIdVal = mentorId.value.trim();

    const nameRegex = /^[A-Za-z\s]+$/;
    if (!nameRegex.test(fullname)) {
      message.textContent = "Full name should only contain letters and spaces.";
      message.style.color = "red";
      return;
    }

    const phoneRegex = /^\d{10}$/;
    if (!phoneRegex.test(phone)) {
      message.textContent = "Phone number must be exactly 10 digits.";
      message.style.color = "red";
      return;
    }

    if (role === "mentor" && !mentorIdVal) {
      message.textContent = "Mentor ID is required.";
      message.style.color = "red";
      return;
    }

    if (passwordVal !== confirmVal) {
      message.textContent = "Passwords do not match!";
      message.style.color = "red";
      return;
    }

    const passwordRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$/;
    if (!passwordRegex.test(passwordVal)) {
      message.textContent = "Password must be 8+ chars with uppercase, lowercase, number, and special character.";
      message.style.color = "red";
      return;
    }

    try {
      const response = await fetch("/signup", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          fullname,
          email,
          phone,
          password: passwordVal,
          role,
          referral,
          mentorId: role === "mentor" ? mentorIdVal : null
        }),
      });

      const data = await response.json();

      if (data.status === "exists") {
        message.textContent = "User already exists! Redirecting to login...";
        message.style.color = "orange";
        setTimeout(() => (window.location.href = "/login.html?role=" + role), 1500);
      } else if (data.status === "created") {
        message.textContent = "Account created successfully! Please login now! Redirecting to login...";
        message.style.color = "green";
        setTimeout(() => (window.location.href = "/login.html?role=" + role), 1500);
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