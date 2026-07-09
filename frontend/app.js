/* ================================================================
   ClinicFlow — SPA Application Logic
   Backend: https://clinic-appointment-system-o71t.onrender.com
   ================================================================ */

const API = 'https://clinic-appointment-system-o71t.onrender.com';

/* ================================================================
   DOM HELPERS
   ================================================================ */
const $ = id => document.getElementById(id);
const el = id => document.getElementById(id); // alias

/* ================================================================
   TOAST NOTIFICATIONS
   ================================================================ */
function toast(msg, type = 'info') {
  const container = $('toast-container');
  if (!container) return;

  const icons = { success: '✓', error: '✕', info: 'ℹ', warning: '⚠' };
  const t = document.createElement('div');
  t.className = `toast ${type}`;
  t.innerHTML = `<span class="toast-icon">${icons[type] || 'ℹ'}</span><span>${msg}</span>`;
  container.appendChild(t);

  setTimeout(() => {
    t.style.opacity = '0';
    t.style.transform = 'translateX(20px)';
    t.style.transition = 'opacity .3s ease, transform .3s ease';
    setTimeout(() => t.remove(), 320);
  }, 4200);
}

/* ================================================================
   MODAL
   ================================================================ */
function showModal(title, bodyHTML) {
  $('modal-title').textContent = title;
  $('modal-body').innerHTML = bodyHTML;
  $('modal-overlay').classList.add('open');
  document.body.style.overflow = 'hidden';
}

function closeModal() {
  $('modal-overlay').classList.remove('open');
  document.body.style.overflow = '';
}

/* Close modal on overlay click */
$('modal-overlay')?.addEventListener('click', function (e) {
  if (e.target === this) closeModal();
});

/* ================================================================
   FORMATTERS
   ================================================================ */
function fmtDate(d) {
  if (!d) return '—';
  const dt = new Date(d + (d.includes('T') ? '' : 'T00:00:00'));
  if (isNaN(dt)) return d;
  return dt.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' });
}

function fmtDateTime(d) {
  if (!d) return '—';
  const dt = new Date(d);
  if (isNaN(dt)) return d;
  return dt.toLocaleString('en-IN', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' });
}

function badge(status) {
  const s = (status || '').toLowerCase().replace(/ /g, '_');
  return `<span class="badge badge-${s}">${(status || '—').replace(/_/g, ' ')}</span>`;
}

function progressBar(score) {
  const pct = Math.min(100, Math.round((score || 0) * 100));
  const cls = pct >= 80 ? 'high' : pct >= 50 ? 'medium' : 'low';
  return `
    <div class="progress-bar-wrap">
      <div class="progress-bar">
        <div class="progress-fill ${cls}" style="width:${pct}%"></div>
      </div>
      <span class="progress-pct">${pct}%</span>
    </div>`;
}

/* ================================================================
   API FETCH WRAPPER
   ================================================================ */
async function apiFetch(path, opts = {}) {
  const res = await fetch(API + path, {
    headers: { 'Content-Type': 'application/json', ...(opts.headers || {}) },
    ...opts
  });
  if (!res.ok) {
    let errMsg = res.statusText;
    try {
      const err = await res.json();
      errMsg = err.detail || errMsg;
    } catch (_) {}
    throw new Error(errMsg);
  }
  return res.status === 204 ? null : res.json();
}

/* ================================================================
   NAVIGATION & VIEW ROUTING
   ================================================================ */
const VIEWS = {
  dashboard:    { title: 'Dashboard',         breadcrumb: 'Overview',       render: renderDashboard },
  appointments: { title: 'Appointments',       breadcrumb: 'Staff Portal',   render: renderAppointments },
  intakes:      { title: 'Intake Forms',       breadcrumb: 'Staff Portal',   render: renderIntakes },
  followups:    { title: 'Follow-ups',         breadcrumb: 'Staff Portal',   render: renderFollowups },
  patients:     { title: 'Patients',           breadcrumb: 'Staff Portal',   render: renderPatients },
  book:         { title: 'Book Appointment',   breadcrumb: 'Patient Portal', render: renderBook },
};

let currentView = 'dashboard';

function navigate(view) {
  if (!VIEWS[view]) return;
  currentView = view;
  closeSidebar();

  document.querySelectorAll('.nav-item').forEach(n => {
    n.classList.toggle('active', n.dataset.view === view);
  });

  const v = VIEWS[view];
  const titleEl   = $('page-title');
  const breadcrEl = $('breadcrumb');
  if (titleEl)   titleEl.textContent   = v.title;
  if (breadcrEl) breadcrEl.textContent = v.breadcrumb;

  const container = $('view-container');
  container.style.opacity = '0';
  container.style.transform = 'translateY(10px)';
  container.innerHTML = `<div class="view-loading"><div class="dot-loader"><span></span><span></span><span></span></div></div>`;

  requestAnimationFrame(() => {
    container.style.transition = 'opacity .3s ease, transform .3s ease';
    container.style.opacity = '1';
    container.style.transform = 'translateY(0)';
  });

  v.render(container);
}

/* Wire nav clicks */
document.querySelectorAll('.nav-item').forEach(n => {
  n.addEventListener('click', e => {
    e.preventDefault();
    navigate(n.dataset.view);
  });
});

/* ================================================================
   MOBILE SIDEBAR
   ================================================================ */
function openSidebar() {
  $('sidebar').classList.add('open');
  $('sidebar-backdrop').classList.add('show');
  $('mobile-menu-btn').classList.add('open');
}

function closeSidebar() {
  $('sidebar').classList.remove('open');
  $('sidebar-backdrop').classList.remove('show');
  $('mobile-menu-btn')?.classList.remove('open');
}

$('mobile-menu-btn')?.addEventListener('click', openSidebar);
$('sidebar-close-btn')?.addEventListener('click', closeSidebar);
$('sidebar-backdrop')?.addEventListener('click', closeSidebar);

/* ================================================================
   CLOCK & API STATUS
   ================================================================ */
function updateClock() {
  const el = $('topbar-time');
  if (el) el.textContent = new Date().toLocaleTimeString('en-IN', {
    hour: '2-digit', minute: '2-digit', second: '2-digit'
  });
}
setInterval(updateClock, 1000);
updateClock();

async function checkApiStatus() {
  const topbarStatus  = $('api-status');
  const sidebarStatus = $('sidebar-api-dot');
  try {
    await apiFetch('/');
    [topbarStatus, sidebarStatus].forEach(el => {
      if (!el) return;
      el.className = el.className.replace('offline', '') + ' online';
      const dot  = el.querySelector('.status-dot, .api-dot');
      const text = el.querySelector('.status-text, .api-label');
      if (text) text.textContent = 'API Online';
    });
  } catch {
    [topbarStatus, sidebarStatus].forEach(el => {
      if (!el) return;
      el.className = el.className.replace('online', '') + ' offline';
      const text = el.querySelector('.status-text, .api-label');
      if (text) text.textContent = 'API Offline';
    });
  }
}
setInterval(checkApiStatus, 15000);
checkApiStatus();

/* ================================================================
   THEME TOGGLE
   ================================================================ */
function initTheme() {
  const stored = localStorage.getItem('cf-theme') || 'dark';
  applyTheme(stored);

  [$('theme-toggle'), $('mobile-theme-toggle')].forEach(btn => {
    btn?.addEventListener('click', () => {
      const current = document.documentElement.getAttribute('data-theme');
      const next = current === 'dark' ? 'light' : 'dark';
      applyTheme(next);
      localStorage.setItem('cf-theme', next);
      toast(`Switched to ${next === 'light' ? 'Light' : 'Dark'} theme`, 'info');
    });
  });
}

function applyTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  const isLight = theme === 'light';

  [$('theme-toggle'), $('mobile-theme-toggle')].forEach(btn => {
    if (!btn) return;
    const sun  = btn.querySelector('.icon-sun');
    const moon = btn.querySelector('.icon-moon');
    if (sun)  sun.style.display  = isLight ? 'none'  : 'block';
    if (moon) moon.style.display = isLight ? 'block' : 'none';
  });
}

/* ================================================================
   DASHBOARD VIEW
   ================================================================ */
async function renderDashboard(container) {
  try {
    const data = await apiFetch('/dashboard/summary');

    const badge = $('followup-badge');
    if (badge) badge.textContent = data.pending_followups_count || 0;

    container.innerHTML = `
      <div class="stats-grid">
        <div class="stat-card indigo">
          <div class="stat-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="4" width="18" height="18" rx="2"/>
              <line x1="16" y1="2" x2="16" y2="6"/>
              <line x1="8"  y1="2" x2="8"  y2="6"/>
              <line x1="3"  y1="10" x2="21" y2="10"/>
            </svg>
          </div>
          <div class="stat-value">${data.today_appointments.length}</div>
          <div class="stat-label">Today's Appointments</div>
        </div>

        <div class="stat-card warning">
          <div class="stat-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
              <polyline points="14,2 14,8 20,8"/>
            </svg>
          </div>
          <div class="stat-value">${data.incomplete_intakes_count}</div>
          <div class="stat-label">Incomplete Intakes</div>
        </div>

        <div class="stat-card violet">
          <div class="stat-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
            </svg>
          </div>
          <div class="stat-value">${data.pending_followups_count}</div>
          <div class="stat-label">Pending Follow-ups</div>
        </div>

        <div class="stat-card success">
          <div class="stat-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
              <circle cx="12" cy="7" r="4"/>
            </svg>
          </div>
          <div class="stat-value">${data.today_appointments.filter(a => a.status === 'confirmed').length}</div>
          <div class="stat-label">Confirmed Today</div>
        </div>
      </div>

      <div class="dash-bottom">
        <div class="card">
          <div class="card-header">
            <div>
              <div class="card-title">Today's Schedule</div>
              <div class="card-subtitle">${new Date().toLocaleDateString('en-IN', { weekday: 'long', day: 'numeric', month: 'long' })}</div>
            </div>
            <button class="btn btn-secondary btn-sm" onclick="navigate('appointments')">View All</button>
          </div>
          ${data.today_appointments.length === 0
            ? `<div class="empty-state">
                <div class="empty-state-icon">📅</div>
                <div class="empty-state-title">No appointments today</div>
              </div>`
            : `<div class="table-wrap"><table>
                <thead><tr>
                  <th>Patient</th><th>Time</th><th>Department</th><th>Status</th><th></th>
                </tr></thead>
                <tbody>
                  ${data.today_appointments.map(a => `
                    <tr>
                      <td class="td-name">${a.patient?.full_name || '—'}</td>
                      <td>${a.appointment_time}</td>
                      <td>${a.department}</td>
                      <td>${badge(a.status)}</td>
                      <td><button class="btn btn-secondary btn-xs" onclick="showAppointmentDetail('${a.appointment_id}')">View</button></td>
                    </tr>`).join('')}
                </tbody>
              </table></div>`}
        </div>

        <div class="card">
          <div class="card-header">
            <div class="card-title">Recent Activity</div>
          </div>
          ${data.recent_audit_logs.length === 0
            ? `<div class="empty-state"><div class="empty-state-icon">📋</div><div class="empty-state-title">No recent activity</div></div>`
            : `<div style="display:flex;flex-direction:column;gap:8px">
                ${data.recent_audit_logs.map(l => `
                  <div class="activity-item">
                    <div class="activity-status">
                      ${l.old_status ? `${l.old_status} → ` : ''}${l.new_status}
                    </div>
                    <div class="activity-meta">by ${l.changed_by} · ${fmtDateTime(l.changed_at)}</div>
                  </div>`).join('')}
              </div>`}
        </div>
      </div>`;
  } catch (e) {
    container.innerHTML = errorState(e.message);
  }
}

/* ================================================================
   APPOINTMENTS VIEW
   ================================================================ */
async function renderAppointments(container) {
  try {
    const appts = await apiFetch('/appointments');
    const statuses = ['all', 'requested', 'confirmed', 'checked_in', 'completed', 'cancelled', 'no_show'];

    container.innerHTML = `
      <div class="section-header">
        <div>
          <div class="section-title">Appointments</div>
          <div class="section-subtitle">${appts.length} total records</div>
        </div>
      </div>
      <div class="filter-bar">
        <div class="search-input-wrap">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
          </svg>
          <input class="form-input" id="appt-search" placeholder="Search patient, clinician, department…" oninput="filterAppointments()"/>
        </div>
        <select class="filter-select" id="appt-status-filter" onchange="filterAppointments()">
          ${statuses.map(s => `<option value="${s}">${s === 'all' ? 'All Statuses' : s.replace(/_/g, ' ')}</option>`).join('')}
        </select>
      </div>
      <div class="card">
        <div class="table-wrap" id="appt-table-wrap">
          ${appointmentsTable(appts)}
        </div>
      </div>`;

    window._appts = appts;
  } catch (e) {
    container.innerHTML = errorState(e.message);
  }
}

function appointmentsTable(appts) {
  if (!appts.length) return emptyState('📅', 'No appointments found');
  return `<table>
    <thead><tr>
      <th>Patient</th><th>Date</th><th>Time</th>
      <th>Clinician</th><th>Department</th><th>Status</th><th>Actions</th>
    </tr></thead>
    <tbody>
      ${appts.map(a => `
        <tr>
          <td class="td-name">${a.patient?.full_name || '—'}</td>
          <td>${fmtDate(a.appointment_date)}</td>
          <td>${a.appointment_time}</td>
          <td>${a.clinician_name || '—'}</td>
          <td>${a.department}</td>
          <td>${badge(a.status)}</td>
          <td style="display:flex;gap:6px;flex-wrap:wrap">
            <button class="btn btn-secondary btn-xs" onclick="showAppointmentDetail('${a.appointment_id}')">View</button>
            <button class="btn btn-xs" style="background:rgba(99,102,241,.12);color:var(--indigo-400)"
              onclick="showStatusChange('${a.appointment_id}','${a.status}')">Status</button>
          </td>
        </tr>`).join('')}
    </tbody></table>`;
}

function filterAppointments() {
  const q  = $('appt-search')?.value.toLowerCase() || '';
  const sf = $('appt-status-filter')?.value || 'all';
  const filtered = (window._appts || []).filter(a => {
    const matchQ = !q
      || (a.patient?.full_name || '').toLowerCase().includes(q)
      || (a.clinician_name || '').toLowerCase().includes(q)
      || (a.department || '').toLowerCase().includes(q);
    const matchS = sf === 'all' || a.status === sf;
    return matchQ && matchS;
  });
  $('appt-table-wrap').innerHTML = appointmentsTable(filtered);
}

async function showAppointmentDetail(apptId) {
  try {
    const [a, intakeForms] = await Promise.all([
      apiFetch(`/appointments/${apptId}`),
      apiFetch(`/appointments/${apptId}/intake`).catch(() => [])
    ]);
    const intake = Array.isArray(intakeForms) ? intakeForms[0] : intakeForms;

    showModal(`Appointment — ${a.patient?.full_name || ''}`, `
      <div class="detail-row"><span class="detail-key">Date & Time</span><span class="detail-val">${fmtDate(a.appointment_date)} at ${a.appointment_time}</span></div>
      <div class="detail-row"><span class="detail-key">Clinician</span><span class="detail-val">${a.clinician_name || '—'}</span></div>
      <div class="detail-row"><span class="detail-key">Department</span><span class="detail-val">${a.department}</span></div>
      <div class="detail-row"><span class="detail-key">Status</span><span class="detail-val">${badge(a.status)}</span></div>
      <div class="detail-row"><span class="detail-key">Reason</span><span class="detail-val">${a.reason_for_visit || '—'}</span></div>
      ${intake ? `
        <div style="margin-top:16px">
          <div class="card-title mb-16">Intake Summary</div>
          ${intake.urgent_review_needed ? urgentBanner() : ''}
          ${progressBar(intake.completeness_score)}
          ${intake.ai_summary ? aiBlock(intake.ai_summary) : `
            <div class="mt-12">
              <button class="btn btn-secondary btn-sm" onclick="runSummarize('${intake.intake_id}')">Generate AI Summary</button>
            </div>`}
          ${intake.missing_fields?.length ? `<div class="mt-12 text-sm text-muted">Missing: ${intake.missing_fields.map(f => `<span class="badge badge-draft">${f}</span>`).join(' ')}</div>` : ''}
        </div>` : `<div class="mt-16 text-muted text-sm">No intake form submitted yet.</div>`}
    `);
  } catch (e) {
    toast(e.message, 'error');
  }
}

async function showStatusChange(apptId, currentStatus) {
  const statuses = ['requested', 'confirmed', 'checked_in', 'completed', 'cancelled', 'no_show'];
  showModal('Update Appointment Status', `
    <div class="form-group">
      <label class="form-label">New Status</label>
      <select class="form-select" id="new-status-sel">
        ${statuses.map(s => `<option value="${s}" ${s === currentStatus ? 'selected' : ''}>${s.replace(/_/g, ' ')}</option>`).join('')}
      </select>
    </div>
    <div class="form-group">
      <label class="form-label">Changed By</label>
      <input class="form-input" id="changed-by-inp" value="staff" />
    </div>
    <div style="display:flex;gap:10px;justify-content:flex-end;margin-top:16px">
      <button class="btn btn-secondary" onclick="closeModal()">Cancel</button>
      <button class="btn btn-primary" onclick="submitStatusChange('${apptId}')">Update Status</button>
    </div>
  `);
}

async function submitStatusChange(apptId) {
  try {
    const status     = $('new-status-sel').value;
    const changed_by = $('changed-by-inp').value || 'staff';
    await apiFetch(`/appointments/${apptId}/status`, {
      method: 'PATCH',
      body: JSON.stringify({ status, changed_by })
    });
    closeModal();
    toast('Status updated', 'success');
    navigate('appointments');
  } catch (e) { toast(e.message, 'error'); }
}

/* ================================================================
   INTAKE FORMS VIEW
   ================================================================ */
async function renderIntakes(container) {
  try {
    const intakes = await apiFetch('/intake-forms');

    container.innerHTML = `
      <div class="section-header">
        <div>
          <div class="section-title">Intake Forms</div>
          <div class="section-subtitle">${intakes.length} total forms</div>
        </div>
      </div>
      <div class="filter-bar">
        <div class="search-input-wrap">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
          </svg>
          <input class="form-input" id="intake-search" placeholder="Search symptoms, language…" oninput="filterIntakes()"/>
        </div>
        <select class="filter-select" id="intake-filter" onchange="filterIntakes()">
          <option value="all">All</option>
          <option value="complete">Complete (≥ 80%)</option>
          <option value="incomplete">Incomplete</option>
          <option value="urgent">Urgent Review</option>
        </select>
      </div>
      <div class="card">
        <div class="table-wrap" id="intake-table-wrap">
          ${intakesTable(intakes)}
        </div>
      </div>`;

    window._intakes = intakes;
  } catch (e) {
    container.innerHTML = errorState(e.message);
  }
}

function intakesTable(intakes) {
  if (!intakes.length) return emptyState('📄', 'No intake forms found');
  return `<table>
    <thead><tr>
      <th>ID</th><th>Completeness</th><th>Missing Fields</th>
      <th>AI Summary</th><th>Urgent</th><th>Submitted</th><th>Actions</th>
    </tr></thead>
    <tbody>
      ${intakes.map(i => `
        <tr>
          <td style="font-family:monospace;font-size:.72rem;color:var(--text-muted)">${i.intake_id.substring(0, 8)}…</td>
          <td style="min-width:150px">${progressBar(i.completeness_score)}</td>
          <td>${i.missing_fields?.length
            ? i.missing_fields.map(f => `<span class="badge badge-draft">${f}</span>`).join(' ')
            : '<span class="badge badge-confirmed">Complete</span>'}</td>
          <td>${i.ai_summary ? '<span class="badge badge-ai">✓ AI</span>' : '<span class="text-muted text-xs">—</span>'}</td>
          <td>${i.urgent_review_needed ? '<span class="badge badge-urgent">⚠ Urgent</span>' : '—'}</td>
          <td class="text-sm text-muted">${fmtDateTime(i.submitted_at)}</td>
          <td style="display:flex;gap:6px;flex-wrap:wrap">
            <button class="btn btn-secondary btn-xs" onclick="showIntakeDetail('${i.intake_id}')">View</button>
            ${!i.ai_summary ? `<button class="btn btn-xs" style="background:rgba(139,92,246,.12);color:var(--violet-400)" onclick="runSummarize('${i.intake_id}')">Summarize</button>` : ''}
          </td>
        </tr>`).join('')}
    </tbody></table>`;
}

function filterIntakes() {
  const q  = $('intake-search')?.value.toLowerCase() || '';
  const f  = $('intake-filter')?.value || 'all';
  const filtered = (window._intakes || []).filter(i => {
    const matchQ = !q || (i.symptoms_description || '').toLowerCase().includes(q)
      || (i.preferred_language || '').toLowerCase().includes(q);
    const pct = (i.completeness_score || 0) * 100;
    const matchF = f === 'all'
      || (f === 'complete'   && pct >= 80)
      || (f === 'incomplete' && pct < 80)
      || (f === 'urgent'     && i.urgent_review_needed);
    return matchQ && matchF;
  });
  $('intake-table-wrap').innerHTML = intakesTable(filtered);
}

async function showIntakeDetail(intakeId) {
  try {
    const i = await apiFetch(`/intake-forms/${intakeId}`);
    showModal('Intake Form Details', `
      ${i.urgent_review_needed ? urgentBanner() : ''}
      <div class="detail-row"><span class="detail-key">Completeness</span><span class="detail-val" style="flex:1">${progressBar(i.completeness_score)}</span></div>
      <div class="detail-row"><span class="detail-key">Symptoms</span><span class="detail-val">${i.symptoms_description || '—'}</span></div>
      <div class="detail-row"><span class="detail-key">Medications</span><span class="detail-val">${i.current_medications || '—'}</span></div>
      <div class="detail-row"><span class="detail-key">Allergies</span><span class="detail-val">${i.allergies || '—'}</span></div>
      <div class="detail-row"><span class="detail-key">Insurance</span><span class="detail-val">${i.insurance_provider || '—'} ${i.insurance_id ? `(${i.insurance_id})` : ''}</span></div>
      <div class="detail-row"><span class="detail-key">Language</span><span class="detail-val">${i.preferred_language || '—'}</span></div>
      <div class="detail-row"><span class="detail-key">Missing</span><span class="detail-val">${i.missing_fields?.length ? i.missing_fields.map(f => `<span class="badge badge-draft">${f}</span>`).join(' ') : 'None'}</span></div>
      <div class="detail-row"><span class="detail-key">Submitted</span><span class="detail-val">${fmtDateTime(i.submitted_at)}</span></div>
      ${i.ai_summary
        ? aiBlock(i.ai_summary)
        : `<div class="mt-16" style="display:flex;gap:10px;align-items:center">
            <button class="btn btn-secondary" onclick="runSummarize('${i.intake_id}')">Generate AI Summary</button>
            <span class="text-xs text-muted">Uses Gemma / Claude with safety guardrails</span>
          </div>`}
    `);
  } catch (e) { toast(e.message, 'error'); }
}

async function runSummarize(intakeId) {
  try {
    toast('Generating AI summary…', 'info');
    closeModal();
    await apiFetch(`/intake-forms/${intakeId}/summarize`, { method: 'POST' });
    toast('AI summary generated successfully', 'success');
    navigate('intakes');
  } catch (e) { toast(e.message, 'error'); }
}

/* ================================================================
   FOLLOW-UPS VIEW
   ================================================================ */
async function renderFollowups(container) {
  try {
    const fups = await apiFetch('/followups');
    const badge = $('followup-badge');
    if (badge) badge.textContent = fups.filter(f => f.status === 'draft').length;

    container.innerHTML = `
      <div class="section-header">
        <div>
          <div class="section-title">Follow-up Messages</div>
          <div class="section-subtitle">Review, edit and approve AI-drafted follow-ups</div>
        </div>
      </div>
      <div class="filter-bar">
        <select class="filter-select" id="fup-filter" onchange="filterFollowups()">
          <option value="all">All Statuses</option>
          <option value="draft">Draft</option>
          <option value="approved">Approved</option>
          <option value="sent">Sent</option>
        </select>
      </div>
      <div class="card">
        <div class="table-wrap" id="fup-table-wrap">
          ${followupsTable(fups)}
        </div>
      </div>`;

    window._fups = fups;
  } catch (e) {
    container.innerHTML = errorState(e.message);
  }
}

function followupsTable(fups) {
  if (!fups.length) return emptyState('💬', 'No follow-ups found');
  return `<table>
    <thead><tr><th>Patient</th><th>Type</th><th>Status</th><th>Draft Preview</th><th>Actions</th></tr></thead>
    <tbody>
      ${fups.map(f => `
        <tr>
          <td class="td-name">${f.patient?.full_name || '—'}</td>
          <td><span class="text-sm text-muted">${(f.followup_type || '').replace(/_/g, ' ')}</span></td>
          <td>${badge(f.status)}</td>
          <td style="max-width:230px">
            <span style="font-size:.78rem;color:var(--text-muted);display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">
              ${f.message_draft ? f.message_draft.substring(0, 90) + '…' : '—'}
            </span>
          </td>
          <td style="display:flex;gap:6px;flex-wrap:wrap">
            <button class="btn btn-secondary btn-xs" onclick="showFollowupDetail('${f.followup_id}')">Review</button>
            ${f.status === 'draft' ? `<button class="btn btn-success btn-xs" onclick="approveFollowup('${f.followup_id}')">Approve</button>` : ''}
          </td>
        </tr>`).join('')}
    </tbody></table>`;
}

function filterFollowups() {
  const s = $('fup-filter')?.value || 'all';
  const filtered = (window._fups || []).filter(f => s === 'all' || f.status === s);
  $('fup-table-wrap').innerHTML = followupsTable(filtered);
}

async function showFollowupDetail(fupId) {
  const f = (window._fups || []).find(x => x.followup_id === fupId);
  if (!f) return;
  showModal(`Follow-up — ${f.patient?.full_name || ''}`, `
    <div class="detail-row"><span class="detail-key">Type</span><span class="detail-val">${(f.followup_type || '').replace(/_/g, ' ')}</span></div>
    <div class="detail-row"><span class="detail-key">Status</span><span class="detail-val">${badge(f.status)}</span></div>
    <div class="form-group mt-16">
      <label class="form-label">Message Draft <span class="badge badge-ai" style="margin-left:6px">AI-Drafted</span></label>
      <div style="font-size:.72rem;color:var(--text-muted);margin-bottom:8px">⚠ Review carefully before approving. This is administrative only — not a clinical message.</div>
      <textarea class="form-textarea" id="fup-draft-${fupId}" rows="6">${f.message_draft || ''}</textarea>
    </div>
    <div style="display:flex;gap:10px;justify-content:flex-end;margin-top:12px">
      <button class="btn btn-secondary" onclick="closeModal()">Close</button>
      ${f.status === 'draft'    ? `<button class="btn btn-primary" onclick="submitFollowupApproval('${fupId}','approved')">Approve & Send</button>` : ''}
      ${f.status === 'approved' ? `<button class="btn btn-success" onclick="submitFollowupApproval('${fupId}','sent')">Mark as Sent</button>` : ''}
    </div>
  `);
}

async function approveFollowup(fupId) {
  await submitFollowupApproval(fupId, 'approved');
}

async function submitFollowupApproval(fupId, newStatus) {
  try {
    const draftEl = $(`fup-draft-${fupId}`);
    await apiFetch(`/followups/${fupId}/status`, {
      method: 'PATCH',
      body: JSON.stringify({ status: newStatus, message_draft: draftEl?.value })
    });
    closeModal();
    toast(`Follow-up ${newStatus}`, 'success');
    navigate('followups');
  } catch (e) { toast(e.message, 'error'); }
}

/* ================================================================
   PATIENTS VIEW
   ================================================================ */
async function renderPatients(container) {
  try {
    const patients = await apiFetch('/patients');

    container.innerHTML = `
      <div class="section-header">
        <div>
          <div class="section-title">Patients</div>
          <div class="section-subtitle">${patients.length} registered patients</div>
        </div>
      </div>
      <div class="filter-bar">
        <div class="search-input-wrap">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
          </svg>
          <input class="form-input" id="patient-search" placeholder="Search by name, email, phone…" oninput="filterPatients()"/>
        </div>
      </div>
      <div class="card">
        <div class="table-wrap" id="patient-table-wrap">
          ${patientsTable(patients)}
        </div>
      </div>`;

    window._patients = patients;
  } catch (e) {
    container.innerHTML = errorState(e.message);
  }
}

function patientsTable(patients) {
  if (!patients.length) return emptyState('👤', 'No patients found');
  return `<table>
    <thead><tr><th>Name</th><th>DOB</th><th>Gender</th><th>Phone</th><th>Email</th><th>Registered</th></tr></thead>
    <tbody>
      ${patients.map(p => `
        <tr>
          <td class="td-name">${p.full_name}</td>
          <td>${fmtDate(p.dob)}</td>
          <td>${p.gender || '—'}</td>
          <td>${p.phone}</td>
          <td style="font-size:.82rem">${p.email}</td>
          <td class="text-sm text-muted">${fmtDateTime(p.created_at)}</td>
        </tr>`).join('')}
    </tbody></table>`;
}

function filterPatients() {
  const q = $('patient-search')?.value.toLowerCase() || '';
  const filtered = (window._patients || []).filter(p =>
    !q ||
    p.full_name.toLowerCase().includes(q) ||
    (p.email || '').toLowerCase().includes(q) ||
    (p.phone || '').includes(q)
  );
  $('patient-table-wrap').innerHTML = patientsTable(filtered);
}

/* ================================================================
   BOOK APPOINTMENT & INTAKE (Patient Portal)
   ================================================================ */
async function renderBook(container) {
  const today = new Date().toISOString().split('T')[0];

  container.innerHTML = `
    <div class="book-wrapper">
      <div class="section-header">
        <div>
          <div class="section-title">Book Appointment</div>
          <div class="section-subtitle">Fill in your details — we'll register your appointment and intake in one step.</div>
        </div>
      </div>

      <div class="card">
        <div class="book-info-banner">
          AI is used solely to generate <strong>administrative summaries</strong> for front-desk triage support.
          It is <strong>never used for clinical diagnosis or prescriptions</strong>.
        </div>

        <!-- Section 1 -->
        <div class="book-section-title">1 · Patient Demographics</div>
        <div class="form-row">
          <div class="form-group">
            <label class="form-label">Full Name <span class="required">*</span></label>
            <input class="form-input" id="book-name" placeholder="e.g. Priya Sharma" autocomplete="name" />
          </div>
          <div class="form-group">
            <label class="form-label">Date of Birth <span class="required">*</span></label>
            <input class="form-input" id="book-dob" type="date" />
          </div>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label class="form-label">Phone <span class="required">*</span></label>
            <input class="form-input" id="book-phone" placeholder="e.g. 555-0123" type="tel" autocomplete="tel" />
          </div>
          <div class="form-group">
            <label class="form-label">Email <span class="required">*</span></label>
            <input class="form-input" id="book-email" type="email" placeholder="you@example.com" autocomplete="email" />
          </div>
        </div>

        <!-- Section 2 -->
        <div class="book-section-title">2 · Appointment Slot</div>
        <div class="form-row">
          <div class="form-group">
            <label class="form-label">Department <span class="required">*</span></label>
            <select class="form-select" id="book-dept">
              <option>General Practice</option>
              <option>Pediatrics</option>
              <option>Cardiology</option>
              <option>Orthopedics</option>
              <option>Neurology</option>
              <option>Dermatology</option>
              <option>Gynecology</option>
              <option>Ophthalmology</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">Preferred Date <span class="required">*</span></label>
            <input class="form-input" id="book-date" type="date" min="${today}" />
          </div>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label class="form-label">Preferred Time <span class="required">*</span></label>
            <select class="form-select" id="book-time">
              ${['08:00','09:00','10:00','11:00','12:00','14:00','15:00','16:00','17:00']
                .map(t => `<option value="${t}">${t}</option>`).join('')}
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">Clinician (Optional)</label>
            <input class="form-input" id="book-clinician" placeholder="e.g. Dr. Osei" />
          </div>
        </div>

        <!-- Section 3 -->
        <div class="book-section-title">3 · Intake Information</div>
        <div class="form-group">
          <label class="form-label">Symptoms / Reason for Visit <span class="required">*</span></label>
          <textarea class="form-textarea" id="book-symptoms" rows="3"
            placeholder="Describe your symptoms or reason for visiting in your own words…"></textarea>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label class="form-label">Current Medications</label>
            <input class="form-input" id="book-meds" placeholder="e.g. Lisinopril 10mg, or 'None'" />
          </div>
          <div class="form-group">
            <label class="form-label">Allergies</label>
            <input class="form-input" id="book-allergies" placeholder="e.g. Penicillin, or 'None'" />
          </div>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label class="form-label">Insurance Provider</label>
            <input class="form-input" id="book-ins-prov" placeholder="e.g. Aetna" />
          </div>
          <div class="form-group">
            <label class="form-label">Insurance ID</label>
            <input class="form-input" id="book-ins-id" placeholder="Policy / Member number" />
          </div>
        </div>
        <div class="form-group">
          <label class="form-label">Preferred Language</label>
          <select class="form-select" id="book-lang">
            <option>English</option><option>Spanish</option><option>French</option>
            <option>Hindi</option><option>Vietnamese</option><option>Arabic</option>
          </select>
        </div>

        <!-- Section 4: Consent -->
        <div class="book-section-title">4 · AI Consent</div>
        <div class="form-group">
          <div class="checkbox-group">
            <input type="checkbox" id="book-consent" />
            <label class="checkbox-label" for="book-consent">
              I consent to having my intake details summarized by AI for <strong>administrative front-desk support only</strong>.
              I understand this will <strong>never</strong> be used for medical diagnosis or treatment decisions.
              <span class="required">*</span>
            </label>
          </div>
        </div>

        <button class="btn btn-primary btn-lg w-full mt-16" id="book-submit-btn" onclick="submitCombinedBooking()">
          Book Appointment &amp; Submit Intake
        </button>
      </div>
    </div>`;
}

async function submitCombinedBooking() {
  const btn = $('book-submit-btn');
  btn.disabled = true;
  btn.textContent = 'Processing…';

  try {
    const full_name  = $('book-name')?.value?.trim();
    const dob        = $('book-dob')?.value;
    const phone      = $('book-phone')?.value?.trim();
    const email      = $('book-email')?.value?.trim();
    const dept       = $('book-dept')?.value;
    const date       = $('book-date')?.value;
    const time       = $('book-time')?.value;
    const clinician  = $('book-clinician')?.value?.trim() || 'To be assigned';
    const symptoms   = $('book-symptoms')?.value?.trim();
    const meds       = $('book-meds')?.value?.trim()        || '';
    const allergies  = $('book-allergies')?.value?.trim()   || '';
    const insProv    = $('book-ins-prov')?.value?.trim()    || '';
    const insId      = $('book-ins-id')?.value?.trim()      || '';
    const lang       = $('book-lang')?.value                || 'English';
    const consent    = $('book-consent')?.checked;

    if (!full_name || !dob || !phone || !email || !date || !symptoms) {
      toast('Please fill in all required fields (*)', 'error');
      btn.disabled = false;
      btn.textContent = 'Book Appointment & Submit Intake';
      return;
    }
    if (!consent) {
      toast('AI consent is required to submit the intake form', 'error');
      btn.disabled = false;
      btn.textContent = 'Book Appointment & Submit Intake';
      return;
    }

    const payload = {
      full_name, dob, phone, email,
      department: dept,
      appointment_date: date,
      appointment_time: time,
      clinician_name: clinician,
      symptoms_description: symptoms,
      current_medications: meds,
      allergies, insurance_provider: insProv,
      insurance_id: insId, preferred_language: lang,
      consent_given: true
    };

    const appt = await apiFetch('/appointments/book-with-intake', {
      method: 'POST',
      body: JSON.stringify(payload)
    });

    toast('Appointment booked successfully!', 'success');

    /* Background AI summarization for staff dashboard */
    apiFetch(`/appointments/${appt.appointment_id}/intake`)
      .then(forms => {
        const id = Array.isArray(forms) ? forms[0]?.intake_id : forms?.intake_id;
        if (id) apiFetch(`/intake-forms/${id}/summarize`, { method: 'POST' }).catch(() => {});
      })
      .catch(() => {});

    /* Success screen */
    $('view-container').innerHTML = `
      <div class="book-success-wrap">
        <div class="book-success-icon">🎉</div>
        <h2 class="book-success-title">Booking Confirmed!</h2>
        <p class="book-success-desc">Thank you, <strong>${appt.patient?.full_name || full_name}</strong>. Your appointment has been registered. Our staff will review your intake and send a confirmation shortly.</p>
        <div class="card" style="text-align:left;gap:0">
          <div class="detail-row"><span class="detail-key">Department</span><span class="detail-val">${appt.department}</span></div>
          <div class="detail-row"><span class="detail-key">Date & Time</span><span class="detail-val">${fmtDate(appt.appointment_date)} at ${appt.appointment_time}</span></div>
          <div class="detail-row"><span class="detail-key">Status</span><span class="detail-val">${badge(appt.status)}</span></div>
          <div class="detail-row"><span class="detail-key">Clinician</span><span class="detail-val">${appt.clinician_name || 'To be assigned'}</span></div>
        </div>
        <button class="btn btn-primary btn-lg w-full mt-24" onclick="navigate('book')">Book Another Appointment</button>
      </div>`;

  } catch (e) {
    toast(e.message, 'error');
    btn.disabled = false;
    btn.textContent = 'Book Appointment & Submit Intake';
  }
}

/* ================================================================
   SHARED COMPONENT HELPERS
   ================================================================ */
function urgentBanner() {
  return `<div class="urgent-banner">
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
      <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
      <line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>
    </svg>
    URGENT CLINICAL REVIEW REQUIRED
  </div>`;
}

function aiBlock(summary) {
  return `<div class="ai-block mt-16">
    <div class="ai-block-header">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="10"/><path d="M12 8v4l3 3"/>
      </svg>
      <span class="ai-block-label">AI Administrative Summary</span>
      <span class="ai-block-disclaimer">⚠ Not a clinical judgment</span>
    </div>
    <div class="ai-block-content">${summary}</div>
  </div>`;
}

function emptyState(icon, title, desc = '') {
  return `<div class="empty-state">
    <div class="empty-state-icon">${icon}</div>
    <div class="empty-state-title">${title}</div>
    ${desc ? `<div class="empty-state-desc">${desc}</div>` : ''}
  </div>`;
}

function errorState(msg) {
  return `<div class="empty-state">
    <div class="empty-state-icon">⚠️</div>
    <div class="empty-state-title">Failed to load</div>
    <div class="empty-state-desc">${msg}</div>
  </div>`;
}

/* ================================================================
   BOOT SEQUENCE
   ================================================================ */
window.addEventListener('load', () => {
  initTheme();
  checkApiStatus();

  /* Hide splash and reveal app */
  setTimeout(() => {
    const splash   = $('splash');
    const appShell = $('app-shell');

    splash?.classList.add('hide');
    if (appShell) {
      appShell.hidden = false;
      appShell.style.opacity = '0';
      appShell.style.transition = 'opacity .4s ease';
      requestAnimationFrame(() => { appShell.style.opacity = '1'; });
    }
    setTimeout(() => splash?.remove(), 520);

    navigate('dashboard');
  }, 900);
});
