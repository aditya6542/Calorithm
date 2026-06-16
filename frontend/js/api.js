/**
 * API helper — centralised fetch wrapper for the backend.
 */
const API_BASE = "";  // same origin — works on localhost & ngrok

async function apiFetch(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;

  const defaults = {
    headers: { "Content-Type": "application/json" },
    credentials: "include",            // send session cookie
  };

  const config = { ...defaults, ...options, headers: { ...defaults.headers, ...options.headers } };

  const res = await fetch(url, config);

  if (res.status === 401) {
    // Not logged in — redirect to login page
    if (!window.location.pathname.endsWith("index.html") && !window.location.pathname.endsWith("/")) {
      window.location.href = "index.html";
    }
    throw new Error("Authentication required");
  }

  const data = await res.json();

  if (!res.ok) {
    throw new Error(data.error || "Something went wrong");
  }

  return data;
}

function showAlert(container, message, type = "error") {
  const existing = container.querySelector(".alert");
  if (existing) existing.remove();

  const div = document.createElement("div");
  div.className = `alert alert-${type}`;
  div.textContent = message;
  container.prepend(div);

  setTimeout(() => div.remove(), 5000);
}
