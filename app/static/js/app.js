
// FreightIQ — Client Decision & Analytics Engine
let forecastChartInstance = null;
let currentOptimizationData = null;
let presetScenarios = [];
let operationalNotifications = [];
let currentUserProfile = null;

// Initialize on DOM ready
document.addEventListener("DOMContentLoaded", async () => {
    lucide.createIcons();
    initSliders();
    initOptimizer();
    
    // Parallel data preloading
    await Promise.allSettled([
        loadPresetScenarios(),
        loadNotifications(),
        switchUserRole("cpo"),
        initPortsHandbook()
    ]);

    // Initial background optimization run
    runOptimization(false);

    // Global listener for closing floating dropdowns
    document.addEventListener("click", (e) => {
        if (!e.target.closest("#btn-scenarios-dropdown") && !e.target.closest("#scenarios-menu")) {
            document.getElementById("scenarios-menu")?.classList.add("hidden");
        }
        if (!e.target.closest("#btn-notifications") && !e.target.closest("#notifications-panel")) {
            document.getElementById("notifications-panel")?.classList.add("hidden");
        }
        if (!e.target.closest("#btn-user-profile") && !e.target.closest("#user-menu")) {
            document.getElementById("user-menu")?.classList.add("hidden");
        }
    });
});

// Tab Navigation
function navigateToTab(tabId) {
    const tabs = ["landing", "optimizer", "market", "backtest", "ports"];
    tabs.forEach(t => {
        const viewEl = document.getElementById(`view-${t}`);
        const navBtn = document.getElementById(`nav-${t}`);
        if (t === tabId) {
            viewEl?.classList.remove("hidden");
            navBtn?.classList.add("active");
        } else {
            viewEl?.classList.add("hidden");
            navBtn?.classList.remove("active");
        }
    });

    if (tabId === "backtest") {
        loadBacktestData();
    }
    window.scrollTo({ top: 0, behavior: "smooth" });
    lucide.createIcons();
}

// Dropdown Toggler
function toggleDropdown(id) {
    const el = document.getElementById(id);
    if (!el) return;
    const isHidden = el.classList.contains("hidden");
    
    // Hide other active menus
    ["scenarios-menu", "notifications-panel", "user-menu"].forEach(other => {
        if (other !== id) document.getElementById(other)?.classList.add("hidden");
    });

    if (isHidden) {
        el.classList.remove("hidden");
    } else {
        el.classList.add("hidden");
    }
}

// Toast Notifications
function showToast(message, type = "info") {
    const container = document.getElementById("toast-container");
    if (!container) return;

    const toast = document.createElement("div");
    const bgMap = {
        success: "bg-emerald-950/90 border-emerald-500/50 text-emerald-300 shadow-emerald-500/10",
        warning: "bg-amber-950/90 border-amber-500/50 text-amber-300 shadow-amber-500/10",
        error: "bg-rose-950/90 border-rose-500/50 text-rose-300 shadow-rose-500/10",
        info: "bg-slate-900/90 border-cyan-500/40 text-cyan-200 shadow-cyan-500/10"
    };

    const iconMap = {
        success: "check-circle",
        warning: "alert-triangle",
        error: "alert-circle",
        info: "info"
    };

    toast.className = `pointer-events-auto flex items-center space-x-2.5 px-4 py-3 rounded-xl border backdrop-blur-xl ${bgMap[type] || bgMap.info} shadow-xl text-xs font-semibold transform transition-all duration-300 translate-y-2 opacity-0`;
    toast.innerHTML = `<i data-lucide="${iconMap[type] || 'info'}" class="w-4 h-4 shrink-0"></i><span>${message}</span>`;
    
    container.appendChild(toast);
    lucide.createIcons();

    setTimeout(() => {
        toast.classList.remove("translate-y-2", "opacity-0");
    }, 10);

    setTimeout(() => {
        toast.classList.add("opacity-0", "translate-y-2");
        setTimeout(() => toast.remove(), 300);
    }, 3500);
}

// Load Demo Scenarios
async function loadPresetScenarios() {
    try {
        const res = await fetch("/api/v1/scenarios");
        presetScenarios = await res.json();
        const listEl = document.getElementById("scenarios-list");
        if (!listEl) return;
        listEl.innerHTML = "";

        presetScenarios.forEach(sc => {
            const btn = document.createElement("button");
            btn.className = "w-full text-left p-2.5 rounded-xl hover:bg-slate-800/80 flex flex-col space-y-0.5 transition-colors cursor-pointer border border-transparent hover:border-slate-700";
            btn.onclick = () => {
                loadScenario(sc.id);
                toggleDropdown("scenarios-menu");
            };
            btn.innerHTML = `
                <div class="flex items-center justify-between">
                    <span class="font-bold text-xs text-white">${sc.title}</span>
                    <span class="badge-pill badge-${sc.badge_color === 'amber' ? 'amber' : sc.badge_color === 'emerald' ? 'emerald' : 'cyan'} text-[9px]">${sc.tag}</span>
                </div>
                <span class="text-[10px] text-slate-400 leading-tight">${sc.subtitle}</span>
            `;
            listEl.appendChild(btn);
        });
    } catch (err) {
        console.error("Failed loading scenarios:", err);
    }
}

// Load Scenario into UI
function loadScenario(scenarioId) {
    const sc = presetScenarios.find(s => s.id === scenarioId);
    if (!sc) return;

    const r = sc.request;
    document.getElementById("inp-commodity").value = r.commodity;
    document.getElementById("inp-tonnage-slider").value = r.parcel_tonnage_mt;
    document.getElementById("tonnage-display").textContent = `${r.parcel_tonnage_mt.toLocaleString()} MT`;
    document.getElementById("inp-origin").value = r.origin_port_id;
    document.getElementById("inp-dest").value = r.dest_port_id;
    document.getElementById("inp-laycan").value = r.laycan_days_ahead;
    document.getElementById("laycan-display").textContent = `${r.laycan_days_ahead} Days Ahead`;
    document.getElementById("inp-holding-cost").value = r.holding_cost_usd_per_day;
    document.getElementById("inp-risk-strategy").value = r.risk_tolerance;

    navigateToTab("optimizer");
    runOptimization(true);
    showToast(`Loaded Preset: ${sc.title}`, "success");
}

// Notifications Feed
async function loadNotifications() {
    try {
        const res = await fetch("/api/v1/notifications");
        operationalNotifications = await res.json();
        const listEl = document.getElementById("notifications-list");
        if (!listEl) return;
        listEl.innerHTML = "";

        operationalNotifications.forEach(n => {
            const item = document.createElement("div");
            item.className = "p-2.5 hover:bg-slate-800/60 rounded-xl text-xs space-y-1 transition-colors";
            const icon = n.type === "alert" ? "alert-circle" : n.type === "warning" ? "alert-triangle" : "info";
            const iconColor = n.type === "alert" ? "text-amber-400" : n.type === "warning" ? "text-rose-400" : "text-cyan-400";
            item.innerHTML = `
                <div class="flex items-center justify-between">
                    <span class="font-bold text-white flex items-center space-x-1.5">
                        <i data-lucide="${icon}" class="w-3.5 h-3.5 ${iconColor}"></i>
                        <span>${n.title}</span>
                    </span>
                    <span class="text-[10px] text-slate-500 mono">${n.time}</span>
                </div>
                <p class="text-[11px] text-slate-400 leading-tight">${n.message}</p>
            `;
            listEl.appendChild(item);
        });
        lucide.createIcons();
    } catch (err) {
        console.error("Notifications fetch error:", err);
    }
}

function markAllNotificationsRead() {
    const badge = document.getElementById("notif-badge");
    if (badge) badge.style.display = "none";
    showToast("Operational signals marked as read", "info");
}

// Switch User Role
async function switchUserRole(roleKey) {
    try {
        const res = await fetch(`/api/v1/profile?role=${roleKey}`);
        currentUserProfile = await res.json();
        
        document.getElementById("user-avatar").textContent = currentUserProfile.avatar_badge;
        document.getElementById("user-display-name").textContent = currentUserProfile.name;
        document.getElementById("user-role-name").textContent = currentUserProfile.title.split(" ")[0] + ", SAIL";
        document.getElementById("menu-user-name").textContent = currentUserProfile.name;
        document.getElementById("menu-user-title").textContent = currentUserProfile.title;
        
        toggleDropdown("user-menu");
        showToast(`Role Switched: ${currentUserProfile.role}`, "info");
    } catch (err) {
        console.error("Role switch error:", err);
    }
}

// Sliders Initialization
function initSliders() {
    const tonnageSlider = document.getElementById("inp-tonnage-slider");
    const tonnageDisplay = document.getElementById("tonnage-display");
    tonnageSlider?.addEventListener("input", (e) => {
        const val = parseInt(e.target.value);
        tonnageDisplay.textContent = `${val.toLocaleString()} MT`;
    });

    const laycanSlider = document.getElementById("inp-laycan");
    const laycanDisplay = document.getElementById("laycan-display");
    laycanSlider?.addEventListener("input", (e) => {
        laycanDisplay.textContent = `${e.target.value} Days Ahead`;
    });
}

// Optimizer Form Handler
function initOptimizer() {
    const form = document.getElementById("optimizer-form");
    form?.addEventListener("submit", (e) => {
        e.preventDefault();
        runOptimization(true);
    });
}

// Run Optimization API
async function runOptimization(showToastNotification = false) {
    const tonnage = parseFloat(document.getElementById("inp-tonnage-slider").value);
    const commodity = document.getElementById("inp-commodity").value;
    const origin = document.getElementById("inp-origin").value;
    const dest = document.getElementById("inp-dest").value;
    const laycan = parseInt(document.getElementById("inp-laycan").value);
    const holdingCost = parseFloat(document.getElementById("inp-holding-cost").value || 2500.0);
    const risk = document.getElementById("inp-risk-strategy").value;

    const payload = {
        parcel_tonnage_mt: tonnage,
        commodity: commodity,
        origin_port_id: origin,
        dest_port_id: dest,
        laycan_days_ahead: laycan,
        risk_tolerance: risk,
        holding_cost_usd_per_day: holdingCost
    };

    try {
        const response = await fetch("/api/v1/optimize", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        
        if (!response.ok) throw new Error(`API error: ${response.statusText}`);

        const data = await response.json();
        currentOptimizationData = data;
        renderOptimizationResults(data);
        if (showToastNotification) {
            showToast(`Optimization complete: ${data.recommendation} decision generated`, "success");
        }
    } catch (err) {
        console.error("Optimization failed:", err);
        showToast("Optimization calculation failed", "error");
    }
}

// Render Optimization Results
function renderOptimizationResults(data) {
    const isWait = data.recommendation === "WAIT";
    const banner = document.getElementById("decision-banner");
    const tag = document.getElementById("decision-action-tag");
    const headline = document.getElementById("decision-headline");
    const savingsUsd = document.getElementById("decision-savings-usd");
    const savingsPct = document.getElementById("decision-savings-pct");
    const summary = document.getElementById("decision-summary-text");
    const conf = document.getElementById("decision-confidence");
    const iconBadge = document.getElementById("decision-icon-badge");

    if (isWait) {
        banner.className = "glass-panel p-5 border-emerald-500/40 bg-gradient-to-r from-emerald-950/40 via-slate-900/80 to-slate-900/80 shadow-2xl";
        tag.className = "badge-pill badge-emerald";
        tag.textContent = "WAIT TO BOOK";
        headline.textContent = `Recommended Booking: Day ${data.optimal_booking_day_offset} (${data.optimal_booking_date})`;
        savingsUsd.className = "mono text-xl font-black text-emerald-400";
        savingsUsd.textContent = `$${data.expected_savings_usd.toLocaleString()} USD`;
        savingsPct.textContent = `(${data.expected_savings_pct.toFixed(1)}% freight reduction)`;
        conf.className = "text-xs text-emerald-400 font-semibold mono";
        conf.textContent = `Confidence: ${data.confidence_pct}%`;
        iconBadge.className = "w-12 h-12 rounded-xl bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center text-emerald-400 shadow-lg shadow-emerald-500/10";
        iconBadge.innerHTML = '<i data-lucide="clock" class="w-6 h-6"></i>';
    } else {
        banner.className = "glass-panel p-5 border-cyan-500/40 bg-gradient-to-r from-cyan-950/40 via-slate-900/80 to-slate-900/80 shadow-2xl";
        tag.className = "badge-pill badge-cyan";
        tag.textContent = "BOOK NOW";
        headline.textContent = `Lock in Spot Charter Today ($${data.current_spot_rate_usd_t.toFixed(2)}/MT)`;
        savingsUsd.className = "mono text-xl font-black text-cyan-400";
        savingsUsd.textContent = "Protected";
        savingsPct.textContent = "(Upward pressure mitigated)";
        conf.className = "text-xs text-cyan-400 font-semibold mono";
        conf.textContent = `Confidence: ${data.confidence_pct}%`;
        iconBadge.className = "w-12 h-12 rounded-xl bg-cyan-500/20 border border-cyan-500/40 flex items-center justify-center text-cyan-400 shadow-lg shadow-cyan-500/10";
        iconBadge.innerHTML = '<i data-lucide="check-circle-2" class="w-6 h-6"></i>';
    }
    summary.textContent = data.decision_summary;

    document.getElementById("recommended-vessel-badge").textContent = data.recommended_vessel_class;

    // Vessel Matches List
    const vesselList = document.getElementById("vessel-list");
    vesselList.innerHTML = "";
    data.all_vessel_matches.forEach(v => {
        const isRec = v.vessel_class === data.recommended_vessel_class;
        const row = document.createElement("div");
        row.className = `p-2.5 rounded-xl border ${v.is_suitable ? (isRec ? 'bg-cyan-950/40 border-cyan-500/50 shadow-sm shadow-cyan-500/10' : 'bg-slate-900/80 border-slate-800') : 'bg-rose-950/20 border-rose-900/40 opacity-70'} flex flex-col space-y-1`;
        row.innerHTML = `
            <div class="flex items-center justify-between">
                <div class="flex items-center space-x-2">
                    <span class="font-bold text-white text-xs">${v.vessel_class}</span>
                    <span class="badge-pill ${v.is_suitable ? 'badge-emerald' : 'badge-rose'} text-[9px]">
                        ${v.is_suitable ? 'PASS' : 'RESTRICTED'}
                    </span>
                    ${isRec ? '<span class="badge-pill badge-amber text-[9px]">OPTIMAL FIT</span>' : ''}
                </div>
                <span class="text-slate-400 text-[10px] mono">Arrival Draft: <b class="text-slate-200">${v.estimated_arrival_draft_m}m</b> / Limit ${v.port_max_draft_m}m</span>
            </div>
            ${v.disqualification_reasons.length > 0 ? `<p class="text-[10px] text-rose-400 leading-tight">&bull; ${v.disqualification_reasons.join(', ')}</p>` : ''}
            ${v.transshipment_recommendation ? `<p class="text-[10px] text-amber-300 leading-tight">&bull; ${v.transshipment_recommendation}</p>` : ''}
        `;
        vesselList.appendChild(row);
    });

    // Voyage Economics
    const eco = data.voyage_breakdown;
    document.getElementById("eco-duration").textContent = `${eco.steaming_days} Sea + ${(eco.loading_days + eco.discharge_days + eco.port_waiting_days).toFixed(1)} Port Days`;
    document.getElementById("eco-bunker").textContent = `${eco.bunker_vlsfo_mt.toLocaleString()} MT ($${eco.bunker_fuel_cost_usd.toLocaleString()})`;
    document.getElementById("eco-charter").textContent = `$${eco.vessel_charter_cost_usd.toLocaleString()}`;
    document.getElementById("eco-dues").textContent = `$${(eco.port_dues_usd + eco.canal_dues_usd + eco.lighterage_cost_usd).toLocaleString()}`;
    document.getElementById("eco-freight-rate").textContent = `$${data.current_spot_rate_usd_t.toFixed(2)} / MT`;

    // Weather / Congestion Risks
    const r = data.risk_assessment;
    const monsoonEl = document.getElementById("risk-monsoon");
    if (r.monsoon_impact_flag) {
        monsoonEl.className = "p-1.5 rounded-lg bg-amber-950/40 text-amber-300 border border-amber-500/40 flex items-center space-x-1.5";
        monsoonEl.innerHTML = '<i data-lucide="alert-triangle" class="w-3.5 h-3.5 text-amber-400"></i><span>Monsoon Active</span>';
    } else {
        monsoonEl.className = "p-1.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-300 flex items-center space-x-1.5";
        monsoonEl.innerHTML = '<i data-lucide="cloud-sun" class="w-3.5 h-3.5 text-emerald-400"></i><span>Monsoon: Clear</span>';
    }

    renderForecastChart(data);
    lucide.createIcons();
}

// Render Luminous Chart.js
function renderForecastChart(data) {
    const ctx = document.getElementById("forecastChart")?.getContext("2d");
    if (!ctx) return;
    
    const labels = ["Spot Today"];
    const forecastSeries = [data.current_spot_rate_usd_t];
    const upper80Series = [data.current_spot_rate_usd_t];
    const lower80Series = [data.current_spot_rate_usd_t];

    data.forecast_curve.forEach((pt) => {
        labels.push(`Day ${pt.day_offset}`);
        forecastSeries.push(pt.predicted_rate_usd_t);
        upper80Series.push(pt.upper_80_pct);
        lower80Series.push(pt.lower_80_pct);
    });

    if (forecastChartInstance) {
        forecastChartInstance.destroy();
    }

    // Gradient fill for main curve
    const gradient = ctx.createLinearGradient(0, 0, 0, 250);
    gradient.addColorStop(0, 'rgba(245, 158, 11, 0.25)');
    gradient.addColorStop(1, 'rgba(245, 158, 11, 0.0)');

    forecastChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Predicted Rate ($/MT)',
                    data: forecastSeries,
                    borderColor: '#f59e0b',
                    borderWidth: 3,
                    pointBackgroundColor: (context) => context.dataIndex === data.optimal_booking_day_offset ? '#10b981' : '#f59e0b',
                    pointBorderColor: '#060913',
                    pointBorderWidth: 2,
                    pointRadius: (context) => context.dataIndex === data.optimal_booking_day_offset ? 7 : 3,
                    pointHoverRadius: 8,
                    tension: 0.3,
                    fill: true,
                    backgroundColor: gradient,
                    zIndex: 10
                },
                {
                    label: 'Upper 80% CI',
                    data: upper80Series,
                    borderColor: 'rgba(245, 158, 11, 0.25)',
                    borderWidth: 1.5,
                    borderDash: [4, 4],
                    pointRadius: 0,
                    fill: '+1',
                    backgroundColor: 'rgba(245, 158, 11, 0.06)',
                    tension: 0.3
                },
                {
                    label: 'Lower 80% CI',
                    data: lower80Series,
                    borderColor: 'rgba(245, 158, 11, 0.25)',
                    borderWidth: 1.5,
                    borderDash: [4, 4],
                    pointRadius: 0,
                    fill: false,
                    tension: 0.3
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { intersect: false, mode: 'index' },
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: 'rgba(10, 15, 29, 0.95)',
                    titleColor: '#ffffff',
                    bodyColor: '#cbd5e1',
                    borderColor: 'rgba(56, 189, 248, 0.3)',
                    borderWidth: 1,
                    padding: 10,
                    cornerRadius: 8,
                    titleFont: { family: 'JetBrains Mono', size: 11 },
                    bodyFont: { family: 'Plus Jakarta Sans', size: 11 },
                    callbacks: {
                        label: (c) => ` ${c.dataset.label}: $${c.raw?.toFixed(2) || 'N/A'}`
                    }
                }
            },
            scales: {
                x: { 
                    grid: { color: 'rgba(51, 65, 85, 0.2)' }, 
                    ticks: { color: '#94a3b8', font: { family: 'JetBrains Mono', size: 10 } } 
                },
                y: { 
                    grid: { color: 'rgba(51, 65, 85, 0.2)' }, 
                    ticks: { color: '#94a3b8', font: { family: 'JetBrains Mono', size: 10 }, callback: (val) => `$${val}` } 
                }
            }
        }
    });
}

// Backtest Data Loader
async function loadBacktestData() {
    try {
        const response = await fetch("/api/v1/backtest?period_days=365&origin_port_id=AUHPT&dest_port_id=INPRT&parcel_size_mt=75000", {
            method: "POST"
        });
        const data = await response.json();
        
        document.getElementById("bt-spend-naive").textContent = `$${data.total_freight_spend_naive_usd.toLocaleString()}`;
        document.getElementById("bt-spend-model").textContent = `$${data.total_freight_spend_model_usd.toLocaleString()}`;
        document.getElementById("bt-total-savings").textContent = `$${data.total_savings_usd.toLocaleString()}`;
        document.getElementById("bt-savings-pct").textContent = `${data.savings_percentage.toFixed(2)}% net reduction`;
        document.getElementById("bt-win-rate").textContent = `${data.profitable_decisions_pct.toFixed(1)}%`;

        const tableBody = document.getElementById("backtest-table-body");
        tableBody.innerHTML = "";
        data.trades.forEach(t => {
            const tr = document.createElement("tr");
            tr.className = "hover:bg-slate-800/40 transition-colors";
            tr.innerHTML = `
                <td class="py-2.5 px-3 font-semibold text-slate-400">${t.trade_id}</td>
                <td class="py-2.5 px-3 text-slate-200">${t.date}</td>
                <td class="py-2.5 px-3 text-slate-300 font-sans">${t.route} (${t.vessel_class})</td>
                <td class="py-2.5 px-3">$${t.spot_rate_usd_t.toFixed(2)}</td>
                <td class="py-2.5 px-3"><span class="badge-pill ${t.model_action === 'WAIT' ? 'badge-amber' : 'badge-cyan'} text-[9px]">${t.model_action}</span></td>
                <td class="py-2.5 px-3 text-emerald-400 font-bold">$${t.actual_booked_rate_usd_t.toFixed(2)}</td>
                <td class="py-2.5 px-3 font-semibold ${t.savings_usd >= 0 ? 'text-emerald-400' : 'text-rose-400'}">${t.savings_usd >= 0 ? '+' : ''}$${t.savings_usd.toLocaleString()}</td>
                <td class="py-2.5 px-3"><span class="badge-pill ${t.was_profitable ? 'badge-emerald' : 'badge-slate'} text-[9px]">${t.was_profitable ? 'PROFIT' : 'NEUTRAL'}</span></td>
            `;
            tableBody.appendChild(tr);
        });
        showToast("Historical Backtest simulation synchronized", "info");
    } catch (err) {
        console.error("Backtest load error:", err);
    }
}

// Ports Registry Loader
async function initPortsHandbook() {
    try {
        const response = await fetch("/api/v1/ports/indian");
        const ports = await response.json();
        const tableBody = document.getElementById("ports-table-body");
        if (!tableBody) return;
        tableBody.innerHTML = "";
        ports.forEach(p => {
            const tr = document.createElement("tr");
            tr.className = "hover:bg-slate-800/40 transition-colors";
            tr.innerHTML = `
                <td class="py-3 px-3 font-bold text-white">${p.name} <span class="text-[10px] text-slate-400 block font-normal">${p.state_or_country}</span></td>
                <td class="py-3 px-3 font-semibold text-amber-400 mono">${p.max_draft_m} m</td>
                <td class="py-3 px-3 text-slate-300 mono">${p.max_loa_m} m</td>
                <td class="py-3 px-3 text-slate-300 mono">${p.max_beam_m} m</td>
                <td class="py-3 px-3 font-semibold text-cyan-300">${p.allowed_vessel_classes[p.allowed_vessel_classes.length - 1]}</td>
                <td class="py-3 px-3 text-slate-200 mono">${p.handling_rate_tpd.toLocaleString()} TPD</td>
                <td class="py-3 px-3"><span class="badge-pill ${p.lighterage_required ? 'badge-rose' : 'badge-emerald'} text-[9px]">${p.lighterage_required ? 'YES (Sandheads)' : 'NO (Direct)'}</span></td>
                <td class="py-3 px-3 text-slate-400 text-[11px]">${p.notes || 'Direct Rail link'}</td>
            `;
            tableBody.appendChild(tr);
        });
    } catch (err) {
        console.error("Ports handbook error:", err);
    }
}

// Board Approval Memo Handlers
function openProcurementMemo() {
    if (!currentOptimizationData) return;
    const d = currentOptimizationData;
    const isWait = d.recommendation === "WAIT";
    
    document.getElementById("memo-date").textContent = new Date().toLocaleString('en-IN', { timeZone: 'Asia/Kolkata' }) + ' IST';
    document.getElementById("memo-officer").textContent = currentUserProfile ? `${currentUserProfile.name} (${currentUserProfile.role})` : "Devendra Tyagi (CPO)";
    
    const badge = document.getElementById("memo-decision-badge");
    badge.className = isWait ? "badge-pill badge-emerald" : "badge-pill badge-cyan";
    badge.textContent = d.recommendation === "WAIT" ? `WAIT TO BOOK (DAY ${d.optimal_booking_day_offset})` : "BOOK SPOT CHARTER NOW";

    document.getElementById("memo-rationale").textContent = d.decision_summary;
    document.getElementById("memo-cargo").textContent = `${d.voyage_breakdown.parcel_tonnage_mt || 75000} MT ${document.getElementById("inp-commodity").value}`;
    document.getElementById("memo-vessel").textContent = `${d.recommended_vessel_class} (Arrival Draft: ${d.voyage_breakdown.vessel_class || '13.95m'})`;
    document.getElementById("memo-spot-rate").textContent = `$${d.current_spot_rate_usd_t.toFixed(2)} / MT`;
    document.getElementById("memo-target-rate").textContent = `$${d.target_booking_rate_usd_t.toFixed(2)} / MT`;
    document.getElementById("memo-savings").textContent = `$${d.expected_savings_usd.toLocaleString()} USD (${d.expected_savings_pct.toFixed(1)}% reduction)`;

    document.getElementById("modal-memo").classList.remove("hidden");
    lucide.createIcons();
}

function closeProcurementMemo() {
    document.getElementById("modal-memo").classList.add("hidden");
}

// Global Exports
window.navigateToTab = navigateToTab;
window.toggleDropdown = toggleDropdown;
window.loadScenario = loadScenario;
window.switchUserRole = switchUserRole;
window.runOptimization = runOptimization;
window.loadBacktestData = loadBacktestData;
window.markAllNotificationsRead = markAllNotificationsRead;
window.openProcurementMemo = openProcurementMemo;
window.closeProcurementMemo = closeProcurementMemo;
window.showToast = showToast;
window.initPortsHandbook = initPortsHandbook;
