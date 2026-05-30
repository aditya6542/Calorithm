/**
 * Profile page logic — populate, live BMI, card selectors, save.
 */

const ACTIVITY_LEVELS = [
  { value: "sedentary", icon: "🪑", label: "Sedentary" },
  { value: "lightly_active", icon: "🚶", label: "Lightly Active" },
  { value: "moderately_active", icon: "🏃", label: "Moderately Active" },
  { value: "very_active", icon: "💪", label: "Very Active" },
  { value: "extra_active", icon: "🔥", label: "Extra Active" },
];

const GOALS = [
  { value: "weight_loss", icon: "📉", label: "Lose Weight" },
  { value: "maintain", icon: "⚖️", label: "Maintain" },
  { value: "weight_gain", icon: "📈", label: "Gain Weight" },
  { value: "muscle_gain", icon: "💪", label: "Build Muscle" },
];

let selectedActivity = "";
let selectedGoal = "";

document.addEventListener("DOMContentLoaded", async () => {
  renderOptionCards("activityCards", ACTIVITY_LEVELS, (val) => { selectedActivity = val; });
  renderOptionCards("goalCards", GOALS, (val) => { selectedGoal = val; });

  // Live BMI calculation
  const heightInput = document.getElementById("height");
  const weightInput = document.getElementById("weight");
  if (heightInput && weightInput) {
    const update = () => {
      const bmi = calculateBMI(parseFloat(weightInput.value), parseFloat(heightInput.value));
      if (bmi) renderBMIGauge("liveBMI", bmi);
    };
    heightInput.addEventListener("input", update);
    weightInput.addEventListener("input", update);
  }

  // Load existing profile
  try {
    const data = await apiFetch("/api/profile");
    const u = data.user;
    if (u.name) document.getElementById("name").value = u.name;
    if (u.age) document.getElementById("age").value = u.age;
    if (u.gender) {
      const radio = document.querySelector(`input[name="gender"][value="${u.gender}"]`);
      if (radio) radio.checked = true;
    }
    if (u.height_cm) document.getElementById("height").value = u.height_cm;
    if (u.weight_kg) document.getElementById("weight").value = u.weight_kg;
    if (u.dietary_preference) document.getElementById("diet").value = u.dietary_preference;
    if (u.allergies) document.getElementById("allergies").value = u.allergies;

    if (u.activity_level) {
      selectedActivity = u.activity_level;
      selectCard("activityCards", u.activity_level);
    }
    if (u.goal) {
      selectedGoal = u.goal;
      selectCard("goalCards", u.goal);
    }

    // Trigger live BMI
    if (u.height_cm && u.weight_kg) {
      const bmi = calculateBMI(u.weight_kg, u.height_cm);
      if (bmi) renderBMIGauge("liveBMI", bmi);
    }
  } catch (e) { /* profile not loaded yet */ }

  // Save profile
  document.getElementById("profileForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const btn = e.target.querySelector("button[type=submit]");
    btn.disabled = true;
    btn.textContent = "Saving…";

    const genderRadio = document.querySelector('input[name="gender"]:checked');

    try {
      await apiFetch("/api/profile", {
        method: "PUT",
        body: JSON.stringify({
          name: document.getElementById("name").value,
          age: parseInt(document.getElementById("age").value) || null,
          gender: genderRadio ? genderRadio.value : null,
          height_cm: parseFloat(document.getElementById("height").value) || null,
          weight_kg: parseFloat(document.getElementById("weight").value) || null,
          activity_level: selectedActivity || null,
          goal: selectedGoal || null,
          dietary_preference: document.getElementById("diet").value || "none",
          allergies: document.getElementById("allergies").value || "",
        }),
      });

      showAlert(document.getElementById("profileForm"), "Profile saved! Redirecting to dashboard…", "success");
      // Redirect to dashboard after a brief delay
      setTimeout(() => {
        window.location.href = "dashboard.html";
      }, 1000);
    } catch (err) {
      showAlert(document.getElementById("profileForm"), err.message);
      btn.disabled = false;
      btn.textContent = "Save Profile";
    }
  });
});

function renderOptionCards(containerId, options, onSelect) {
  const container = document.getElementById(containerId);
  if (!container) return;
  container.innerHTML = "";

  options.forEach((opt) => {
    const card = document.createElement("div");
    card.className = "option-card";
    card.dataset.value = opt.value;
    card.innerHTML = `<div class="option-icon">${opt.icon}</div><div class="option-label">${opt.label}</div>`;
    card.addEventListener("click", () => {
      container.querySelectorAll(".option-card").forEach((c) => c.classList.remove("selected"));
      card.classList.add("selected");
      onSelect(opt.value);
    });
    container.appendChild(card);
  });
}

function selectCard(containerId, value) {
  const container = document.getElementById(containerId);
  if (!container) return;
  const card = container.querySelector(`[data-value="${value}"]`);
  if (card) {
    container.querySelectorAll(".option-card").forEach((c) => c.classList.remove("selected"));
    card.classList.add("selected");
  }
}
