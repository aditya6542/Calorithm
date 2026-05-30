/**
 * Auth logic — login & register forms.
 */

document.addEventListener("DOMContentLoaded", () => {
  const loginForm = document.getElementById("loginForm");
  const registerForm = document.getElementById("registerForm");

  if (loginForm) {
    loginForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const btn = loginForm.querySelector("button[type=submit]");
      btn.disabled = true;
      btn.textContent = "Signing in…";

      try {
        const data = await apiFetch("/api/auth/login", {
          method: "POST",
          body: JSON.stringify({
            email: document.getElementById("email").value,
            password: document.getElementById("password").value,
          }),
        });

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
