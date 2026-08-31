
let forecastChartInstance = null;
let currentOptimizationData = null;
let presetScenarios = [];
let operationalNotifications = [];
let currentUserProfile = null;

document.addEventListener("DOMContentLoaded", () => {
    lucide.createIcons();
    initSliders();
    loadPresetScenarios();
    loadNotifications();
    switchUserRole("cpo");
    initPortsHandbook();
    initOptimizer();
    
    // Close dropdowns on outside click
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

    // Run optimization in background for initial state
    runOptimization(false);
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

function toggleDropdown(id) {
    const el = document.getElementById(id);
    if (!el) return;
    const isHidden = el.classList.contains("hidden");
    // Hide others
    ["scenarios-menu", "notifications-panel", "user-menu"].forEach(other => {
        if (other !== id) document.getElementById(other)?.classList.add("hidden");
    });
    if (isHidden) el.classList.remove("hidden");
    else el.classList.add("hidden");
}

function showToast(message, type = "info") {
    const container = document.getElementById("toast-container");
    if (!container) return;

    const toast = document.createElement("div");
    const bg = type === "success" ? "bg-emerald-950 border-emerald-500/60 text-emerald-300" :
               type === "warning" ? "bg-amber-950 border-amber-500/60 text-amber-300" :
               type === "error" ? "bg-rose-950 border-rose-500/60 text-rose-300" :
               "bg-steel-900 border-slate-700 text-slate-200";

    toast.className = `pointer-events-auto flex items-center space-x-2 px-4 py-3 rounded-xl border ${bg} shadow-2xl text-xs font-semibold transform transition-all duration-300 translate-y-2 opacity-0`;
    toast.innerHTML = `<i data-lucide="info" class="w-4 h-4 shrink-0"></i><span>${message}</span>`;
    
    container.appendChild(toast);
    lucide.createIcons();

    setTimeout(() => {
        toast.classList.remove("translate-y-2", "opacity-0");
    }, 10);

    setTimeout(() => {
        toast.classList.add("opacity-0", "translate-y-2");
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

// Presets & Scenarios Management
async function loadPresetScenarios() {
    try {
        const res = await fetch("/api/v1/scenarios");
        presetScenarios = await res.json();
        const listEl = document.getElementById("scenarios-list");
        if (!listEl) return;
        listEl.innerHTML = "";

        presetScenarios.forEach(sc => {
            const btn = document.createElement("button");
            btn.className = "w-full text-left p-2 rounded-lg hover:bg-steel-800 flex flex-col space-y-0.5 transition-colors cursor-pointer";
            btn.onclick = () => {
                loadScenario(sc.id);
                toggleDropdown("scenarios-menu");
            };
            btn.innerHTML = `
                <div class="flex items-center justify-between">
                    <span class="font-bold text-xs text-white">${sc.title}</span>
                    <span class="text-[9px] px-1.5 py-0.2 rounded font-black bg-${sc.badge_color}-500/20 text-${sc.badge_color}-300">${sc.tag}</span>
                </div>
                <span class="text-[10px] text-slate-400 leading-tight">${sc.subtitle}</span>
            `;
            listEl.appendChild(btn);
        });
    } catch (err) {
        console.error("Failed loading scenarios:", err);
    }
}

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
    showToast(`Loaded Scenario: ${sc.title}`, "success");
}

// Notifications
async function loadNotifications() {
    try {
        const res = await fetch("/api/v1/notifications");
        operationalNotifications = await res.json();
        const listEl = document.getElementById("notifications-list");
        if (!listEl) return;
        listEl.innerHTML = "";

        operationalNotifications.forEach(n => {
            const item = document.createElement("div");
            item.className = "p-2 hover:bg-steel-850 rounded-lg text-xs space-y-1";
            const icon = n.type === "alert" ? "alert-circle" : n.type === "warning" ? "alert-triangle" : "info";
            const iconColor = n.type === "alert" ? "text-amber-400" : n.type === "warning" ? "text-rose-400" : "text-brand-400";
            item.innerHTML = `
                <div class="flex items-center justify-between">
                    <span class="font-bold text-white flex items-center space-x-1.5">
                        <i data-lucide="${icon}" class="w-3 h-3 ${iconColor}"></i>
                        <span>${n.title}</span>
                    </span>
                    <span class="text-[10px] text-slate-500">${n.time}</span>
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
    showToast("All operational notifications marked as read", "info");
}

// Role Switcher
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
        showToast(`Switched active view to: ${currentUserProfile.role}`, "info");
    } catch (err) {
        console.error("Role switch error:", err);
    }
}

// Sliders initialization
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

// Optimizer Logic
function initOptimizer() {
    const form = document.getElementById("optimizer-form");
    form?.addEventListener("submit", (e) => {
        e.preventDefault();
        runOptimization(true);
    });
}

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
            showToast(`Optimization complete: ${data.recommendation} call generated`, "success");
        }
    } catch (err) {
        console.error("Optimization failed:", err);
        showToast("Optimization calculation failed", "error");
    }
}

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
        banner.className = "bg-gradient-to-r from-emerald-950/80 via-steel-900 to-steel-900 border border-emerald-500/40 rounded-2xl p-5 shadow-xl";
        tag.className = "px-2.5 py-0.5 rounded-full text-xs font-black bg-emerald-500 text-slate-950 tracking-wider";
        tag.textContent = "WAIT TO BOOK";
        headline.textContent = `Recommended Booking: Day ${data.optimal_booking_day_offset} (${data.optimal_booking_date})`;
        savingsUsd.className = "text-xl font-black text-emerald-400";
        savingsUsd.textContent = `$${data.expected_savings_usd.toLocaleString()} USD`;
        savingsPct.textContent = `(${data.expected_savings_pct.toFixed(1)}% freight reduction)`;
        conf.className = "text-xs text-emerald-400 font-semibold";
        conf.textContent = `Confidence: ${data.confidence_pct}%`;
        iconBadge.className = "w-12 h-12 rounded-xl bg-emerald-500/20 border border-emerald-500/50 flex items-center justify-center text-emerald-400";
        iconBadge.innerHTML = '<i data-lucide="clock" class="w-6 h-6"></i>';
    } else {
        banner.className = "bg-gradient-to-r from-sky-950/80 via-steel-900 to-steel-900 border border-sky-500/40 rounded-2xl p-5 shadow-xl";
        tag.className = "px-2.5 py-0.5 rounded-full text-xs font-black bg-sky-400 text-slate-950 tracking-wider";
        tag.textContent = "BOOK NOW";
        headline.textContent = `Lock in Spot Charter Today ($${data.current_spot_rate_usd_t.toFixed(2)}/MT)`;
        savingsUsd.className = "text-xl font-black text-sky-400";
        savingsUsd.textContent = "Risk Protected";
        savingsPct.textContent = "(Upward pressure mitigated)";
        conf.className = "text-xs text-sky-400 font-semibold";
        conf.textContent = `Confidence: ${data.confidence_pct}%`;
        iconBadge.className = "w-12 h-12 rounded-xl bg-sky-500/20 border border-sky-500/50 flex items-center justify-center text-sky-400";
        iconBadge.innerHTML = '<i data-lucide="check-circle-2" class="w-6 h-6"></i>';
    }
    summary.textContent = data.decision_summary;

    document.getElementById("recommended-vessel-badge").textContent = data.recommended_vessel_class;

    const vesselList = document.getElementById("vessel-list");
    vesselList.innerHTML = "";
    data.all_vessel_matches.forEach(v => {
        const row = document.createElement("div");
        row.className = `p-2 rounded-lg border ${v.is_suitable ? (v.vessel_class === data.recommended_vessel_class ? 'bg-brand-950/40 border-brand-500/50' : 'bg-steel-850 border-slate-800') : 'bg-rose-950/20 border-rose-900/40 opacity-70'} flex flex-col space-y-1`;
        row.innerHTML = `
            <div class="flex items-center justify-between">
                <div class="flex items-center space-x-2">
                    <span class="font-bold text-white">${v.vessel_class}</span>
                    <span class="text-[9px] px-1.5 py-0.5 rounded ${v.is_suitable ? 'bg-emerald-500/20 text-emerald-300' : 'bg-rose-500/20 text-rose-300'} font-semibold">
                        ${v.is_suitable ? 'COMPATIBLE' : 'RESTRICTED'}
                    </span>
                    ${v.vessel_class === data.recommended_vessel_class ? '<span class="text-[9px] bg-amber-500/20 text-amber-300 border border-amber-500/30 px-1 rounded font-bold">OPTIMAL FIT</span>' : ''}
                </div>
                <span class="text-slate-400 text-[10px]">Arrival Draft: <b class="text-slate-200">${v.estimated_arrival_draft_m}m</b> (Max: ${v.port_max_draft_m}m)</span>
            </div>
            ${v.disqualification_reasons.length > 0 ? `<p class="text-[10px] text-rose-400">&bull; ${v.disqualification_reasons.join(', ')}</p>` : ''}
            ${v.transshipment_recommendation ? `<p class="text-[10px] text-amber-300">&bull; ${v.transshipment_recommendation}</p>` : ''}
        `;
        vesselList.appendChild(row);
    });

    const eco = data.voyage_breakdown;
    document.getElementById("eco-duration").textContent = `${eco.steaming_days} Sea + ${(eco.loading_days + eco.discharge_days + eco.port_waiting_days).toFixed(1)} Port Days`;
    document.getElementById("eco-bunker").textContent = `${eco.bunker_vlsfo_mt.toLocaleString()} MT ($${eco.bunker_fuel_cost_usd.toLocaleString()})`;
    document.getElementById("eco-charter").textContent = `$${eco.vessel_charter_cost_usd.toLocaleString()}`;
    document.getElementById("eco-dues").textContent = `$${(eco.port_dues_usd + eco.canal_dues_usd + eco.lighterage_cost_usd).toLocaleString()}`;
    document.getElementById("eco-freight-rate").textContent = `$${data.current_spot_rate_usd_t.toFixed(2)} / MT`;

    const r = data.risk_assessment;
    const monsoonEl = document.getElementById("risk-monsoon");
    if (r.monsoon_impact_flag) {
        monsoonEl.className = "p-1.5 rounded bg-amber-950/40 text-amber-300 border border-amber-500/30 flex items-center space-x-1.5";
        monsoonEl.innerHTML = '<i data-lucide="alert-triangle" class="w-3.5 h-3.5 text-amber-400"></i><span>Monsoon Active</span>';
    } else {
        monsoonEl.className = "p-1.5 rounded bg-slate-800 text-slate-300 flex items-center space-x-1.5";
        monsoonEl.innerHTML = '<i data-lucide="cloud-sun" class="w-3.5 h-3.5 text-emerald-400"></i><span>Monsoon: Clear</span>';
    }

    renderForecastChart(data);
    lucide.createIcons();
}

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

    forecastChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Predicted Rate ($/MT)',
                    data: forecastSeries,
                    borderColor: '#f59e0b',
                    borderWidth: 2.5,
                    pointBackgroundColor: (context) => context.dataIndex === data.optimal_booking_day_offset ? '#10b981' : '#f59e0b',
                    pointRadius: (context) => context.dataIndex === data.optimal_booking_day_offset ? 6 : 2,
                    tension: 0.25,
                    fill: false,
                    zIndex: 10
                },
                {
                    label: 'Upper 80% CI',
                    data: upper80Series,
                    borderColor: 'rgba(245, 158, 11, 0.15)',
                    borderWidth: 1,
                    pointRadius: 0,
                    fill: '+1',
                    backgroundColor: 'rgba(245, 158, 11, 0.08)',
                    tension: 0.25
                },
                {
                    label: 'Lower 80% CI',
                    data: lower80Series,
                    borderColor: 'rgba(245, 158, 11, 0.15)',
                    borderWidth: 1,
                    pointRadius: 0,
                    fill: false,
                    tension: 0.25
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
                    backgroundColor: '#1e293b',
                    titleColor: '#ffffff',
                    bodyColor: '#cbd5e1',
                    borderColor: '#334155',
                    borderWidth: 1,
                    callbacks: {
                        label: (c) => `${c.dataset.label}: $${c.raw?.toFixed(2) || 'N/A'}`
                    }
                }
            },
            scales: {
                x: { grid: { color: 'rgba(51, 65, 85, 0.3)' }, ticks: { color: '#94a3b8', font: { size: 10 } } },
                y: { grid: { color: 'rgba(51, 65, 85, 0.3)' }, ticks: { color: '#94a3b8', font: { size: 10 }, callback: (val) => `$${val}` } }
            }
        }
    });
}

// Backtest Data
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
            tr.className = "hover:bg-steel-850/50";
            tr.innerHTML = `
                <td class="py-2.5 px-3 font-semibold text-slate-400">${t.trade_id}</td>
                <td class="py-2.5 px-3 text-slate-200">${t.date}</td>
                <td class="py-2.5 px-3 text-slate-300">${t.route} (${t.vessel_class})</td>
                <td class="py-2.5 px-3 font-mono">$${t.spot_rate_usd_t.toFixed(2)}</td>
                <td class="py-2.5 px-3"><span class="px-1.5 py-0.5 rounded text-[10px] font-bold ${t.model_action === 'WAIT' ? 'bg-amber-500/20 text-amber-300' : 'bg-sky-500/20 text-sky-300'}">${t.model_action}</span></td>
                <td class="py-2.5 px-3 font-mono text-emerald-400 font-bold">$${t.actual_booked_rate_usd_t.toFixed(2)}</td>
                <td class="py-2.5 px-3 font-mono font-semibold ${t.savings_usd >= 0 ? 'text-emerald-400' : 'text-rose-400'}">${t.savings_usd >= 0 ? '+' : ''}$${t.savings_usd.toLocaleString()}</td>
                <td class="py-2.5 px-3"><span class="px-2 py-0.5 rounded-full text-[10px] font-bold ${t.was_profitable ? 'bg-emerald-500/20 text-emerald-300' : 'bg-slate-700 text-slate-300'}">${t.was_profitable ? 'PROFIT' : 'NEUTRAL'}</span></td>
            `;
            tableBody.appendChild(tr);
        });
        showToast("Historical Backtest simulation synchronized", "info");
    } catch (err) {
        console.error("Backtest load error:", err);
    }
}

// Ports Registry
async function initPortsHandbook() {
    try {
        const response = await fetch("/api/v1/ports/indian");
        const ports = await response.json();
        const tableBody = document.getElementById("ports-table-body");
        if (!tableBody) return;
        tableBody.innerHTML = "";
        ports.forEach(p => {
            const tr = document.createElement("tr");
            tr.className = "hover:bg-steel-850/50";
            tr.innerHTML = `
                <td class="py-3 px-3 font-bold text-white">${p.name} <span class="text-[10px] text-slate-400 block">${p.state_or_country}</span></td>
                <td class="py-3 px-3 font-semibold text-amber-400">${p.max_draft_m} m</td>
                <td class="py-3 px-3 text-slate-300">${p.max_loa_m} m</td>
                <td class="py-3 px-3 text-slate-300">${p.max_beam_m} m</td>
                <td class="py-3 px-3 font-semibold text-brand-300">${p.allowed_vessel_classes[p.allowed_vessel_classes.length - 1]}</td>
                <td class="py-3 px-3 text-slate-200">${p.handling_rate_tpd.toLocaleString()} TPD</td>
                <td class="py-3 px-3"><span class="px-2 py-0.5 rounded text-[10px] font-bold ${p.lighterage_required ? 'bg-rose-500/20 text-rose-300' : 'bg-emerald-500/20 text-emerald-300'}">${p.lighterage_required ? 'YES (Sandheads)' : 'NO (Direct)'}</span></td>
                <td class="py-3 px-3 text-slate-400 text-[11px]">${p.notes || 'Direct Rail link'}</td>
            `;
            tableBody.appendChild(tr);
        });
    } catch (err) {
        console.error("Ports handbook error:", err);
    }
}

// Board Approval Memo Modal
function openProcurementMemo() {
    if (!currentOptimizationData) return;
    const d = currentOptimizationData;
    const isWait = d.recommendation === "WAIT";
    
    document.getElementById("memo-date").textContent = new Date().toLocaleString();
    document.getElementById("memo-officer").textContent = currentUserProfile ? `${currentUserProfile.name} (${currentUserProfile.role})` : "Devendra Tyagi (CPO)";
    
    const badge = document.getElementById("memo-decision-badge");
    badge.className = isWait ? "px-2.5 py-0.5 rounded font-black bg-emerald-600 text-white" : "px-2.5 py-0.5 rounded font-black bg-sky-600 text-white";
    badge.textContent = d.recommendation === "WAIT" ? `WAIT TO BOOK (TARGET DAY ${d.optimal_booking_day_offset})` : "BOOK SPOT CHARTER NOW";

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
