/**
 * BMI calculator helpers for client-side use.
 */

function calculateBMI(weightKg, heightCm) {
  if (!weightKg || !heightCm || heightCm <= 0 || weightKg <= 0) return null;
  const heightM = heightCm / 100;
  const bmi = weightKg / (heightM * heightM);
  return Math.round(bmi * 10) / 10;
}

function getBMICategory(bmi) {
  if (bmi < 18.5) return { label: "Underweight", color: "#f0ad4e" };
  if (bmi < 25) return { label: "Normal", color: "#00d68f" };
  if (bmi < 30) return { label: "Overweight", color: "#ff6b35" };
  return { label: "Obese", color: "#ff4757" };
}

/**
 * Render a semicircle BMI gauge using SVG.
 */
function renderBMIGauge(containerId, bmi, category) {
  const container = document.getElementById(containerId);
  if (!container) return;

  const catInfo = category || getBMICategory(bmi);
  // Map BMI (10–45) to angle (0–180)
  const clampedBmi = Math.max(10, Math.min(45, bmi));
  const angle = ((clampedBmi - 10) / 35) * 180;

  container.innerHTML = `
    <svg viewBox="0 0 200 110" class="bmi-gauge">
      <defs>
        <linearGradient id="gaugeGrad" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" style="stop-color:#f0ad4e"/>
          <stop offset="35%" style="stop-color:#00d68f"/>
          <stop offset="65%" style="stop-color:#ff6b35"/>
          <stop offset="100%" style="stop-color:#ff4757"/>
        </linearGradient>
      </defs>
      <!-- Track -->
      <path d="M 20 100 A 80 80 0 0 1 180 100" fill="none" stroke="rgba(255,255,255,0.08)" stroke-width="10" stroke-linecap="round"/>
      <!-- Colored arc -->
      <path d="M 20 100 A 80 80 0 0 1 180 100" fill="none" stroke="url(#gaugeGrad)" stroke-width="10" stroke-linecap="round"/>
      <!-- Needle -->
      <line x1="100" y1="100" x2="${100 + 65 * Math.cos((Math.PI * (180 - angle)) / 180)}" y2="${100 - 65 * Math.sin((Math.PI * (180 - angle)) / 180)}" stroke="${catInfo.color}" stroke-width="2.5" stroke-linecap="round"/>
      <circle cx="100" cy="100" r="5" fill="${catInfo.color}"/>
    </svg>
    <div class="bmi-value-display" style="color:${catInfo.color}">${bmi}</div>
    <span class="bmi-category" style="background:${catInfo.color}20; color:${catInfo.color}">${catInfo.label}</span>
  `;
}
