/**
 * Auth logic — login & register forms.
 */

document.addEventListener("DOMContentLoaded", () => {
  const loginForm = document.getElementById("loginForm");
  const registerForm = document.getElementById("registerForm");

  if (loginForm) {
    // Autofill email and rememberMe state from localStorage
    const savedEmail = localStorage.getItem("calorithm_remembered_email");
    const rememberMeCheckbox = document.getElementById("rememberMe");
    if (savedEmail) {
      document.getElementById("email").value = savedEmail;
      if (rememberMeCheckbox) rememberMeCheckbox.checked = true;
    }

    // Quick demo login button
    const quickDemoBtn = document.getElementById("quickDemoBtn");
    if (quickDemoBtn) {
      quickDemoBtn.addEventListener("click", () => {
        document.getElementById("email").value = "demo@calorithm.com";
        document.getElementById("password").value = "demo1234";
        if (rememberMeCheckbox) rememberMeCheckbox.checked = true;
        
        // Wait a small bit for visual feedback before submitting
        const demoBox = document.querySelector(".demo-login-box");
        if (demoBox) demoBox.style.borderColor = "var(--accent)";
        setTimeout(() => {
          loginForm.querySelector("button[type=submit]").click();
        }, 150);
      });
    }

    loginForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const btn = loginForm.querySelector("button[type=submit]");
      btn.disabled = true;
      btn.textContent = "Signing in…";

      const emailVal = document.getElementById("email").value;
      const rememberVal = rememberMeCheckbox ? rememberMeCheckbox.checked : false;

      try {
        const data = await apiFetch("/api/auth/login", {
          method: "POST",
          body: JSON.stringify({
            email: emailVal,
            password: document.getElementById("password").value,
            remember: rememberVal,
          }),
        });

        // Store or clear email in localStorage
        if (rememberVal) {
          localStorage.setItem("calorithm_remembered_email", emailVal);
        } else {
          localStorage.removeItem("calorithm_remembered_email");
        }

        // Redirect based on profile completeness
        if (data.user.profile_complete) {
          window.location.href = "dashboard.html";
        } else {
          window.location.href = "profile.html";
        }
      } catch (err) {
        showAlert(loginForm, err.message);
        btn.disabled = false;
        btn.textContent = "Sign In";
      }
    });
  }

  if (registerForm) {
    registerForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const btn = registerForm.querySelector("button[type=submit]");
      btn.disabled = true;
      btn.textContent = "Creating account…";

      const password = document.getElementById("password").value;
      const confirm = document.getElementById("confirmPassword").value;

      if (password !== confirm) {
        showAlert(registerForm, "Passwords do not match");
        btn.disabled = false;
        btn.textContent = "Create Account";
        return;
      }

      try {
        await apiFetch("/api/auth/register", {
          method: "POST",
          body: JSON.stringify({
            name: document.getElementById("name").value,
            email: document.getElementById("email").value,
            password: password,
          }),
        });

        window.location.href = "profile.html";
      } catch (err) {
        showAlert(registerForm, err.message);
        btn.disabled = false;
        btn.textContent = "Create Account";
      }
    });
  }
});
