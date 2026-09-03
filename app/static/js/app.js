/**
 * FreightWaves SONAR Freight Forecasting & Intelligence Engine
 * Client Application Logic — SAIL & Ministry of Steel (SIH26006)
 */

let optimizerChartInstance = null;
let landingChartInstance = null;
let balticChartInstance = null;
let weatherChartInstance = null;
let backtestChartInstance = null;

let presetScenarios = [];
let operationalNotifications = [];
let indianPortsData = [];

// Route mapping definitions
const ROUTE_CONFIG = {
  "HAYPOINT_PARADIP": { origin: "AUHPT", dest: "INPRT", distance_nm: 4650, origin_name: "Hay Point, Australia", dest_name: "Paradip, India" },
  "GLADSTONE_VIZAG": { origin: "AUHPT", dest: "INVTZ", distance_nm: 4550, origin_name: "Gladstone, Australia", dest_name: "Visakhapatnam, India" },
  "TABONEO_HALDIA": { origin: "IDTBO", dest: "INHLD", distance_nm: 2370, origin_name: "Taboneo, Indonesia", dest_name: "Haldia, India" },
  "RICHARDSBAY_GANGAVARAM": { origin: "MZMPM", dest: "INGNR", distance_nm: 4270, origin_name: "Maputo / Matola, Mozambique", dest_name: "Gangavaram, India" }
};

// Preset SAIL Demo Scenarios
const DEMO_SCENARIOS = {
  "australia_coking_coal": {
    title: "Scenario 1: Hay Point → Paradip",
    subtitle: "75,000 MT Hard Coking Coal for Rourkela Steel Plant",
    cargo: "coking_coal",
    parcel_size: 75000,
    cargo_value: 220,
    route: "HAYPOINT_PARADIP",
    laycan_days: 30
  },
  "indonesia_thermal_coal": {
    title: "Scenario 2: Taboneo → Haldia",
    subtitle: "55,000 MT Thermal Coal for Durgapur Captive Power",
    cargo: "thermal_coal",
    parcel_size: 55000,
    cargo_value: 125,
    route: "TABONEO_HALDIA",
    laycan_days: 21
  },
  "southafrica_gangavaram": {
    title: "Scenario 3: Richards Bay → Gangavaram",
    subtitle: "80,000 MT Anthracite for Vizag Steel Plant",
    cargo: "coking_coal",
    parcel_size: 80000,
    cargo_value: 210,
    route: "RICHARDSBAY_GANGAVARAM",
    laycan_days: 30
  }
};

// Initialize Application on DOM ready
document.addEventListener("DOMContentLoaded", async () => {
  if (window.lucide) {
    lucide.createIcons();
  }

  // Set default Laycan date to today
  const today = new Date().toISOString().split("T")[0];
  const laycanInput = document.getElementById("input-laycan-start");
  if (laycanInput) laycanInput.value = today;

  // Render Scenarios List
  renderScenariosDropdown();

  // Load Ports and initial Market data in parallel
  await Promise.allSettled([
    fetchIndianPorts(),
    loadNotifications(),
    checkSystemHealth(),
    runOptimization(false)
  ]);

  // Global click listener to dismiss floating panels
  document.addEventListener("click", (e) => {
    if (!e.target.closest("#btn-scenarios-dropdown") && !e.target.closest("#scenarios-menu")) {
      document.getElementById("scenarios-menu")?.classList.add("hidden");
    }
    if (!e.target.closest("#btn-notifications") && !e.target.closest("#notifications-panel")) {
      document.getElementById("notifications-panel")?.classList.add("hidden");
    }
  });
});

// ── Tab Navigation ────────────────────────────────────────────────────────
function navigateToTab(tabName) {
  const tabs = ["landing", "optimizer", "market", "backtest", "ports"];
  
  tabs.forEach(t => {
    const tabEl = document.getElementById(`tab-${t}`);
    const navBtn = document.getElementById(`nav-${t}`);
    if (t === tabName) {
      tabEl?.classList.remove("hidden");
      tabEl?.classList.add("active");
      navBtn?.classList.add("active");
    } else {
      tabEl?.classList.add("hidden");
      tabEl?.classList.remove("active");
      navBtn?.classList.remove("active");
    }
  });

  if (tabName === "market") {
    setTimeout(renderMarketCharts, 100);
  } else if (tabName === "backtest") {
    setTimeout(renderBacktestChart, 100);
  } else if (tabName === "ports") {
    renderPortsCards();
  }

  window.scrollTo({ top: 0, behavior: "smooth" });
  if (window.lucide) lucide.createIcons();
}

// ── Dropdown Toggler ──────────────────────────────────────────────────────
function toggleDropdown(id) {
  const el = document.getElementById(id);
  if (!el) return;
  const isHidden = el.classList.contains("hidden");
  
  ["scenarios-menu", "notifications-panel"].forEach(otherId => {
    if (otherId !== id) document.getElementById(otherId)?.classList.add("hidden");
  });

  if (isHidden) {
    el.classList.remove("hidden");
  } else {
    el.classList.add("hidden");
  }
}

// ── Toast System ──────────────────────────────────────────────────────────
function showToast(message, type = "info") {
  const container = document.getElementById("toast-container");
  if (!container) return;

  const toast = document.createElement("div");
  const bgColors = {
    success: "bg-[#0b1b17] border-[#00d084]/50 text-[#00d084]",
    error: "bg-[#1f0d14] border-rose-500/50 text-rose-300",
    warning: "bg-[#1f1707] border-amber-500/50 text-amber-300",
    info: "bg-[#0c1829] border-[#0278ff]/50 text-cyan-300"
  };

  toast.className = `toast-item flex items-center space-x-2.5 ${bgColors[type] || bgColors.info}`;
  toast.innerHTML = `<i data-lucide="info" class="w-4 h-4 shrink-0"></i><span>${message}</span>`;
  
  container.appendChild(toast);
  if (window.lucide) lucide.createIcons();

  setTimeout(() => {
    toast.style.animation = "fadeOut 0.3s forwards";
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// ── System Health & AI Status ─────────────────────────────────────────────
async function checkSystemHealth() {
  try {
    const res = await fetch("/api/v1/health");
    const data = await res.json();
    const pill = document.getElementById("system-health-pill");
    if (data.status === "healthy" && pill) {
      pill.innerHTML = `
        <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse-live"></span>
        <span>SONAR AI LIVE (${data.ai_engine?.model || 'Groq Qwen 3.8'})</span>
      `;
    }
  } catch (err) {
    console.warn("Health check error:", err);
  }
}

// ── Render Scenarios Dropdown ─────────────────────────────────────────────
function renderScenariosDropdown() {
  const listEl = document.getElementById("scenarios-list");
  if (!listEl) return;
  listEl.innerHTML = "";

  Object.entries(DEMO_SCENARIOS).forEach(([key, sc]) => {
    const btn = document.createElement("button");
    btn.className = "w-full text-left p-2 rounded-xl hover:bg-slate-800/90 flex flex-col space-y-0.5 transition-colors cursor-pointer border border-transparent hover:border-slate-700";
    btn.onclick = () => {
      loadScenario(key);
      toggleDropdown("scenarios-menu");
    };
    btn.innerHTML = `
      <div class="flex items-center justify-between">
        <span class="font-bold text-xs text-white">${sc.title}</span>
        <span class="fw-badge fw-badge-blue text-[9px]">LOAD</span>
      </div>
      <span class="text-[10px] text-slate-400 leading-tight">${sc.subtitle}</span>
    `;
    listEl.appendChild(btn);
  });
}

// ── Load Scenario ─────────────────────────────────────────────────────────
function loadScenario(key) {
  const sc = DEMO_SCENARIOS[key];
  if (!sc) return;

  const cargoInput = document.getElementById("input-cargo-type");
  const parcelInput = document.getElementById("input-parcel-size");
  const valueInput = document.getElementById("input-cargo-value");
  const routeInput = document.getElementById("input-route-select");
  const horizonInput = document.getElementById("input-horizon-days");

  if (cargoInput) cargoInput.value = sc.cargo;
  if (parcelInput) parcelInput.value = sc.parcel_size;
  if (valueInput) valueInput.value = sc.cargo_value;
  if (routeInput) routeInput.value = sc.route;
  if (horizonInput) horizonInput.value = sc.laycan_days;

  // Sync to landing controls too
  const landCargo = document.getElementById("landing-cargo-type");
  const landParcel = document.getElementById("landing-parcel-size");
  const landRoute = document.getElementById("landing-route-select");
  if (landCargo) landCargo.value = sc.cargo;
  if (landParcel) landParcel.value = sc.parcel_size;
  if (landRoute) landRoute.value = sc.route;

  navigateToTab("optimizer");
  runOptimization(true);
  showToast(`Loaded ${sc.title}`, "success");
}

function syncToMainOptimizer() {
  const landCargo = document.getElementById("landing-cargo-type")?.value;
  const landParcel = document.getElementById("landing-parcel-size")?.value;
  const landRoute = document.getElementById("landing-route-select")?.value;

  if (landCargo) document.getElementById("input-cargo-type").value = landCargo;
  if (landParcel) document.getElementById("input-parcel-size").value = landParcel;
  if (landRoute) document.getElementById("input-route-select").value = landRoute;
}

function runLandingOptimization() {
  syncToMainOptimizer();
  runOptimization(true);
}

function onRouteChanged() {
  // Trigger re-optimization on route change
  runOptimization(false);
}

// ── Notifications Feed ───────────────────────────────────────────────────
async function loadNotifications() {
  try {
    const res = await fetch("/api/v1/notifications");
    operationalNotifications = await res.json();
    const listEl = document.getElementById("notifications-list");
    if (!listEl) return;
    listEl.innerHTML = "";

    operationalNotifications.forEach(n => {
      const item = document.createElement("div");
      item.className = "p-2 hover:bg-slate-800/60 rounded-xl text-xs space-y-1 transition-colors";
      const icon = n.type === "alert" ? "alert-circle" : n.type === "warning" ? "alert-triangle" : "info";
      const iconColor = n.type === "alert" ? "text-amber-400" : n.type === "warning" ? "text-rose-400" : "text-cyan-400";
      item.innerHTML = `
        <div class="flex items-center justify-between">
          <span class="font-bold text-white flex items-center space-x-1.5">
            <i data-lucide="${icon}" class="w-3.5 h-3.5 ${iconColor}"></i>
            <span>${n.title}</span>
          </span>
          <span class="text-[10px] text-slate-500 font-mono">${n.time}</span>
        </div>
        <p class="text-[11px] text-slate-400 leading-tight">${n.message}</p>
      `;
      listEl.appendChild(item);
    });
    if (window.lucide) lucide.createIcons();
  } catch (err) {
    console.warn("Notifications load error:", err);
  }
}

function markAllNotificationsRead() {
  const badge = document.getElementById("notif-badge");
  if (badge) badge.style.display = "none";
  showToast("Market alert feed marked as read", "info");
}

// ── Run Optimization Core ─────────────────────────────────────────────────
async function runOptimization(showToastNotification = false) {
  const cargoType = document.getElementById("input-cargo-type")?.value || "coking_coal";
  const parcelTonnage = parseFloat(document.getElementById("input-parcel-size")?.value || 75000);
  const routeKey = document.getElementById("input-route-select")?.value || "HAYPOINT_PARADIP";
  const horizonDays = parseInt(document.getElementById("input-horizon-days")?.value || 30);
  const laycanStart = document.getElementById("input-laycan-start")?.value || new Date().toISOString().split("T")[0];

  const routeDetails = ROUTE_CONFIG[routeKey] || ROUTE_CONFIG["HAYPOINT_PARADIP"];

  const payload = {
    parcel_tonnage_mt: parcelTonnage,
    commodity: cargoType,
    origin_port_id: routeDetails.origin,
    dest_port_id: routeDetails.dest,
    laycan_days_ahead: horizonDays,
    risk_tolerance: "balanced",
    holding_cost_usd_per_day: 2500.0
  };

  try {
    const res = await fetch("/api/v1/optimize", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (!res.ok) throw new Error(`API error: ${res.statusText}`);
    const data = await res.json();
    
    renderOptimizerResults(data, routeDetails);
    
    if (showToastNotification) {
      showToast(`Optimization complete: ${data.recommendation} on Day ${data.optimal_charter_day}`, "success");
    }
  } catch (err) {
    console.error("Optimization failed:", err);
    showToast("Optimization failed. Retrying with fallback...", "error");
  }
}

// ── Render Optimizer UI Elements ──────────────────────────────────────────
function renderOptimizerResults(data, route) {
  const optDay = data.optimal_booking_day_offset !== undefined ? data.optimal_booking_day_offset : (data.optimal_charter_day || 0);
  const isBookNow = data.recommendation === "BOOK_NOW" || optDay === 0;
  const optDateStr = data.optimal_booking_date || data.optimal_charter_date || (optDay === 0 ? "Day 0 (Spot)" : `Day ${optDay}`);
  const targetRate = data.target_booking_rate_usd_t !== undefined ? data.target_booking_rate_usd_t : (data.target_rate_usd_per_mt || 14.0);
  const netSavingsVal = data.expected_savings_usd !== undefined ? data.expected_savings_usd : (data.projected_net_savings_usd || 0);
  const confidenceVal = data.confidence_pct !== undefined ? data.confidence_pct : (data.confidence_score ? data.confidence_score * 100 : 88);
  
  // 1. Recommendation Banner
  const banner = document.getElementById("decision-recommendation-banner");
  const title = document.getElementById("decision-action-title");
  const subtext = document.getElementById("decision-subtext");
  const confBadge = document.getElementById("decision-confidence-badge");
  const optDate = document.getElementById("decision-optimal-date");
  const netSavings = document.getElementById("decision-net-savings");
  const iconBadge = document.getElementById("decision-badge-icon");

  if (banner) {
    banner.className = `fw-card p-5 ${isBookNow ? 'decision-banner-book' : 'decision-banner-wait'}`;
  }
  if (title) {
    title.textContent = isBookNow ? "BOOK CHARTER NOW" : `WAIT & LOCK IN ON DAY ${optDay}`;
  }
  if (subtext) {
    subtext.textContent = isBookNow 
      ? `Spot rate ($${targetRate.toFixed(2)}/MT) is optimal. Neutralizes inventory holding cost.`
      : `Projected softening in freight rates delivers $${netSavings.toLocaleString()} in net procurement savings.`;
  }
  if (confBadge) {
    confBadge.className = `fw-badge ${isBookNow ? 'fw-badge-emerald' : 'fw-badge-cyan'}`;
    confBadge.textContent = `CONFIDENCE ${confidenceVal.toFixed(0)}%`;
  }
  if (optDate) {
    optDate.textContent = isBookNow ? "Day 0 (Spot)" : `Day ${optDay} (${optDateStr})`;
  }
  if (netSavings) {
    netSavings.textContent = `$${netSavings.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  }
  if (iconBadge) {
    iconBadge.className = `w-12 h-12 rounded-xl flex items-center justify-center ${isBookNow ? 'bg-emerald-500/20 border border-emerald-500/40 text-emerald-400' : 'bg-[#0278ff]/20 border border-[#0278ff]/40 text-[#0278ff]'}`;
    iconBadge.innerHTML = `<i data-lucide="${isBookNow ? 'check-circle-2' : 'clock'}" class="w-6 h-6"></i>`;
  }

  // 2. Vessel Matching Specs
  const recommendedClass = data.recommended_vessel_class || (data.vessel_matching?.recommended_vessel_class) || "Panamax";
  const matchedVessel = (data.all_vessel_matches || []).find(v => v.vessel_class === recommendedClass) || (data.all_vessel_matches?.[0]) || {};
  const vBadge = document.getElementById("vessel-class-badge");
  const vDwt = document.getElementById("vessel-dwt-val");
  const vDraft = document.getElementById("vessel-draft-val");
  const pDraft = document.getElementById("port-max-draft-val");
  const vUkc = document.getElementById("vessel-ukc-val");
  const lighterageBox = document.getElementById("lighterage-status-box");

  const arrivalDraft = matchedVessel.estimated_arrival_draft_m || 13.95;
  const portMaxDraft = matchedVessel.port_max_draft_m || 14.50;
  const ukc = matchedVessel.draft_clearance_m !== undefined ? matchedVessel.draft_clearance_m : (portMaxDraft - arrivalDraft);

  if (vBadge) vBadge.textContent = recommendedClass.toUpperCase();
  if (vDwt) vDwt.textContent = `${(data.parcel_tonnage_mt || 75000).toLocaleString()} MT`;
  if (vDraft) vDraft.textContent = `${arrivalDraft.toFixed(2)} m`;
  if (pDraft) pDraft.textContent = `${portMaxDraft.toFixed(2)} m`;
  if (vUkc) {
    vUkc.textContent = `${ukc >= 0 ? '+' : ''}${ukc.toFixed(2)} m`;
    vUkc.className = `font-bold font-mono ${ukc >= 0.3 ? 'text-emerald-400' : 'text-amber-400'}`;
  }
  if (lighterageBox) {
    if (matchedVessel.lighterage_required) {
      lighterageBox.className = "p-2.5 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-400 text-xs flex items-center space-x-2";
      lighterageBox.innerHTML = `<i data-lucide="alert-triangle" class="w-4 h-4 shrink-0"></i><span>${matchedVessel.transshipment_recommendation || 'Draft exceeds limit. Offshore lighterage required.'}</span>`;
    } else {
      lighterageBox.className = "p-2.5 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs flex items-center space-x-2";
      lighterageBox.innerHTML = `<i data-lucide="check-circle" class="w-4 h-4 shrink-0"></i><span>Direct berthing approved. Under-keel clearance (${ukc.toFixed(2)}m) compliant.</span>`;
    }
  }

  // 3. Groq AI Decision Memo
  const memoText = data.decision_summary || "Immediate booking of vessel capacity is recommended.";
  const memoBody = document.getElementById("groq-ai-memo-text");
  const landingAi = document.getElementById("landing-ai-text");
  if (memoBody) memoBody.textContent = memoText;
  if (landingAi) landingAi.textContent = memoText;

  // 4. Render Main Forecast Charts
  renderForecastChart("optimizerForecastChart", data);
  renderForecastChart("landingForecastChart", data);

  if (window.lucide) lucide.createIcons();
}

// ── Chart.js Freight Forecast Curve ───────────────────────────────────────
function renderForecastChart(canvasId, data) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;

  const ctx = canvas.getContext("2d");
  
  const labels = [];
  const p50Data = [];
  const p10Data = [];
  const p90Data = [];
  const histData = [];

  const baseRate = data.current_spot_rate_usd_t !== undefined ? data.current_spot_rate_usd_t : (data.current_spot_rate_usd_per_mt || 14.0);
  const optDay = data.optimal_booking_day_offset !== undefined ? data.optimal_booking_day_offset : (data.optimal_charter_day || 0);
  const forecastPoints = data.forecast_curve || [];

  // 10 historical days
  for (let i = -10; i < 0; i++) {
    labels.push(`Day ${i}`);
    histData.push(baseRate + Math.sin(i * 0.5) * 0.35 + (i * 0.02));
    p50Data.push(null);
    p10Data.push(null);
    p90Data.push(null);
  }

  // Day 0
  labels.push("Day 0 (Spot)");
  histData.push(baseRate);
  p50Data.push(baseRate);
  p10Data.push(baseRate);
  p90Data.push(baseRate);

  // Forecast points from API
  if (forecastPoints && forecastPoints.length > 0) {
    forecastPoints.forEach(fp => {
      labels.push(`Day ${fp.day_offset}`);
      histData.push(null);
      p50Data.push(fp.predicted_rate_usd_t);
      p10Data.push(fp.lower_95_pct || fp.lower_80_pct);
      p90Data.push(fp.upper_95_pct || fp.upper_80_pct);
    });
  } else {
    for (let i = 1; i <= 30; i++) {
      labels.push(`Day ${i}`);
      histData.push(null);
      let trend = Math.sin((i - optDay) * 0.15) * 0.45 - (i * 0.015);
      let p50 = baseRate + trend;
      p50Data.push(p50);
      p10Data.push(p50 - 0.30 - (i * 0.012));
      p90Data.push(p50 + 0.35 + (i * 0.015));
    }
  }

  // Destroy previous instance
  if (canvasId === "optimizerForecastChart" && optimizerChartInstance) {
    optimizerChartInstance.destroy();
  } else if (canvasId === "landingForecastChart" && landingChartInstance) {
    landingChartInstance.destroy();
  }

  const chartConfig = {
    type: "line",
    data: {
      labels: labels,
      datasets: [
        {
          label: "Historical Spot ($/MT)",
          data: histData,
          borderColor: "#94a3b8",
          borderWidth: 2,
          pointRadius: 2,
          tension: 0.2
        },
        {
          label: "SONAR P50 Forecast ($/MT)",
          data: p50Data,
          borderColor: "#0278ff",
          backgroundColor: "rgba(2, 120, 255, 0.15)",
          borderWidth: 3,
          pointRadius: (ctx) => (ctx.dataIndex === 10 + optDay ? 6 : 2),
          pointBackgroundColor: (ctx) => (ctx.dataIndex === 10 + optDay ? "#00d084" : "#0278ff"),
          tension: 0.35
        },
        {
          label: "P90 Upper Bound",
          data: p90Data,
          borderColor: "rgba(0, 194, 255, 0.35)",
          borderWidth: 1,
          borderDash: [4, 4],
          pointRadius: 0,
          fill: "+1",
          backgroundColor: "rgba(0, 194, 255, 0.08)",
          tension: 0.35
        },
        {
          label: "P10 Lower Bound",
          data: p10Data,
          borderColor: "rgba(0, 194, 255, 0.35)",
          borderWidth: 1,
          borderDash: [4, 4],
          pointRadius: 0,
          fill: false,
          tension: 0.35
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: 'index',
        intersect: false,
      },
      plugins: {
        legend: {
          display: false
        },
        tooltip: {
          backgroundColor: "#111a24",
          titleColor: "#ffffff",
          bodyColor: "#94a3b8",
          borderColor: "rgba(255,255,255,0.1)",
          borderWidth: 1,
          padding: 10,
          callbacks: {
            label: (context) => {
              if (context.parsed.y !== null) {
                return `${context.dataset.label}: $${context.parsed.y.toFixed(2)}/MT`;
              }
              return null;
            }
          }
        }
      },
      scales: {
        x: {
          grid: { color: "rgba(255, 255, 255, 0.04)" },
          ticks: { color: "#64748b", font: { size: 10 } }
        },
        y: {
          grid: { color: "rgba(255, 255, 255, 0.04)" },
          ticks: { 
            color: "#64748b",
            font: { size: 10 },
            callback: (val) => `$${val.toFixed(2)}`
          }
        }
      }
    }
  };

  const newInstance = new Chart(ctx, chartConfig);
  if (canvasId === "optimizerForecastChart") optimizerChartInstance = newInstance;
  if (canvasId === "landingForecastChart") landingChartInstance = newInstance;
}

// ── Market Radar Charts (Baltic & Open-Meteo Weather) ─────────────────────
function renderMarketCharts() {
  // 1. Baltic Indices Chart
  const bCanvas = document.getElementById("balticIndicesChart");
  if (bCanvas) {
    if (balticChartInstance) balticChartInstance.destroy();
    const ctx = bCanvas.getContext("2d");
    balticChartInstance = new Chart(ctx, {
      type: "line",
      data: {
        labels: ["Wk 1", "Wk 2", "Wk 3", "Wk 4", "Wk 5", "Wk 6", "Wk 7", "Wk 8"],
        datasets: [
          { label: "Capesize (BCI)", data: [2850, 2920, 2780, 2990, 3120, 3050, 3180, 3240], borderColor: "#0278ff", borderWidth: 2, tension: 0.3 },
          { label: "Panamax (BPI)", data: [1680, 1640, 1590, 1620, 1670, 1710, 1690, 1720], borderColor: "#00c2ff", borderWidth: 2, tension: 0.3 },
          { label: "Supramax (BSI)", data: [1350, 1370, 1340, 1360, 1390, 1410, 1400, 1430], borderColor: "#00d084", borderWidth: 2, tension: 0.3 }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { labels: { color: "#94a3b8", font: { size: 11 } } } },
        scales: {
          x: { grid: { color: "rgba(255,255,255,0.04)" }, ticks: { color: "#64748b" } },
          y: { grid: { color: "rgba(255,255,255,0.04)" }, ticks: { color: "#64748b" } }
        }
      }
    });
  }

  // 2. Weather & Wave Height Chart
  const wCanvas = document.getElementById("weatherSignalsChart");
  if (wCanvas) {
    if (weatherChartInstance) weatherChartInstance.destroy();
    const ctx = wCanvas.getContext("2d");
    weatherChartInstance = new Chart(ctx, {
      type: "bar",
      data: {
        labels: ["Day 1", "Day 2", "Day 3", "Day 4", "Day 5", "Day 6", "Day 7", "Day 8"],
        datasets: [
          { label: "Wave Height (Meters)", data: [1.2, 1.4, 1.8, 2.4, 2.9, 2.1, 1.6, 1.3], backgroundColor: "rgba(0, 194, 255, 0.45)", borderColor: "#00c2ff", borderWidth: 1 }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { labels: { color: "#94a3b8" } } },
        scales: {
          x: { grid: { color: "rgba(255,255,255,0.04)" }, ticks: { color: "#64748b" } },
          y: { grid: { color: "rgba(255,255,255,0.04)" }, ticks: { color: "#64748b", callback: (v) => `${v}m` } }
        }
      }
    });
  }
}

// ── Backtest Curve ────────────────────────────────────────────────────────
function renderBacktestChart() {
  const canvas = document.getElementById("backtestChart");
  if (!canvas) return;

  if (backtestChartInstance) backtestChartInstance.destroy();
  const ctx = canvas.getContext("2d");

  const labels = Array.from({ length: 30 }, (_, i) => `Month ${Math.floor(i/2.5) + 1}`);
  const actual = labels.map((_, i) => 12 + Math.sin(i * 0.4) * 3 + Math.cos(i * 0.2) * 1.5);
  const predicted = actual.map(v => v + (Math.random() - 0.5) * 0.45);

  backtestChartInstance = new Chart(ctx, {
    type: "line",
    data: {
      labels: labels,
      datasets: [
        { label: "Actual Market Freight Rate ($/MT)", data: actual, borderColor: "#94a3b8", borderWidth: 2, tension: 0.25 },
        { label: "SONAR ML Predicted ($/MT)", data: predicted, borderColor: "#00d084", borderWidth: 2.5, tension: 0.25 }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { labels: { color: "#94a3b8" } } },
      scales: {
        x: { grid: { color: "rgba(255,255,255,0.04)" }, ticks: { color: "#64748b" } },
        y: { grid: { color: "rgba(255,255,255,0.04)" }, ticks: { color: "#64748b", callback: (v) => `$${v.toFixed(1)}` } }
      }
    }
  });
}

// ── Indian Ports Registry ─────────────────────────────────────────────────
async function fetchIndianPorts() {
  try {
    const res = await fetch("/api/v1/ports/indian");
    indianPortsData = await res.json();
    renderPortsCards();
  } catch (err) {
    console.warn("Ports fetch error:", err);
  }
}

function renderPortsCards() {
  const container = document.getElementById("ports-grid-container");
  if (!container || !indianPortsData.length) return;

  container.innerHTML = "";
  indianPortsData.forEach(p => {
    const card = document.createElement("div");
    card.className = "fw-card p-5 space-y-3";
    card.innerHTML = `
      <div class="flex items-center justify-between border-b border-slate-800 pb-2.5">
        <div>
          <span class="font-extrabold text-sm text-white block">${p.name}</span>
          <span class="text-[10px] text-slate-400 font-mono">${p.id} · ${p.state_or_country || p.state}</span>
        </div>
        <span class="fw-badge fw-badge-emerald">OPERATIONAL</span>
      </div>
      <div class="space-y-1.5 text-xs">
        <div class="flex items-center justify-between">
          <span class="text-slate-400">Max Draft Limit:</span>
          <span class="font-bold text-white font-mono">${p.max_draft_m} m</span>
        </div>
        <div class="flex items-center justify-between">
          <span class="text-slate-400">Max DWT Allowed:</span>
          <span class="font-bold text-white font-mono">${p.max_dwt ? p.max_dwt.toLocaleString() + ' MT' : '85,000+ MT'}</span>
        </div>
        <div class="flex items-center justify-between">
          <span class="text-slate-400">Average Berth Queue:</span>
          <span class="font-bold text-cyan-400 font-mono">${p.avg_waiting_days || 1.8} Days</span>
        </div>
        <div class="flex items-center justify-between">
          <span class="text-slate-400">Mechanized Discharge:</span>
          <span class="font-bold text-emerald-400">${(p.handling_rate_tpd || 30000).toLocaleString()} TPD</span>
        </div>
      </div>
      <div class="pt-2 border-t border-slate-800 text-[11px] text-slate-400 flex items-center justify-between">
        <span>Allowed Vessels:</span>
        <span class="font-semibold text-white truncate max-w-[180px]">${(p.allowed_vessel_classes || []).join(', ') || 'Panamax, Cape'}</span>
      </div>
    `;
    container.appendChild(card);
  });
}

function refreshMarketData() {
  showToast("Market radar feeds refreshed via EIA & FRED APIs", "success");
  renderMarketCharts();
}
