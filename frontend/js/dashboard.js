/**
 * Dashboard page — loads profile, BMI, generates & displays meal plans.
 */

document.addEventListener("DOMContentLoaded", async () => {
  // ── Load user data ─────────────────────────────────────
  try {
    const data = await apiFetch("/api/auth/me");
    const user = data.user;

    document.getElementById("userName").textContent = user.name;
    document.getElementById("navUserName").textContent = user.name;

    // Stats
    document.getElementById("statGoal").textContent = formatGoal(user.goal);
    document.getElementById("statActivity").textContent = formatActivity(user.activity_level);
    document.getElementById("statWeight").textContent = user.weight_kg ? `${user.weight_kg} kg` : "—";

    // BMI
    if (user.height_cm && user.weight_kg) {
      const bmiData = await apiFetch("/api/profile/bmi");
      renderBMIGauge("bmiGauge", bmiData.bmi, { label: bmiData.category, color: bmiData.color });
      document.getElementById("bmiRange").textContent =
        `Healthy range: ${bmiData.healthy_weight_range.min_kg}–${bmiData.healthy_weight_range.max_kg} kg`;
    }

    if (!user.profile_complete) {
      showAlert(document.querySelector(".dashboard-content"), "Complete your profile to generate meal plans.", "error");
    }
  } catch (e) {
    /* redirect handled by api.js */
  }

  // ── Cache of plans ─────────────────────────────────────
  let allPlans = [];

  // ── Load history & show latest ─────────────────────────
  await loadHistory(true);

  // ── Plan type toggle ───────────────────────────────────
  document.querySelectorAll(".toggle-group button").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".toggle-group button").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      displayLatestPlanOfType(btn.dataset.type);
    });
  });

  // ── Generate button ────────────────────────────────────
  document.getElementById("generateBtn").addEventListener("click", generatePlan);

  // ── Logout ─────────────────────────────────────────────
  document.getElementById("logoutBtn").addEventListener("click", async () => {
    try { await apiFetch("/api/auth/logout", { method: "POST" }); } catch (e) { /* ok */ }
    window.location.href = "index.html";
  });

  // ── Display latest plan helper ─────────────────────────
  function displayLatestPlanOfType(type) {
    const plan = allPlans.find((p) => p.plan_type === type);
    if (plan) {
      renderMealPlan(plan);
    } else {
      const display = document.getElementById("mealPlanDisplay");
      display.innerHTML = `
        <p style="color:var(--text-muted);text-align:center;padding:60px 20px;font-size:0.95rem;">
          Click "Generate Meal Plan" to get your AI-powered personalized ${type === "daily" ? "daily" : "weekly"} nutrition plan.
        </p>`;
    }
  }

  async function generatePlan() {
    const btn = document.getElementById("generateBtn");
    const activeToggle = document.querySelector(".toggle-group button.active");
    const planType = activeToggle ? activeToggle.dataset.type : "daily";

    btn.disabled = true;
    btn.textContent = "Generating…";

    // Show loading
    const display = document.getElementById("mealPlanDisplay");
    display.innerHTML = `<div class="loading-overlay"><div class="spinner"></div><p>AI is crafting your personalized meal plan…</p></div>`;

    try {
      const data = await apiFetch("/api/meal/generate", {
        method: "POST",
        body: JSON.stringify({ plan_type: planType }),
      });

      renderMealPlan(data.meal_plan);
      await loadHistory();
    } catch (err) {
      display.innerHTML = "";
      showAlert(document.querySelector(".dashboard-content"), err.message);
    }

    btn.disabled = false;
    btn.textContent = "✨ Generate Meal Plan";
  }

  function renderMealPlan(mealPlan) {
    const display = document.getElementById("mealPlanDisplay");
    const plan = mealPlan.plan_data;

    if (!plan || !plan.days || plan.days.length === 0) {
      display.innerHTML = `<p style="color:var(--text-secondary);text-align:center;padding:40px;">No meal data returned. Try generating again.</p>`;
      return;
    }

    // If daily plan (only 1 day), render single day layout
    if (plan.days.length === 1) {
      display.innerHTML = renderSingleDay(plan.days[0]);
      return;
    }

    // If weekly plan, render tabbed interface for days
    let html = `<div class="weekly-planner-wrapper">`;
    
    // Day tabs nav
    html += `<div class="weekly-tabs-nav">`;
    plan.days.forEach((day, index) => {
      const isActive = index === 0 ? "active" : "";
      html += `<button class="weekly-tab-btn ${isActive}" data-day-index="${index}">${day.day}</button>`;
    });
    html += `</div>`;

    // Day panels content
    html += `<div class="weekly-tabs-content">`;
    plan.days.forEach((day, index) => {
      const isHidden = index === 0 ? "" : "style='display:none;'";
      html += `<div class="weekly-day-pane weekly-day-${index}" ${isHidden}>`;
      html += renderSingleDayContent(day);
      html += `</div>`;
    });
    html += `</div></div>`;

    display.innerHTML = html;

    // Set up tab switching listeners
    const tabs = display.querySelectorAll(".weekly-tab-btn");
    const panes = display.querySelectorAll(".weekly-day-pane");
    tabs.forEach((tab) => {
      tab.addEventListener("click", () => {
        tabs.forEach((t) => t.classList.remove("active"));
        panes.forEach((p) => p.style.display = "none");

        tab.classList.add("active");
        const index = tab.dataset.dayIndex;
        const targetPane = display.querySelector(`.weekly-day-${index}`);
        if (targetPane) {
          targetPane.style.display = "block";
          targetPane.style.opacity = 0;
          setTimeout(() => {
            targetPane.style.transition = "opacity 0.2s ease";
            targetPane.style.opacity = 1;
          }, 10);
        }
      });
    });
  }

  function renderSingleDay(day) {
    let html = `<div class="day-section">`;
    html += `<div class="day-header" style="border-bottom:none;margin-bottom:0;">${day.day} Overview</div>`;
    html += renderSingleDayContent(day);
    html += `</div>`;
    return html;
  }

  function renderSingleDayContent(day) {
    let html = `
      <div class="day-summary" style="margin-top:12px;">
        <span class="summary-item">🔥 <strong>${day.total_calories || "—"}</strong> kcal</span>
        <span class="summary-item">🥩 <strong>${day.total_protein || "—"}</strong>g protein</span>
        <span class="summary-item">🍞 <strong>${day.total_carbs || "—"}</strong>g carbs</span>
        <span class="summary-item">🧈 <strong>${day.total_fat || "—"}</strong>g fat</span>
      </div>
      <div class="meals-grid" style="margin-top:16px;">`;

    (day.meals || []).forEach((meal) => {
      const maxMacro = Math.max(meal.protein || 0, meal.carbs || 0, meal.fat || 0, 1);
      html += `
        <div class="meal-card">
          <div class="meal-type" style="color:var(--accent-2);">${meal.meal_type || ""}</div>
          <div class="meal-name">${meal.name || "Meal"}</div>
          <div class="meal-meta">
            <span class="meal-meta-item">🔥 <span class="meta-value">${meal.calories || "—"}</span> kcal</span>
            <span class="meal-meta-item">⏱ <span class="meta-value">${meal.prep_time || "—"}</span></span>
          </div>
          <div class="macro-bars">
            <div class="macro-bar">
              <div class="bar-track"><div class="bar-fill protein" style="width:${((meal.protein || 0) / maxMacro) * 100}%"></div></div>
              <div class="bar-label">Protein ${meal.protein || 0}g</div>
            </div>
            <div class="macro-bar">
              <div class="bar-track"><div class="bar-fill carbs" style="width:${((meal.carbs || 0) / maxMacro) * 100}%"></div></div>
              <div class="bar-label">Carbs ${meal.carbs || 0}g</div>
            </div>
            <div class="macro-bar">
              <div class="bar-track"><div class="bar-fill fat" style="width:${((meal.fat || 0) / maxMacro) * 100}%"></div></div>
              <div class="bar-label">Fat ${meal.fat || 0}g</div>
            </div>
          </div>
          <ul class="ingredients-list">${(meal.ingredients || []).map((i) => `<li>${i}</li>`).join("")}</ul>
          <div class="instructions">${meal.instructions || ""}</div>
        </div>`;
    });

    html += `</div>`;
    return html;
  }

  async function loadHistory(initialLoad = false) {
    const container = document.getElementById("historyList");
    if (!container) return;

    try {
      const data = await apiFetch("/api/meal/history");
      allPlans = data.meal_plans || [];

      if (allPlans.length === 0) {
        container.innerHTML = `<p style="color:var(--text-muted);font-size:0.9rem;">No meal plans yet. Generate your first one!</p>`;
        return;
      }

      container.innerHTML = allPlans.map((p) => `
        <div class="history-item" data-id="${p.id}" style="cursor:pointer;">
          <span class="history-date">${new Date(p.created_at).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric", hour: "2-digit", minute: "2-digit" })}</span>
          <span class="history-type">${p.plan_type}</span>
          <span class="history-cals">${p.total_calories || "—"} kcal</span>
        </div>`).join("");

      // Add click listeners to history items
      container.querySelectorAll(".history-item").forEach((item) => {
        item.addEventListener("click", () => {
          const id = parseInt(item.dataset.id);
          const plan = allPlans.find((p) => p.id === id);
          if (plan) {
            renderMealPlan(plan);
            // Set active toggle
            document.querySelectorAll(".toggle-group button").forEach((b) => {
              if (b.dataset.type === plan.plan_type) {
                b.classList.add("active");
              } else {
                b.classList.remove("active");
              }
            });
            window.scrollTo({ top: document.getElementById("mealPlanDisplay").offsetTop - 80, behavior: "smooth" });
          }
        });
      });

      if (initialLoad) {
        const activeToggle = document.querySelector(".toggle-group button.active");
        const activeType = activeToggle ? activeToggle.dataset.type : "daily";
        displayLatestPlanOfType(activeType);
      }
    } catch (e) { /* ignore */ }
  }
});

function formatGoal(g) {
  const map = { weight_loss: "Lose Weight", weight_gain: "Gain Weight", maintain: "Maintain", muscle_gain: "Build Muscle" };
  return map[g] || "—";
}
function formatActivity(a) {
  const map = { sedentary: "Sedentary", lightly_active: "Lightly Active", moderately_active: "Moderately Active", very_active: "Very Active", extra_active: "Extra Active" };
  return map[a] || "—";
}
