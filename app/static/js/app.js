let forecastChartInstance = null;

document.addEventListener("DOMContentLoaded", () => {
    lucide.createIcons();
    initTabNavigation();
    initSliders();
    initPortsHandbook();
    initOptimizer();
    initBacktest();
    
    // Auto-run the default 75k MT coal demo on load
    runOptimization();
});

// Tab Navigation
function initTabNavigation() {
    const tabButtons = {
        optimizer: document.getElementById("tab-btn-optimizer"),
        backtest: document.getElementById("tab-btn-backtest"),
        ports: document.getElementById("tab-btn-ports")
    };

    const tabContents = {
        optimizer: document.getElementById("tab-optimizer"),
        backtest: document.getElementById("tab-backtest"),
        ports: document.getElementById("tab-ports")
    };

    Object.keys(tabButtons).forEach(key => {
        tabButtons[key].addEventListener("click", () => {
            Object.values(tabButtons).forEach(btn => {
                btn.classList.remove("active", "border-brand-500", "text-brand-400");
                btn.classList.add("border-transparent", "text-slate-400");
            });
            Object.values(tabContents).forEach(content => content.classList.add("hidden"));
            
            tabButtons[key].classList.add("active", "border-brand-500", "text-brand-400");
            tabButtons[key].classList.remove("border-transparent", "text-slate-400");
            tabContents[key].classList.remove("hidden");

            if (key === "backtest") {
                loadBacktestData();
            }
        });
    });
}

// Sliders initialization
function initSliders() {
    const tonnageSlider = document.getElementById("inp-tonnage-slider");
    const tonnageDisplay = document.getElementById("tonnage-display");
    tonnageSlider.addEventListener("input", (e) => {
        const val = parseInt(e.target.value);
        tonnageDisplay.textContent = `${val.toLocaleString()} MT`;
    });

    const laycanSlider = document.getElementById("inp-laycan");
    const laycanDisplay = document.getElementById("laycan-display");
    laycanSlider.addEventListener("input", (e) => {
        laycanDisplay.textContent = `${e.target.value} Days Ahead`;
    });

    document.getElementById("btn-quick-demo").addEventListener("click", () => {
        // Set inputs to official demo scenario
        document.getElementById("inp-commodity").value = "Coking Coal";
        tonnageSlider.value = 75000;
        tonnageDisplay.textContent = "75,000 MT";
        document.getElementById("inp-origin").value = "AUHPT";
        document.getElementById("inp-dest").value = "INPRT";
        laycanSlider.value = 21;
        laycanDisplay.textContent = "21 Days Ahead";
        
        // Select Balanced
        document.querySelector('input[name="risk_strategy"][value="BALANCED"]').checked = true;

        // Switch to optimizer tab and run
        document.getElementById("tab-btn-optimizer").click();
        runOptimization();
    });
}

// Optimizer Form Submission
function initOptimizer() {
    const form = document.getElementById("optimizer-form");
    form.addEventListener("submit", (e) => {
        e.preventDefault();
        runOptimization();
    });
}

async function runOptimization() {
    const tonnage = parseFloat(document.getElementById("inp-tonnage-slider").value);
    const commodity = document.getElementById("inp-commodity").value;
    const origin = document.getElementById("inp-origin").value;
    const dest = document.getElementById("inp-dest").value;
    const laycan = parseInt(document.getElementById("inp-laycan").value);
    const risk = document.querySelector('input[name="risk_strategy"]:checked').value;

    const payload = {
        parcel_tonnage_mt: tonnage,
        commodity: commodity,
        origin_port_id: origin,
        dest_port_id: dest,
        laycan_days_ahead: laycan,
        risk_tolerance: risk,
        holding_cost_usd_per_day: 2500.0
    };

    try {
        const response = await fetch("/api/v1/optimize", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        
        if (!response.ok) {
            throw new Error(`API error: ${response.statusText}`);
        }

        const data = await response.json();
        renderOptimizationResults(data);
    } catch (err) {
        console.error("Optimization failed:", err);
    }
}

function renderOptimizationResults(data) {
    // 1. Decision Banner
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
        banner.className = "bg-gradient-to-r from-emerald-950/80 via-steel-900 to-steel-900 border border-emerald-500/40 rounded-xl p-5 shadow-xl";
        tag.className = "px-2.5 py-0.5 rounded-full text-xs font-black bg-emerald-500 text-slate-950 tracking-wider";
        tag.textContent = "WAIT TO BOOK";
        headline.textContent = `Recommended Booking: Day ${data.optimal_booking_day_offset} (${data.optimal_booking_date})`;
        savingsUsd.className = "text-xl font-extrabold text-emerald-400";
        savingsUsd.textContent = `$${data.expected_savings_usd.toLocaleString()} USD`;
        savingsPct.textContent = `(${data.expected_savings_pct.toFixed(1)}% freight reduction)`;
        conf.className = "text-xs text-emerald-400 font-semibold";
        conf.textContent = `Confidence: ${data.confidence_pct}%`;
        iconBadge.className = "w-12 h-12 rounded-xl bg-emerald-500/20 border border-emerald-500/50 flex items-center justify-center text-emerald-400";
        iconBadge.innerHTML = '<i data-lucide="clock" class="w-7 h-7"></i>';
    } else {
        banner.className = "bg-gradient-to-r from-sky-950/80 via-steel-900 to-steel-900 border border-sky-500/40 rounded-xl p-5 shadow-xl";
        tag.className = "px-2.5 py-0.5 rounded-full text-xs font-black bg-sky-400 text-slate-950 tracking-wider";
        tag.textContent = "BOOK NOW";
        headline.textContent = `Lock in Spot Charter Today ($${data.current_spot_rate_usd_t.toFixed(2)}/MT)`;
        savingsUsd.className = "text-xl font-extrabold text-sky-400";
        savingsUsd.textContent = "Risk Protected";
        savingsPct.textContent = "(Upward pressure mitigated)";
        conf.className = "text-xs text-sky-400 font-semibold";
        conf.textContent = `Confidence: ${data.confidence_pct}%`;
        iconBadge.className = "w-12 h-12 rounded-xl bg-sky-500/20 border border-sky-500/50 flex items-center justify-center text-sky-400";
        iconBadge.innerHTML = '<i data-lucide="check-circle" class="w-7 h-7"></i>';
    }
    summary.textContent = data.decision_summary;

    // 2. Recommended Vessel Badge
    document.getElementById("recommended-vessel-badge").textContent = data.recommended_vessel_class;

    // 3. Vessel Compatibility List
    const vesselList = document.getElementById("vessel-list");
    vesselList.innerHTML = "";
    data.all_vessel_matches.forEach(v => {
        const row = document.createElement("div");
        row.className = `p-2.5 rounded border ${v.is_suitable ? (v.vessel_class === data.recommended_vessel_class ? 'bg-brand-950/40 border-brand-500/50' : 'bg-steel-850 border-slate-800') : 'bg-rose-950/20 border-rose-900/40 opacity-70'} flex flex-col space-y-1`;
        
        row.innerHTML = `
            <div class="flex items-center justify-between">
                <div class="flex items-center space-x-2">
                    <span class="font-bold text-white">${v.vessel_class}</span>
                    <span class="text-[10px] px-1.5 py-0.5 rounded ${v.is_suitable ? 'bg-emerald-500/20 text-emerald-300' : 'bg-rose-500/20 text-rose-300'} font-semibold">
                        ${v.is_suitable ? 'COMPATIBLE' : 'RESTRICTED'}
                    </span>
                    ${v.vessel_class === data.recommended_vessel_class ? '<span class="text-[10px] bg-amber-500/20 text-amber-300 border border-amber-500/30 px-1 rounded font-bold">OPTIMAL FIT</span>' : ''}
                </div>
                <span class="text-slate-400 text-[11px]">Arrival Draft: <b class="text-slate-200">${v.estimated_arrival_draft_m}m</b> (Max: ${v.port_max_draft_m}m)</span>
            </div>
            ${v.disqualification_reasons.length > 0 ? `<p class="text-[10px] text-rose-400 mt-0.5">&bull; ${v.disqualification_reasons.join(', ')}</p>` : ''}
            ${v.transshipment_recommendation ? `<p class="text-[10px] text-amber-300 mt-0.5">&bull; ${v.transshipment_recommendation}</p>` : ''}
        `;
        vesselList.appendChild(row);
    });

    // 4. Voyage Economics
    const eco = data.voyage_breakdown;
    document.getElementById("eco-duration").textContent = `${eco.steaming_days} Sea Days + ${(eco.loading_days + eco.discharge_days + eco.port_waiting_days).toFixed(1)} Port Days`;
    document.getElementById("eco-bunker").textContent = `${eco.bunker_vlsfo_mt.toLocaleString()} MT ($${eco.bunker_fuel_cost_usd.toLocaleString()})`;
    document.getElementById("eco-charter").textContent = `$${eco.vessel_charter_cost_usd.toLocaleString()}`;
    document.getElementById("eco-dues").textContent = `$${(eco.port_dues_usd + eco.canal_dues_usd + eco.lighterage_cost_usd).toLocaleString()}`;
    document.getElementById("eco-freight-rate").textContent = `$${data.current_spot_rate_usd_t.toFixed(2)} / MT`;

    // 5. Risk Signals
    const r = data.risk_assessment;
    const monsoonEl = document.getElementById("risk-monsoon");
    if (r.monsoon_impact_flag) {
        monsoonEl.className = "p-1.5 rounded bg-amber-950/40 text-amber-300 border border-amber-500/30 flex items-center space-x-1.5";
        monsoonEl.innerHTML = '<i data-lucide="alert-triangle" class="w-3.5 h-3.5 text-amber-400"></i><span>Monsoon Active</span>';
    } else {
        monsoonEl.className = "p-1.5 rounded bg-slate-800 text-slate-300 flex items-center space-x-1.5";
        monsoonEl.innerHTML = '<i data-lucide="cloud-sun" class="w-3.5 h-3.5 text-emerald-400"></i><span>Monsoon: Clear</span>';
    }

    const congEl = document.getElementById("risk-congestion");
    congEl.className = r.congestion_risk_level === 'HIGH' ? "p-1.5 rounded bg-rose-950/40 text-rose-300 border border-rose-500/30 flex items-center space-x-1.5" : "p-1.5 rounded bg-slate-800 text-slate-300 flex items-center space-x-1.5";
    congEl.innerHTML = `<i data-lucide="anchor" class="w-3.5 h-3.5 text-slate-400"></i><span>Congestion: ${r.congestion_risk_level}</span>`;

    // 6. Render Chart
    renderForecastChart(data);

    lucide.createIcons();
}

function renderForecastChart(data) {
    const ctx = document.getElementById("forecastChart").getContext("2d");
    
    const labels = ["Spot Today"];
    const spotSeries = [data.current_spot_rate_usd_t];
    const forecastSeries = [data.current_spot_rate_usd_t];
    const upper80Series = [data.current_spot_rate_usd_t];
    const lower80Series = [data.current_spot_rate_usd_t];

    data.forecast_curve.forEach((pt, idx) => {
        labels.push(`Day ${pt.day_offset}`);
        spotSeries.push(null);
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
                    borderColor: '#f59e0b', // amber-500
                    borderWidth: 2.5,
                    pointBackgroundColor: (context) => {
                        return context.dataIndex === data.optimal_booking_day_offset ? '#10b981' : '#f59e0b';
                    },
                    pointRadius: (context) => {
                        return context.dataIndex === data.optimal_booking_day_offset ? 6 : 2;
                    },
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
            interaction: {
                intersect: false,
                mode: 'index'
            },
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: '#1e293b',
                    titleColor: '#ffffff',
                    bodyColor: '#cbd5e1',
                    borderColor: '#334155',
                    borderWidth: 1,
                    callbacks: {
                        label: function(context) {
                            return `${context.dataset.label}: $${context.raw?.toFixed(2) || 'N/A'}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: { color: 'rgba(51, 65, 85, 0.3)' },
                    ticks: { color: '#94a3b8', font: { size: 10 } }
                },
                y: {
                    grid: { color: 'rgba(51, 65, 85, 0.3)' },
                    ticks: {
                        color: '#94a3b8',
                        font: { size: 10 },
                        callback: (val) => `$${val}`
                    }
                }
            }
        }
    });
}

// Backtest Tab
function initBacktest() {
    document.getElementById("btn-run-backtest").addEventListener("click", () => {
        loadBacktestData();
    });
}

async function loadBacktestData() {
    try {
        const response = await fetch("/api/v1/backtest?period_days=365&origin_port_id=AUHPT&dest_port_id=INPRT&parcel_size_mt=75000", {
            method: "POST"
        });
        const data = await response.json();
        renderBacktestResults(data);
    } catch (err) {
        console.error("Backtest load error:", err);
    }
}

function renderBacktestResults(data) {
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
            <td class="py-2.5 px-3">
                <span class="px-1.5 py-0.5 rounded text-[10px] font-bold ${t.model_action === 'WAIT' ? 'bg-amber-500/20 text-amber-300' : 'bg-sky-500/20 text-sky-300'}">
                    ${t.model_action}
                </span>
            </td>
            <td class="py-2.5 px-3 font-mono text-emerald-400 font-bold">$${t.actual_booked_rate_usd_t.toFixed(2)}</td>
            <td class="py-2.5 px-3 font-mono font-semibold ${t.savings_usd >= 0 ? 'text-emerald-400' : 'text-rose-400'}">
                ${t.savings_usd >= 0 ? '+' : ''}$${t.savings_usd.toLocaleString()}
            </td>
            <td class="py-2.5 px-3">
                <span class="px-2 py-0.5 rounded-full text-[10px] font-bold ${t.was_profitable ? 'bg-emerald-500/20 text-emerald-300' : 'bg-slate-700 text-slate-300'}">
                    ${t.was_profitable ? 'PROFIT' : 'NEUTRAL'}
                </span>
            </td>
        `;
        tableBody.appendChild(tr);
    });
}

// Ports Handbook Tab
async function initPortsHandbook() {
    try {
        const response = await fetch("/api/v1/ports/indian");
        const ports = await response.json();
        const tableBody = document.getElementById("ports-table-body");
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
                <td class="py-3 px-3">
                    <span class="px-2 py-0.5 rounded text-[10px] font-bold ${p.lighterage_required ? 'bg-rose-500/20 text-rose-300' : 'bg-emerald-500/20 text-emerald-300'}">
                        ${p.lighterage_required ? 'YES (Sandheads)' : 'NO (Direct)'}
                    </span>
                </td>
                <td class="py-3 px-3 text-slate-400 text-[11px]">${p.notes || 'Direct Rail link'}</td>
            `;
            tableBody.appendChild(tr);
        });
    } catch (err) {
        console.error("Failed to load ports handbook:", err);
    }
}
