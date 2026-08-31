
// FreightIQ — Professional Charter Intelligence Platform
'use strict';

let chartInstance = null;
let optimizationData = null;
let scenarios = [];
let notifications = [];
let userProfile = null;

// ─── Boot ──────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', async () => {
  lucide.createIcons();
  initSliders();
  initOptimizer();
  await Promise.all([
    loadScenarios(),
    loadNotifications(),
    switchUserRole('cpo')
  ]);
  runOptimization(false);

  document.addEventListener('click', e => {
    if (!e.target.closest('[onclick*="scenarios-menu"]') && !e.target.closest('#scenarios-menu'))
      document.getElementById('scenarios-menu').style.display = 'none';
    if (!e.target.closest('[onclick*="notifications-panel"]') && !e.target.closest('#notifications-panel'))
      document.getElementById('notifications-panel').style.display = 'none';
    if (!e.target.closest('[onclick*="user-menu"]') && !e.target.closest('#user-menu'))
      document.getElementById('user-menu').style.display = 'none';
  });
});

// ─── Navigation ────────────────────────────────────────────────────────────
function navigateToTab(id) {
  ['landing','optimizer','market','backtest','ports'].forEach(t => {
    const v = document.getElementById('view-' + t);
    const n = document.getElementById('nav-' + t);
    const isActive = t === id;
    if (v) v.style.display = isActive ? 'block' : 'none';
    if (n) { n.classList.toggle('active', isActive); }
  });
  if (id === 'backtest') loadBacktestData();
  window.scrollTo({ top: 0, behavior: 'smooth' });
  lucide.createIcons();
}

function toggleDropdown(id) {
  ['scenarios-menu','notifications-panel','user-menu'].forEach(other => {
    if (other !== id) document.getElementById(other).style.display = 'none';
  });
  const el = document.getElementById(id);
  el.style.display = el.style.display === 'none' ? 'block' : 'none';
}

// ─── Toast Notifications ───────────────────────────────────────────────────
function showToast(msg, type = 'info') {
  const c = document.getElementById('toast-container');
  const colors = {
    success: { bg: '#0a1f1c', border: 'rgba(13,148,136,0.4)', text: '#5eead4' },
    warning: { bg: '#1c1408', border: 'rgba(217,119,6,0.4)', text: '#fbbf24' },
    error:   { bg: '#1c0a0a', border: 'rgba(220,38,38,0.4)', text: '#fca5a5' },
    info:    { bg: '#0c1117', border: '#1a2332', text: '#94a3b8' }
  };
  const col = colors[type] || colors.info;
  const toast = document.createElement('div');
  toast.style.cssText = `pointer-events:auto;display:flex;align-items:center;gap:8px;padding:10px 14px;border-radius:7px;border:1px solid ${col.border};background:${col.bg};color:${col.text};font-size:0.8125rem;font-weight:500;box-shadow:0 4px 16px rgba(0,0,0,0.4);opacity:0;transition:opacity 0.2s;font-family:'Inter',sans-serif;`;
  toast.innerHTML = `<i data-lucide="info" style="width:14px;height:14px;flex-shrink:0;"></i><span>${msg}</span>`;
  c.appendChild(toast);
  lucide.createIcons();
  setTimeout(() => toast.style.opacity = '1', 10);
  setTimeout(() => { toast.style.opacity = '0'; setTimeout(() => toast.remove(), 200); }, 4000);
}

// ─── Sliders ───────────────────────────────────────────────────────────────
function initSliders() {
  const ts = document.getElementById('inp-tonnage-slider');
  const td = document.getElementById('tonnage-display');
  ts?.addEventListener('input', e => { td.textContent = `${parseInt(e.target.value).toLocaleString()} MT`; });
  const ls = document.getElementById('inp-laycan');
  const ld = document.getElementById('laycan-display');
  ls?.addEventListener('input', e => { ld.textContent = `${e.target.value} days`; });
}

// ─── Scenarios ─────────────────────────────────────────────────────────────
async function loadScenarios() {
  try {
    const res = await fetch('/api/v1/scenarios');
    scenarios = await res.json();
    const list = document.getElementById('scenarios-list');
    list.innerHTML = '';
    scenarios.forEach(sc => {
      const btn = document.createElement('button');
      btn.style.cssText = 'width:100%;text-align:left;padding:8px 10px;border-radius:6px;background:none;border:none;cursor:pointer;display:flex;flex-direction:column;gap:2px;transition:background 0.15s;';
      btn.onmouseenter = () => btn.style.background = '#111720';
      btn.onmouseleave = () => btn.style.background = 'none';
      btn.onclick = () => { loadScenario(sc.id); document.getElementById('scenarios-menu').style.display='none'; };
      btn.innerHTML = `<div style="display:flex;justify-content:space-between;"><span style="font-size:0.8125rem;font-weight:600;color:#f1f5f9;">${sc.title}</span><span style="font-size:9px;padding:1px 6px;border-radius:3px;background:rgba(37,99,235,0.1);color:#93c5fd;border:1px solid rgba(37,99,235,0.15);font-weight:600;">${sc.tag}</span></div><span style="font-size:0.6875rem;color:#64748b;">${sc.subtitle}</span>`;
      list.appendChild(btn);
    });
  } catch(e) { console.warn('Scenarios load failed', e); }
}

function loadScenario(id) {
  const sc = scenarios.find(s => s.id === id);
  if (!sc) return;
  const r = sc.request;
  document.getElementById('inp-commodity').value = r.commodity;
  document.getElementById('inp-tonnage-slider').value = r.parcel_tonnage_mt;
  document.getElementById('tonnage-display').textContent = `${r.parcel_tonnage_mt.toLocaleString()} MT`;
  document.getElementById('inp-origin').value = r.origin_port_id;
  document.getElementById('inp-dest').value = r.dest_port_id;
  document.getElementById('inp-laycan').value = r.laycan_days_ahead;
  document.getElementById('laycan-display').textContent = `${r.laycan_days_ahead} days`;
  document.getElementById('inp-holding-cost').value = r.holding_cost_usd_per_day;
  document.getElementById('inp-risk-strategy').value = r.risk_tolerance;
  navigateToTab('optimizer');
  runOptimization(true);
  showToast(`Scenario loaded: ${sc.title}`, 'info');
}

// ─── Notifications ─────────────────────────────────────────────────────────
async function loadNotifications() {
  try {
    const res = await fetch('/api/v1/notifications');
    notifications = await res.json();
    const list = document.getElementById('notifications-list');
    list.innerHTML = '';
    notifications.forEach(n => {
      const typeColor = { alert: '#fbbf24', warning: '#fca5a5', info: '#93c5fd' };
      const item = document.createElement('div');
      item.style.cssText = 'padding:8px;border-radius:6px;cursor:pointer;transition:background 0.15s;';
      item.onmouseenter = () => item.style.background = '#111720';
      item.onmouseleave = () => item.style.background = 'transparent';
      item.innerHTML = `<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:3px;"><span style="font-size:0.8125rem;font-weight:600;color:${typeColor[n.type] || '#93c5fd'};">${n.title}</span><span style="font-size:10px;color:#3a4a5e;font-family:'JetBrains Mono',monospace;">${n.time}</span></div><p style="font-size:0.75rem;color:#64748b;line-height:1.5;margin:0;">${n.message}</p>`;
      list.appendChild(item);
    });
    lucide.createIcons();
  } catch(e) { console.warn('Notifications load failed', e); }
}

function markAllNotificationsRead() {
  document.getElementById('notif-badge').style.display = 'none';
  document.getElementById('notifications-panel').style.display = 'none';
  showToast('All signals marked as read', 'info');
}

// ─── Role Switcher ─────────────────────────────────────────────────────────
async function switchUserRole(roleKey) {
  try {
    const res = await fetch(`/api/v1/profile?role=${roleKey}`);
    userProfile = await res.json();
    document.getElementById('user-avatar').textContent = userProfile.avatar_badge;
    document.getElementById('user-display-name').textContent = userProfile.name;
    document.getElementById('user-role-name').textContent = userProfile.title.split(' ').slice(0,2).join(' ');
    document.getElementById('menu-user-name').textContent = userProfile.name;
    document.getElementById('menu-user-title').textContent = userProfile.title;
    document.getElementById('user-menu').style.display = 'none';
    showToast(`View: ${userProfile.role}`, 'info');
  } catch(e) { console.warn('Role switch failed', e); }
}

// ─── Optimizer ─────────────────────────────────────────────────────────────
function initOptimizer() {
  document.getElementById('optimizer-form')?.addEventListener('submit', e => { e.preventDefault(); runOptimization(true); });
}

async function runOptimization(notify = false) {
  const payload = {
    parcel_tonnage_mt: parseFloat(document.getElementById('inp-tonnage-slider').value),
    commodity: document.getElementById('inp-commodity').value,
    origin_port_id: document.getElementById('inp-origin').value,
    dest_port_id: document.getElementById('inp-dest').value,
    laycan_days_ahead: parseInt(document.getElementById('inp-laycan').value),
    risk_tolerance: document.getElementById('inp-risk-strategy').value,
    holding_cost_usd_per_day: parseFloat(document.getElementById('inp-holding-cost').value || 2500)
  };
  try {
    const res = await fetch('/api/v1/optimize', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(payload) });
    if (!res.ok) throw new Error(res.statusText);
    optimizationData = await res.json();
    renderResults(optimizationData);
    if (notify) showToast(`Decision: ${optimizationData.recommendation}`, 'success');
  } catch(e) {
    console.error('Optimization error', e);
    if (notify) showToast('Optimization failed', 'error');
  }
}

function renderResults(d) {
  const isWait = d.recommendation === 'WAIT';
  const banner = document.getElementById('decision-banner');
  const tag    = document.getElementById('decision-action-tag');
  const head   = document.getElementById('decision-headline');
  const savings= document.getElementById('decision-savings-usd');
  const pct    = document.getElementById('decision-savings-pct');
  const summ   = document.getElementById('decision-summary-text');
  const conf   = document.getElementById('decision-confidence');
  const icon   = document.getElementById('decision-icon-badge');

  if (isWait) {
    banner.style.borderColor = 'rgba(13,148,136,0.3)';
    tag.className = 'badge badge-teal';
    tag.textContent = 'WAIT TO BOOK';
    head.textContent = `Optimal booking: Day ${d.optimal_booking_day_offset} — ${d.optimal_booking_date}`;
    savings.style.color = '#0d9488';
    savings.textContent = `$${d.expected_savings_usd.toLocaleString()}`;
    pct.textContent = `${d.expected_savings_pct.toFixed(1)}% freight reduction`;
    icon.style.background = 'rgba(13,148,136,0.12)';
    icon.style.borderColor = 'rgba(13,148,136,0.25)';
    icon.style.color = '#0d9488';
    icon.innerHTML = '<i data-lucide="clock" style="width:20px;height:20px;"></i>';
  } else {
    banner.style.borderColor = 'rgba(37,99,235,0.3)';
    tag.className = 'badge badge-blue';
    tag.textContent = 'BOOK NOW';
    head.textContent = `Spot lock-in recommended — $${d.current_spot_rate_usd_t.toFixed(2)}/MT`;
    savings.style.color = '#93c5fd';
    savings.textContent = 'Risk Protected';
    pct.textContent = 'Upward movement likely';
    icon.style.background = 'rgba(37,99,235,0.12)';
    icon.style.borderColor = 'rgba(37,99,235,0.25)';
    icon.style.color = '#93c5fd';
    icon.innerHTML = '<i data-lucide="check-circle" style="width:20px;height:20px;"></i>';
  }
  conf.textContent = `Confidence ${d.confidence_pct}%`;
  summ.textContent = d.decision_summary;
  document.getElementById('recommended-vessel-badge').textContent = d.recommended_vessel_class;

  // Vessel list
  const vl = document.getElementById('vessel-list');
  vl.innerHTML = '';
  d.all_vessel_matches.forEach(v => {
    const isRec = v.vessel_class === d.recommended_vessel_class;
    const el = document.createElement('div');
    el.style.cssText = `padding:8px 10px;border-radius:6px;border:1px solid ${isRec ? 'rgba(37,99,235,0.3)' : v.is_suitable ? '#1a2332' : 'rgba(220,38,38,0.2)'};background:${isRec ? 'rgba(37,99,235,0.06)' : '#06090f'};`;
    el.innerHTML = `<div style="display:flex;align-items:center;justify-content:space-between;gap:8px;">
      <div style="display:flex;align-items:center;gap:6px;">
        <span style="font-size:0.8125rem;font-weight:600;color:#f1f5f9;">${v.vessel_class}</span>
        ${isRec ? '<span class="badge badge-blue" style="font-size:9px;">OPTIMAL</span>' : ''}
        <span class="badge ${v.is_suitable ? 'badge-teal' : 'badge-red'}" style="font-size:9px;">${v.is_suitable ? 'PASS' : 'RESTRICTED'}</span>
      </div>
      <span style="font-size:0.6875rem;color:#64748b;font-family:'JetBrains Mono',monospace;">Draft ${v.estimated_arrival_draft_m}m / ${v.port_max_draft_m}m</span>
    </div>
    ${v.disqualification_reasons?.length ? `<div style="font-size:0.6875rem;color:#fca5a5;margin-top:4px;">${v.disqualification_reasons.join('; ')}</div>` : ''}`;
    vl.appendChild(el);
  });

  // Economics
  const eco = d.voyage_breakdown;
  document.getElementById('eco-duration').textContent = `${eco.steaming_days} + ${(eco.loading_days+eco.discharge_days+eco.port_waiting_days).toFixed(1)} days`;
  document.getElementById('eco-bunker').textContent = `${eco.bunker_vlsfo_mt.toLocaleString()} MT ($${eco.bunker_fuel_cost_usd.toLocaleString()})`;
  document.getElementById('eco-charter').textContent = `$${eco.vessel_charter_cost_usd.toLocaleString()}`;
  document.getElementById('eco-dues').textContent = `$${(eco.port_dues_usd+eco.canal_dues_usd+eco.lighterage_cost_usd).toLocaleString()}`;
  document.getElementById('eco-freight-rate').textContent = `$${d.current_spot_rate_usd_t.toFixed(2)}`;

  const monsoon = d.risk_assessment?.monsoon_impact_flag;
  const rm = document.getElementById('risk-monsoon');
  rm.innerHTML = monsoon ? '<i data-lucide="alert-triangle" style="width:12px;height:12px;color:#d97706;"></i>Monsoon Active' : '<i data-lucide="cloud-sun" style="width:12px;height:12px;color:#0d9488;"></i>Monsoon: Clear';
  rm.style.color = monsoon ? '#fbbf24' : '#94a3b8';

  renderChart(d);
  lucide.createIcons();
}

function renderChart(d) {
  const ctx = document.getElementById('forecastChart')?.getContext('2d');
  if (!ctx) return;
  const labels = ['Spot'];
  const fore = [d.current_spot_rate_usd_t];
  const up80 = [d.current_spot_rate_usd_t];
  const lo80 = [d.current_spot_rate_usd_t];
  d.forecast_curve.forEach(pt => {
    labels.push(`D${pt.day_offset}`);
    fore.push(pt.predicted_rate_usd_t);
    up80.push(pt.upper_80_pct);
    lo80.push(pt.lower_80_pct);
  });
  if (chartInstance) chartInstance.destroy();
  chartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [
        { label: 'Forecast', data: fore, borderColor: '#d97706', borderWidth: 2, pointRadius: fore.map((_,i) => i === d.optimal_booking_day_offset ? 5 : 2), pointBackgroundColor: fore.map((_,i) => i === d.optimal_booking_day_offset ? '#0d9488' : '#d97706'), tension: 0.3, fill: false, z: 5 },
        { label: 'Upper 80%', data: up80, borderColor: 'rgba(217,119,6,0.15)', borderWidth: 1, pointRadius: 0, fill: '+1', backgroundColor: 'rgba(217,119,6,0.06)', tension: 0.3 },
        { label: 'Lower 80%', data: lo80, borderColor: 'rgba(217,119,6,0.15)', borderWidth: 1, pointRadius: 0, fill: false, tension: 0.3 }
      ]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      interaction: { intersect: false, mode: 'index' },
      plugins: {
        legend: { display: false },
        tooltip: { backgroundColor: '#0c1117', titleColor: '#f1f5f9', bodyColor: '#94a3b8', borderColor: '#1a2332', borderWidth: 1, padding: 10, callbacks: { label: c => `${c.dataset.label}: $${c.raw?.toFixed(2)}` } }
      },
      scales: {
        x: { grid: { color: 'rgba(26,35,50,0.8)' }, ticks: { color: '#3a4a5e', font: { size: 10, family: 'JetBrains Mono' } } },
        y: { grid: { color: 'rgba(26,35,50,0.8)' }, ticks: { color: '#3a4a5e', font: { size: 10, family: 'JetBrains Mono' }, callback: v => '$' + v } }
      }
    }
  });
}

// ─── Backtest ──────────────────────────────────────────────────────────────
async function loadBacktestData() {
  try {
    const res = await fetch('/api/v1/backtest?period_days=365&origin_port_id=AUHPT&dest_port_id=INPRT&parcel_size_mt=75000', { method: 'POST' });
    const data = await res.json();
    document.getElementById('bt-spend-naive').textContent = `$${data.total_freight_spend_naive_usd.toLocaleString()}`;
    document.getElementById('bt-spend-model').textContent = `$${data.total_freight_spend_model_usd.toLocaleString()}`;
    document.getElementById('bt-total-savings').textContent = `$${data.total_savings_usd.toLocaleString()}`;
    document.getElementById('bt-savings-pct').textContent = `${data.savings_percentage.toFixed(2)}% net reduction`;
    document.getElementById('bt-win-rate').textContent = `${data.profitable_decisions_pct.toFixed(1)}%`;

    const tbody = document.getElementById('backtest-table-body');
    tbody.innerHTML = '';
    data.trades.forEach(t => {
      const pos = t.savings_usd >= 0;
      const tr = document.createElement('tr');
      tr.style.borderBottom = '1px solid #0c1117';
      tr.onmouseenter = () => tr.style.background = '#0c1117';
      tr.onmouseleave = () => tr.style.background = 'transparent';
      tr.innerHTML = `
        <td style="padding:10px 20px;font-size:0.8125rem;color:#3a4a5e;font-family:'JetBrains Mono',monospace;">${t.trade_id}</td>
        <td style="padding:10px 14px;font-size:0.8125rem;color:#94a3b8;">${t.date}</td>
        <td style="padding:10px 14px;font-size:0.8125rem;color:#94a3b8;">${t.route} · ${t.vessel_class}</td>
        <td style="padding:10px 14px;text-align:right;font-size:0.8125rem;font-family:'JetBrains Mono',monospace;color:#f1f5f9;">$${t.spot_rate_usd_t.toFixed(2)}</td>
        <td style="padding:10px 14px;text-align:center;"><span class="badge ${t.model_action === 'WAIT' ? 'badge-amber' : 'badge-blue'}" style="font-size:9px;">${t.model_action}</span></td>
        <td style="padding:10px 14px;text-align:right;font-size:0.8125rem;font-family:'JetBrains Mono',monospace;color:#0d9488;font-weight:600;">$${t.actual_booked_rate_usd_t.toFixed(2)}</td>
        <td style="padding:10px 14px;text-align:right;font-size:0.8125rem;font-family:'JetBrains Mono',monospace;color:${pos ? '#0d9488' : '#fca5a5'};font-weight:600;">${pos ? '+' : ''}$${t.savings_usd.toLocaleString()}</td>
        <td style="padding:10px 20px;text-align:center;"><span class="badge ${t.was_profitable ? 'badge-teal' : 'badge-slate'}" style="font-size:9px;">${t.was_profitable ? 'PROFIT' : 'NEUTRAL'}</span></td>`;
      tbody.appendChild(tr);
    });
    showToast('Backtest simulation synchronized', 'info');
  } catch(e) { console.error('Backtest error', e); }
}

// ─── Ports Registry ────────────────────────────────────────────────────────
async function initPortsHandbook() {
  try {
    const res = await fetch('/api/v1/ports/indian');
    const ports = await res.json();
    const tbody = document.getElementById('ports-table-body');
    tbody.innerHTML = '';
    ports.forEach(p => {
      const tr = document.createElement('tr');
      tr.style.borderBottom = '1px solid #0c1117';
      tr.onmouseenter = () => tr.style.background = '#0c1117';
      tr.onmouseleave = () => tr.style.background = 'transparent';
      tr.innerHTML = `
        <td style="padding:12px 20px;"><div style="font-size:0.8125rem;font-weight:500;color:#f1f5f9;">${p.name}</div><div style="font-size:0.6875rem;color:#64748b;">${p.state_or_country}</div></td>
        <td style="padding:12px 14px;text-align:right;font-family:'JetBrains Mono',monospace;font-size:0.8125rem;font-weight:600;color:#fbbf24;">${p.max_draft_m}m</td>
        <td style="padding:12px 14px;text-align:right;font-family:'JetBrains Mono',monospace;font-size:0.8125rem;color:#94a3b8;">${p.max_loa_m}m</td>
        <td style="padding:12px 14px;text-align:right;font-family:'JetBrains Mono',monospace;font-size:0.8125rem;color:#94a3b8;">${p.max_beam_m}m</td>
        <td style="padding:12px 14px;font-size:0.8125rem;color:#93c5fd;font-weight:500;">${p.allowed_vessel_classes.slice(-1)[0]}</td>
        <td style="padding:12px 14px;text-align:right;font-family:'JetBrains Mono',monospace;font-size:0.8125rem;color:#94a3b8;">${p.handling_rate_tpd.toLocaleString()}</td>
        <td style="padding:12px 14px;text-align:center;"><span class="badge ${p.lighterage_required ? 'badge-amber' : 'badge-teal'}" style="font-size:9px;">${p.lighterage_required ? 'REQUIRED' : 'DIRECT'}</span></td>
        <td style="padding:12px 20px;font-size:0.75rem;color:#64748b;">${p.notes || 'Direct rail link'}</td>`;
      tbody.appendChild(tr);
    });
  } catch(e) { console.error('Ports error', e); }
}

// ─── Memo Modal ────────────────────────────────────────────────────────────
function openProcurementMemo() {
  if (!optimizationData) return;
  const d = optimizationData;
  const now = new Date();
  document.getElementById('memo-date').textContent = now.toLocaleString('en-IN', { timeZone: 'Asia/Kolkata' }) + ' IST';
  document.getElementById('memo-officer').textContent = userProfile ? `${userProfile.name} (${userProfile.role})` : 'Devendra Tyagi (CPO)';
  const badge = document.getElementById('memo-decision-badge');
  badge.className = d.recommendation === 'WAIT' ? 'badge badge-teal' : 'badge badge-blue';
  badge.textContent = d.recommendation === 'WAIT' ? `WAIT — TARGET DAY ${d.optimal_booking_day_offset}` : 'BOOK SPOT NOW';
  document.getElementById('memo-rationale').textContent = d.decision_summary;
  document.getElementById('memo-cargo').textContent = `${d.voyage_breakdown?.parcel_tonnage_mt || 75000} MT ${document.getElementById('inp-commodity').value}`;
  document.getElementById('memo-vessel').textContent = d.recommended_vessel_class;
  document.getElementById('memo-spot-rate').textContent = `$${d.current_spot_rate_usd_t.toFixed(2)} / MT`;
  document.getElementById('memo-target-rate').textContent = `$${d.target_booking_rate_usd_t.toFixed(2)} / MT`;
  document.getElementById('memo-savings').textContent = `$${d.expected_savings_usd.toLocaleString()} (${d.expected_savings_pct.toFixed(1)}%)`;
  const modal = document.getElementById('modal-memo');
  modal.style.display = 'flex';
  lucide.createIcons();
}

function closeProcurementMemo() {
  document.getElementById('modal-memo').style.display = 'none';
}

// Expose globally
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
