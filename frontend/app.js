/* ============================================================
   ClinicFlow — Combined Patient Portal SPA JavaScript
   ============================================================ */

const API = 'https://clinic-appointment-system-o71t.onrender.com';

/* ============================================================
   UTILITIES
   ============================================================ */
function el(id) { return document.getElementById(id); }

function toast(msg, type = 'info') {
  const c = el('toast-container');
  if (!c) return;
  const t = document.createElement('div');
  const icons = { success: '✓', error: '✕', info: 'ℹ', warning: '⚠' };
  t.className = `toast ${type}`;
  t.innerHTML = `<span style="font-size:1rem;font-weight:800;">${icons[type]||'ℹ'}</span> ${msg}`;
  c.appendChild(t);
  setTimeout(() => {
    t.style.opacity = '0';
    t.style.transform = 'translateY(10px)';
    t.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
    setTimeout(() => t.remove(), 300);
  }, 4000);
}

function showModal(title, bodyHTML) {
  el('modal-title').textContent = title;
  el('modal-body').innerHTML = bodyHTML;
  el('modal-overlay').classList.add('open');
}

function closeModal() {
  el('modal-overlay').classList.remove('open');
}

function fmtDate(d) {
  if (!d) return '—';
  const dt = new Date(d);
  if (isNaN(dt)) return d;
  return dt.toLocaleDateString('en-IN', { day:'2-digit', month:'short', year:'numeric' });
}

function fmtDateTime(d) {
  if (!d) return '—';
  const dt = new Date(d);
  if (isNaN(dt)) return d;
  return dt.toLocaleString('en-IN', { day:'2-digit', month:'short', hour:'2-digit', minute:'2-digit' });
}

function badge(status) {
  const s = (status || '').toLowerCase().replace(' ','_');
  return `<span class="badge badge-${s}">${status || '—'}</span>`;
}

function progressBar(score) {
  const pct = Math.round(score * 100);
  const cls = pct >= 80 ? 'high' : pct >= 50 ? 'medium' : 'low';
  return `
    <div class="progress-bar-wrap">
      <div class="progress-bar">
        <div class="progress-fill ${cls}" style="width:${pct}%"></div>
      </div>
      <span class="progress-pct">${pct}%</span>
    </div>`;
}

async function apiFetch(path, opts = {}) {
  const res = await fetch(API + path, {
    headers: { 'Content-Type': 'application/json', ...(opts.headers || {}) },
    ...opts
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Request failed');
  }
  return res.status === 204 ? null : res.json();
}

/* ============================================================
   NAVIGATION
   ============================================================ */
const VIEWS = {
  dashboard: { title: 'Dashboard', breadcrumb: 'Overview', render: renderDashboard },
  appointments: { title: 'Appointments', breadcrumb: 'Staff Portal', render: renderAppointments },
  intakes: { title: 'Intake Forms', breadcrumb: 'Staff Portal', render: renderIntakes },
  followups: { title: 'Follow-ups', breadcrumb: 'Staff Portal', render: renderFollowups },
  patients: { title: 'Patients', breadcrumb: 'Staff Portal', render: renderPatients },
  book: { title: 'Book Appointment & Intake', breadcrumb: 'Patient Portal', render: renderBook },
};

let currentView = 'dashboard';

function navigate(view) {
  if (!VIEWS[view]) return;
  currentView = view;

  // Update nav items
  document.querySelectorAll('.nav-item').forEach(n => {
    n.classList.toggle('active', n.dataset.view === view);
  });

  const v = VIEWS[view];
  el('page-title').textContent = v.title;
  el('breadcrumb').textContent = v.breadcrumb;

  const container = el('view-container');
  container.innerHTML = '<div class="loading-spinner"><div class="spinner"></div></div>';

  v.render(container);
}

document.querySelectorAll('.nav-item').forEach(n => {
  n.addEventListener('click', e => {
    e.preventDefault();
    navigate(n.dataset.view);
  });
});

/* ============================================================
   CLOCK & API STATUS
   ============================================================ */
function updateClock() {
  const now = new Date();
  const timeEl = el('topbar-time');
  if (timeEl) {
    timeEl.textContent = now.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  }
}
setInterval(updateClock, 1000);
updateClock();

async function checkApiStatus() {
  const ind = el('api-status');
  if (!ind) return;
  try {
    await apiFetch('/');
    ind.className = 'status-indicator online';
    ind.querySelector('.status-text').textContent = 'API Online';
  } catch {
    ind.className = 'status-indicator offline';
    ind.querySelector('.status-text').textContent = 'API Offline';
  }
}
setInterval(checkApiStatus, 15000);
checkApiStatus();

/* ============================================================
   THEME TOGGLING (Light / Dark)
   ============================================================ */
function initTheme() {
  const themeToggle = el('theme-toggle');
  if (!themeToggle) return;

  const currentTheme = localStorage.getItem('theme') || 'dark';
  if (currentTheme === 'light') {
    document.body.classList.add('light-theme');
    themeToggle.querySelector('.sun-icon').style.display = 'none';
    themeToggle.querySelector('.moon-icon').style.display = 'block';
  }

  themeToggle.addEventListener('click', () => {
    const isLight = document.body.classList.toggle('light-theme');
    localStorage.setItem('theme', isLight ? 'light' : 'dark');
    themeToggle.querySelector('.sun-icon').style.display = isLight ? 'none' : 'block';
    themeToggle.querySelector('.moon-icon').style.display = isLight ? 'block' : 'none';
    toast(`Switched to ${isLight ? 'Light' : 'Dark'} theme`, 'info');
  });
}

/* ============================================================
   DASHBOARD VIEW
   ============================================================ */
async function renderDashboard(container) {
  try {
    const data = await apiFetch('/dashboard/summary');

    // Update badge
    const badgeEl = el('followup-badge');
    if (badgeEl) badgeEl.textContent = data.pending_followups_count || 0;

    container.innerHTML = `
      <div class="stats-grid">
        <div class="stat-card indigo">
          <div class="stat-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
          </div>
          <div class="stat-value">${data.today_appointments.length}</div>
          <div class="stat-label">Today's Appointments</div>
        </div>
        <div class="stat-card warning">
          <div class="stat-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14,2 14,8 20,8"/></svg>
          </div>
          <div class="stat-value">${data.incomplete_intakes_count}</div>
          <div class="stat-label">Incomplete Intakes</div>
        </div>
        <div class="stat-card violet">
          <div class="stat-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
          </div>
          <div class="stat-value">${data.pending_followups_count}</div>
          <div class="stat-label">Pending Follow-ups</div>
        </div>
        <div class="stat-card success">
          <div class="stat-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
          </div>
          <div class="stat-value">${data.today_appointments.filter(a=>a.status==='confirmed').length}</div>
          <div class="stat-label">Confirmed Today</div>
        </div>
      </div>

      <div class="dash-bottom">
        <div class="card">
          <div class="card-header">
            <div>
              <div class="card-title">Today's Appointments</div>
              <div class="card-subtitle">${new Date().toLocaleDateString('en-IN',{weekday:'long',day:'numeric',month:'long'})}</div>
            </div>
            <button class="btn btn-primary btn-sm" onclick="navigate('appointments')">View All</button>
          </div>
          ${data.today_appointments.length === 0
            ? `<div class="empty-state"><div class="empty-state-icon">📅</div><div class="empty-state-title">No appointments today</div></div>`
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
              </tbody></table></div>`}
        </div>

        <div class="card">
          <div class="card-header">
            <div class="card-title">Recent Activity</div>
          </div>
          ${data.recent_audit_logs.length === 0
            ? `<div class="empty-state"><div class="empty-state-icon">📋</div><div class="empty-state-title">No recent activity</div></div>`
            : `<div style="display:flex;flex-direction:column;gap:10px;">
              ${data.recent_audit_logs.map(l => `
                <div style="display:flex;flex-direction:column;gap:3px;padding:10px;background:var(--input-bg);border-radius:var(--radius-sm);border:1px solid var(--border-color);">
                  <div style="font-size:.78rem;font-weight:600;color:var(--text-bright);">
                    ${l.old_status ? `${l.old_status} → ` : ''}${l.new_status}
                  </div>
                  <div style="font-size:.72rem;color:var(--text-muted);">by ${l.changed_by} · ${fmtDateTime(l.changed_at)}</div>
                </div>`).join('')}
            </div>`}
        </div>
      </div>`;
  } catch (e) {
    container.innerHTML = `<div class="empty-state"><div class="empty-state-icon">⚠️</div><div class="empty-state-title">Failed to load dashboard</div><div class="empty-state-desc">${e.message}</div></div>`;
  }
}

/* ============================================================
   APPOINTMENTS VIEW
   ============================================================ */
async function renderAppointments(container) {
  try {
    const appts = await apiFetch('/appointments');
    const statuses = ['all', 'requested', 'confirmed', 'checked_in', 'completed', 'cancelled', 'no_show'];

    container.innerHTML = `
      <div class="section-header">
        <div>
          <div class="section-title">All Appointments</div>
          <div class="section-subtitle">${appts.length} total appointments</div>
        </div>
      </div>
      <div class="filter-bar">
        <div class="search-input-wrap">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
          <input type="text" id="appt-search" placeholder="Search by patient, clinician, department…" oninput="filterAppointments()"/>
        </div>
        <select class="filter-select" id="appt-status-filter" onchange="filterAppointments()">
          ${statuses.map(s => `<option value="${s}">${s === 'all' ? 'All Statuses' : s.replace('_',' ')}</option>`).join('')}
        </select>
      </div>
      <div class="card">
        <div class="table-wrap" id="appt-table-wrap">
          ${renderAppointmentsTable(appts)}
        </div>
      </div>`;

    window._allAppointments = appts;
  } catch (e) {
    container.innerHTML = `<div class="empty-state"><div class="empty-state-icon">⚠️</div><div class="empty-state-title">${e.message}</div></div>`;
  }
}

function renderAppointmentsTable(appts) {
  if (!appts.length) return `<div class="empty-state"><div class="empty-state-icon">📅</div><div class="empty-state-title">No appointments found</div></div>`;
  return `<table>
    <thead><tr>
      <th>Patient</th><th>Date</th><th>Time</th><th>Clinician</th><th>Department</th><th>Status</th><th>Actions</th>
    </tr></thead>
    <tbody>
      ${appts.map(a => `
        <tr>
          <td class="td-name">${a.patient?.full_name || '—'}</td>
          <td>${fmtDate(a.appointment_date)}</td>
          <td>${a.appointment_time}</td>
          <td>${a.clinician_name}</td>
          <td>${a.department}</td>
          <td>${badge(a.status)}</td>
          <td style="display:flex;gap:6px;">
            <button class="btn btn-secondary btn-xs" onclick="showAppointmentDetail('${a.appointment_id}')">View</button>
            <button class="btn btn-xs" style="background:rgba(99,102,241,.15);color:var(--indigo-500);" onclick="showStatusChange('${a.appointment_id}','${a.status}')">Status</button>
          </td>
        </tr>`).join('')}
    </tbody></table>`;
}

function filterAppointments() {
  const q = el('appt-search')?.value.toLowerCase() || '';
  const s = el('appt-status-filter')?.value || 'all';
  const filtered = (window._allAppointments || []).filter(a => {
    const matchSearch = !q ||
      (a.patient?.full_name||'').toLowerCase().includes(q) ||
      a.clinician_name.toLowerCase().includes(q) ||
      a.department.toLowerCase().includes(q);
    const matchStatus = s === 'all' || a.status === s;
    return matchSearch && matchStatus;
  });
  el('appt-table-wrap').innerHTML = renderAppointmentsTable(filtered);
}

async function showAppointmentDetail(apptId) {
  try {
    const a = await apiFetch(`/appointments/${apptId}`);
    const intakeForms = await apiFetch(`/appointments/${apptId}/intake`).catch(() => null);
    const intake = Array.isArray(intakeForms) ? intakeForms[0] : intakeForms;

    showModal(`Appointment — ${a.patient?.full_name || ''}`, `
      <div class="detail-row"><span class="detail-key">Date & Time</span><span class="detail-val">${fmtDate(a.appointment_date)} at ${a.appointment_time}</span></div>
      <div class="detail-row"><span class="detail-key">Clinician</span><span class="detail-val">${a.clinician_name}</span></div>
      <div class="detail-row"><span class="detail-key">Department</span><span class="detail-val">${a.department}</span></div>
      <div class="detail-row"><span class="detail-key">Status</span><span class="detail-val">${badge(a.status)}</span></div>
      <div class="detail-row"><span class="detail-key">Reason</span><span class="detail-val">${a.reason_for_visit}</span></div>
      ${intake ? `
        <div class="mt-16">
          <div class="card-title mb-16">Intake Summary</div>
          ${intake.urgent_review_needed ? `<div class="urgent-banner"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>URGENT CLINICAL REVIEW REQUIRED</div>` : ''}
          ${progressBar(intake.completeness_score)}
          ${intake.ai_summary ? `
            <div class="ai-block mt-12">
              <div class="ai-block-header">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 8v4l3 3"/></svg>
                <span class="ai-block-label">AI Administrative Summary</span>
                <span class="ai-block-disclaimer">⚠ Not a clinical judgment</span>
              </div>
              <div class="ai-block-content">${intake.ai_summary}</div>
            </div>` : `<div class="mt-12"><button class="btn btn-secondary btn-sm" onclick="triggerSummarize('${intake.intake_id}')">Generate AI Summary</button></div>`}
          ${intake.missing_fields?.length ? `<div class="mt-12 text-sm text-muted">Missing: ${intake.missing_fields.map(f=>`<span class="badge badge-draft">${f}</span>`).join(' ')}</div>` : ''}
        </div>` : '<div class="mt-16 text-muted text-sm">No intake form submitted yet.</div>'}
    `);
  } catch (e) {
    toast(e.message, 'error');
  }
}

async function showStatusChange(apptId, currentStatus) {
  const statuses = ['requested','confirmed','checked_in','completed','cancelled','no_show'];
  showModal('Update Appointment Status', `
    <div class="form-group">
      <label class="form-label">New Status</label>
      <select class="form-select" id="new-status-sel">
        ${statuses.map(s => `<option value="${s}" ${s===currentStatus?'selected':''}>${s.replace('_',' ')}</option>`).join('')}
      </select>
    </div>
    <div class="form-group">
      <label class="form-label">Changed By</label>
      <input class="form-input" id="changed-by-inp" value="staff" />
    </div>
    <div style="display:flex;gap:10px;justify-content:flex-end;margin-top:8px;">
      <button class="btn btn-secondary" onclick="closeModal()">Cancel</button>
      <button class="btn btn-primary" onclick="submitStatusChange('${apptId}')">Update Status</button>
    </div>
  `);
}

async function submitStatusChange(apptId) {
  try {
    const status = el('new-status-sel').value;
    const changed_by = el('changed-by-inp').value || 'staff';
    await apiFetch(`/appointments/${apptId}/status`, {
      method: 'PATCH',
      body: JSON.stringify({ status, changed_by })
    });
    closeModal();
    toast('Status updated successfully', 'success');
    navigate('appointments');
  } catch (e) {
    toast(e.message, 'error');
  }
}

async function triggerSummarize(intakeId) {
  try {
    toast('Generating AI summary…', 'info');
    closeModal();
    await apiFetch(`/intake-forms/${intakeId}/summarize`, { method: 'POST' });
    toast('AI summary generated', 'success');
  } catch (e) {
    toast(e.message, 'error');
  }
}

/* ============================================================
   INTAKE FORMS VIEW (Staff Portal)
   ============================================================ */
async function renderIntakes(container) {
  try {
    const intakes = await apiFetch('/intake-forms');

    container.innerHTML = `
      <div class="section-header">
        <div>
          <div class="section-title">Intake Forms</div>
          <div class="section-subtitle">${intakes.length} total intake forms</div>
        </div>
      </div>
      <div class="filter-bar">
        <div class="search-input-wrap">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
          <input type="text" id="intake-search" placeholder="Search by symptoms, language…" oninput="filterIntakes()"/>
        </div>
        <select class="filter-select" id="intake-complete-filter" onchange="filterIntakes()">
          <option value="all">All</option>
          <option value="complete">Complete (≥80%)</option>
          <option value="incomplete">Incomplete (&lt;80%)</option>
          <option value="urgent">Urgent Review</option>
        </select>
      </div>
      <div class="card">
        <div class="table-wrap" id="intake-table-wrap">
          ${renderIntakesTable(intakes)}
        </div>
      </div>`;

    window._allIntakes = intakes;
  } catch (e) {
    container.innerHTML = `<div class="empty-state"><div class="empty-state-icon">⚠️</div><div class="empty-state-title">${e.message}</div></div>`;
  }
}

function renderIntakesTable(intakes) {
  if (!intakes.length) return `<div class="empty-state"><div class="empty-state-icon">📄</div><div class="empty-state-title">No intake forms found</div></div>`;
  return `<table>
    <thead><tr>
      <th>Intake ID</th><th>Completeness</th><th>Missing Fields</th><th>AI Summary</th><th>Urgent</th><th>Submitted</th><th>Actions</th>
    </tr></thead>
    <tbody>
      ${intakes.map(i => `
        <tr>
          <td class="td-name" style="font-family:monospace;font-size:.72rem;">${i.intake_id.substring(0,8)}…</td>
          <td style="min-width:160px;">${progressBar(i.completeness_score)}</td>
          <td>${i.missing_fields?.length ? i.missing_fields.map(f=>`<span class="badge badge-draft">${f}</span>`).join(' ') : '<span class="badge badge-confirmed">Complete</span>'}</td>
          <td>${i.ai_summary ? '<span class="badge badge-ai">✓ AI</span>' : '<span class="text-muted text-xs">—</span>'}</td>
          <td>${i.urgent_review_needed ? '<span class="badge badge-urgent">⚠ Urgent</span>' : '—'}</td>
          <td class="text-sm text-muted">${fmtDateTime(i.submitted_at)}</td>
          <td style="display:flex;gap:6px;">
            <button class="btn btn-secondary btn-xs" onclick="showIntakeDetail('${i.intake_id}')">View</button>
            ${!i.ai_summary ? `<button class="btn btn-xs" style="background:rgba(139,92,246,.15);color:var(--violet-500);" onclick="runSummarize('${i.intake_id}')">Summarize</button>` : ''}
          </td>
        </tr>`).join('')}
    </tbody></table>`;
}

function filterIntakes() {
  const q = el('intake-search')?.value.toLowerCase() || '';
  const f = el('intake-complete-filter')?.value || 'all';
  const filtered = (window._allIntakes || []).filter(i => {
    const matchQ = !q || (i.symptoms_description||'').toLowerCase().includes(q) || (i.preferred_language||'').toLowerCase().includes(q);
    const pct = i.completeness_score * 100;
    const matchF = f === 'all' ||
      (f === 'complete' && pct >= 80) ||
      (f === 'incomplete' && pct < 80) ||
      (f === 'urgent' && i.urgent_review_needed);
    return matchQ && matchF;
  });
  el('intake-table-wrap').innerHTML = renderIntakesTable(filtered);
}

async function showIntakeDetail(intakeId) {
  try {
    const i = await apiFetch(`/intake-forms/${intakeId}`);
    showModal('Intake Form Detail', `
      ${i.urgent_review_needed ? `<div class="urgent-banner"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>URGENT CLINICAL REVIEW REQUIRED</div>` : ''}
      <div class="detail-row"><span class="detail-key">Completeness</span><span class="detail-val" style="flex:1">${progressBar(i.completeness_score)}</span></div>
      <div class="detail-row"><span class="detail-key">Symptoms</span><span class="detail-val">${i.symptoms_description || '—'}</span></div>
      <div class="detail-row"><span class="detail-key">Medications</span><span class="detail-val">${i.current_medications || '—'}</span></div>
      <div class="detail-row"><span class="detail-key">Allergies</span><span class="detail-val">${i.allergies || '—'}</span></div>
      <div class="detail-row"><span class="detail-key">Insurance</span><span class="detail-val">${i.insurance_provider || '—'} ${i.insurance_id ? `(${i.insurance_id})` : ''}</span></div>
      <div class="detail-row"><span class="detail-key">Language</span><span class="detail-val">${i.preferred_language || '—'}</span></div>
      <div class="detail-row"><span class="detail-key">Missing Fields</span><span class="detail-val">${i.missing_fields?.length ? i.missing_fields.map(f=>`<span class="badge badge-draft">${f}</span>`).join(' ') : 'None'}</span></div>
      <div class="detail-row"><span class="detail-key">Submitted</span><span class="detail-val">${fmtDateTime(i.submitted_at)}</span></div>
      ${i.ai_summary ? `
        <div class="ai-block mt-16">
          <div class="ai-block-header">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 8v4l3 3"/></svg>
            <span class="ai-block-label">AI Administrative Summary</span>
            <span class="ai-block-disclaimer">⚠ Not a clinical judgment</span>
          </div>
          <div class="ai-block-content">${i.ai_summary}</div>
        </div>` : `
        <div class="mt-16" style="display:flex;gap:10px;align-items:center;">
          <button class="btn btn-secondary" onclick="runSummarize('${i.intake_id}')">Generate AI Summary</button>
          <span class="text-xs text-muted">Uses Anthropic Claude or safe mock fallback</span>
        </div>`}
    `);
  } catch (e) {
    toast(e.message, 'error');
  }
}

async function runSummarize(intakeId) {
  try {
    toast('Generating AI summary…', 'info');
    closeModal();
    await apiFetch(`/intake-forms/${intakeId}/summarize`, { method: 'POST' });
    toast('AI summary generated successfully', 'success');
    navigate('intakes');
  } catch (e) {
    toast(e.message, 'error');
  }
}

/* ============================================================
   FOLLOW-UPS VIEW
   ============================================================ */
async function renderFollowups(container) {
  try {
    const fups = await apiFetch('/followups');

    const badgeEl = el('followup-badge');
    if (badgeEl) badgeEl.textContent = fups.filter(f => f.status === 'draft').length;

    container.innerHTML = `
      <div class="section-header">
        <div>
          <div class="section-title">Follow-up Messages</div>
          <div class="section-subtitle">Review, edit, and approve AI-drafted follow-up messages</div>
        </div>
      </div>
      <div class="filter-bar">
        <select class="filter-select" id="fup-status-filter" onchange="filterFollowups()">
          <option value="all">All Statuses</option>
          <option value="draft">Draft</option>
          <option value="approved">Approved</option>
          <option value="sent">Sent</option>
        </select>
      </div>
      <div class="card">
        <div class="table-wrap" id="fup-table-wrap">
          ${renderFollowupsTable(fups)}
        </div>
      </div>`;

    window._allFollowups = fups;
  } catch (e) {
    container.innerHTML = `<div class="empty-state"><div class="empty-state-icon">⚠️</div><div class="empty-state-title">${e.message}</div></div>`;
  }
}

function renderFollowupsTable(fups) {
  if (!fups.length) return `<div class="empty-state"><div class="empty-state-icon">💬</div><div class="empty-state-title">No follow-ups found</div></div>`;
  return `<table>
    <thead><tr>
      <th>Patient</th><th>Type</th><th>Status</th><th>Draft Preview</th><th>Actions</th>
    </tr></thead>
    <tbody>
      ${fups.map(f => `
        <tr>
          <td class="td-name">${f.patient?.full_name || '—'}</td>
          <td><span style="font-size:.78rem;color:var(--text-muted);">${f.followup_type?.replace(/_/g,' ')}</span></td>
          <td>${badge(f.status)}</td>
          <td style="max-width:220px;"><span style="font-size:.78rem;color:var(--text-muted);display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">${f.message_draft ? f.message_draft.substring(0,80)+'…' : '—'}</span></td>
          <td style="display:flex;gap:6px;">
            <button class="btn btn-secondary btn-xs" onclick="showFollowupDetail('${f.followup_id}')">Review</button>
            ${f.status==='draft' ? `<button class="btn btn-success btn-xs" onclick="approveFollowup('${f.followup_id}')">Approve</button>` : ''}
          </td>
        </tr>`).join('')}
    </tbody></table>`;
}

function filterFollowups() {
  const s = el('fup-status-filter')?.value || 'all';
  const filtered = (window._allFollowups||[]).filter(f => s==='all'||f.status===s);
  el('fup-table-wrap').innerHTML = renderFollowupsTable(filtered);
}

async function showFollowupDetail(fupId) {
  const f = (window._allFollowups||[]).find(x=>x.followup_id===fupId);
  if (!f) return;
  showModal(`Follow-up — ${f.patient?.full_name||''}`, `
    <div class="detail-row"><span class="detail-key">Type</span><span class="detail-val">${f.followup_type?.replace(/_/g,' ')}</span></div>
    <div class="detail-row"><span class="detail-key">Status</span><span class="detail-val">${badge(f.status)}</span></div>
    <div class="form-group mt-16">
      <label class="form-label">Message Draft <span class="badge badge-ai" style="margin-left:6px;">AI-Drafted</span></label>
      <div style="font-size:.72rem;color:var(--text-muted);margin-bottom:8px;">⚠ Review and edit before approving. This is an administrative draft — not a medical communication.</div>
      <textarea class="form-textarea" id="fup-draft-${fupId}" rows="6">${f.message_draft || ''}</textarea>
    </div>
    <div style="display:flex;gap:10px;justify-content:flex-end;margin-top:8px;">
      <button class="btn btn-secondary" onclick="closeModal()">Close</button>
      ${f.status==='draft'?`<button class="btn btn-primary" onclick="submitFollowupApproval('${fupId}','approved')">Approve & Send</button>`:''}
      ${f.status==='approved'?`<button class="btn btn-success" onclick="submitFollowupApproval('${fupId}','sent')">Mark as Sent</button>`:''}
    </div>
  `);
}

async function approveFollowup(fupId) {
  await submitFollowupApproval(fupId, 'approved');
}

async function submitFollowupApproval(fupId, newStatus) {
  try {
    const draftEl = el(`fup-draft-${fupId}`);
    const msg = draftEl ? draftEl.value : undefined;
    await apiFetch(`/followups/${fupId}/status`, {
      method: 'PATCH',
      body: JSON.stringify({ status: newStatus, message_draft: msg })
    });
    closeModal();
    toast(`Follow-up ${newStatus}`, 'success');
    navigate('followups');
  } catch (e) {
    toast(e.message, 'error');
  }
}

/* ============================================================
   PATIENTS VIEW
   ============================================================ */
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
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
          <input type="text" id="patient-search" placeholder="Search by name, email, phone…" oninput="filterPatients()"/>
        </div>
      </div>
      <div class="card">
        <div class="table-wrap" id="patient-table-wrap">
          ${renderPatientsTable(patients)}
        </div>
      </div>`;

    window._allPatients = patients;
  } catch (e) {
    container.innerHTML = `<div class="empty-state"><div class="empty-state-icon">⚠️</div><div class="empty-state-title">${e.message}</div></div>`;
  }
}

function renderPatientsTable(patients) {
  if (!patients.length) return `<div class="empty-state"><div class="empty-state-icon">👤</div><div class="empty-state-title">No patients found</div></div>`;
  return `<table>
    <thead><tr><th>Name</th><th>DOB</th><th>Gender</th><th>Phone</th><th>Email</th><th>Registered</th></tr></thead>
    <tbody>
      ${patients.map(p => `
        <tr>
          <td class="td-name">${p.full_name}</td>
          <td>${fmtDate(p.dob)}</td>
          <td>${p.gender || '—'}</td>
          <td>${p.phone}</td>
          <td style="font-size:.82rem;">${p.email}</td>
          <td class="text-sm text-muted">${fmtDateTime(p.created_at)}</td>
        </tr>`).join('')}
    </tbody></table>`;
}

function filterPatients() {
  const q = el('patient-search')?.value.toLowerCase() || '';
  const filtered = (window._allPatients||[]).filter(p =>
    !q ||
    p.full_name.toLowerCase().includes(q) ||
    (p.email||'').toLowerCase().includes(q) ||
    (p.phone||'').includes(q)
  );
  el('patient-table-wrap').innerHTML = renderPatientsTable(filtered);
}

/* ============================================================
   BOOK APPOINTMENT & INTAKE (Simplified Combined Flow)
   ============================================================ */
async function renderBook(container) {
  container.innerHTML = `
    <div style="max-width:680px;margin:0 auto;">
      <div class="card">
        <div class="card-title mb-16">Clinic Appointment Booking & Intake Form</div>
        <div style="font-size:.82rem;color:var(--text-muted);margin-bottom:20px;padding:12px 14px;background:var(--input-bg);border-radius:var(--radius-sm);border:1px solid var(--border-color);line-height:1.5;">
          Please complete your details below. Your appointment request will be registered and your intake details processed. AI is used solely to generate administrative summaries for front-desk triage support. It is <strong>never used for clinical diagnostics or prescriptions</strong>.
        </div>

        <div>
          <!-- Section 1: Demographics -->
          <div style="font-size:.85rem;font-weight:700;color:var(--text-bright);margin:20px 0 10px;border-left:3px solid var(--indigo-500);padding-left:8px;">1. Patient Demographics</div>
          <div class="form-row">
            <div class="form-group">
              <label class="form-label">Full Name <span class="required">*</span></label>
              <input class="form-input" id="book-name" placeholder="e.g. Priya Sharma" />
            </div>
            <div class="form-group">
              <label class="form-label">Date of Birth <span class="required">*</span></label>
              <input class="form-input" id="book-dob" type="date" />
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label class="form-label">Phone <span class="required">*</span></label>
              <input class="form-input" id="book-phone" placeholder="e.g. 555-0123" />
            </div>
            <div class="form-group">
              <label class="form-label">Email <span class="required">*</span></label>
              <input class="form-input" id="book-email" type="email" placeholder="priya@example.com" />
            </div>
          </div>

          <!-- Section 2: Slot Choice -->
          <div style="font-size:.85rem;font-weight:700;color:var(--text-bright);margin:20px 0 10px;border-left:3px solid var(--indigo-500);padding-left:8px;">2. Choose Appointment Slot</div>
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
              </select>
            </div>
            <div class="form-group">
              <label class="form-label">Preferred Date <span class="required">*</span></label>
              <input class="form-input" id="book-date" type="date" min="${new Date().toISOString().split('T')[0]}" />
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label class="form-label">Preferred Time <span class="required">*</span></label>
              <select class="form-select" id="book-time">
                ${['08:00','09:00','10:00','11:00','14:00','15:00','16:00'].map(t=>`<option>${t}</option>`).join('')}
              </select>
            </div>
            <div class="form-group">
              <label class="form-label">Clinician (Optional)</label>
              <input class="form-input" id="book-clinician" placeholder="e.g. Dr. Osei" />
            </div>
          </div>

          <!-- Section 3: Clinical Intake -->
          <div style="font-size:.85rem;font-weight:700;color:var(--text-bright);margin:20px 0 10px;border-left:3px solid var(--indigo-500);padding-left:8px;">3. Intake Information</div>
          <div class="form-group">
            <label class="form-label">Symptoms / Reason for Visit <span class="required">*</span></label>
            <textarea class="form-textarea" id="book-symptoms" rows="3" placeholder="Describe symptoms or reasons for your visit in your own words…"></textarea>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label class="form-label">Current Medications (Optional)</label>
              <input class="form-input" id="book-meds" placeholder="e.g. Lisinopril 10mg (or 'None')" />
            </div>
            <div class="form-group">
              <label class="form-label">Allergies (Optional)</label>
              <input class="form-input" id="book-allergies" placeholder="e.g. Penicillin (or 'None')" />
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label class="form-label">Insurance Provider (Optional)</label>
              <input class="form-input" id="book-ins-prov" placeholder="e.g. Aetna" />
            </div>
            <div class="form-group">
              <label class="form-label">Insurance ID (Optional)</label>
              <input class="form-input" id="book-ins-id" placeholder="Policy/Member number" />
            </div>
          </div>
          <div class="form-group">
            <label class="form-label">Preferred Language</label>
            <select class="form-select" id="book-lang">
              <option>English</option><option>Spanish</option><option>French</option>
              <option>Hindi</option><option>Vietnamese</option>
            </select>
          </div>

          <!-- Section 4: AI Consent -->
          <div class="form-group mt-16">
            <div class="checkbox-group">
              <input type="checkbox" id="book-consent" />
              <label class="checkbox-label" for="book-consent">
                I consent to having my symptoms summarized by AI. I understand this summary is <strong>strictly for administrative support</strong> and will not be used to make any medical diagnosis or treatment choices. <span class="required">*</span>
              </label>
            </div>
          </div>

          <button class="btn btn-primary w-full mt-12" onclick="submitCombinedBooking()" id="book-submit-btn">
            Book Appointment & Submit Intake
          </button>
        </div>
      </div>
    </div>`;
}

async function submitCombinedBooking() {
  const btn = el('book-submit-btn');
  btn.disabled = true;
  btn.textContent = 'Processing Booking & Intake…';

  try {
    const full_name = el('book-name')?.value?.trim();
    const dob = el('book-dob')?.value;
    const phone = el('book-phone')?.value?.trim();
    const email = el('book-email')?.value?.trim();
    const dept = el('book-dept')?.value;
    const date = el('book-date')?.value;
    const time = el('book-time')?.value;
    const clinician = el('book-clinician')?.value?.trim() || 'To be assigned';
    const symptoms = el('book-symptoms')?.value?.trim();
    const meds = el('book-meds')?.value?.trim() || '';
    const allergies = el('book-allergies')?.value?.trim() || '';
    const insProv = el('book-ins-prov')?.value?.trim() || '';
    const insId = el('book-ins-id')?.value?.trim() || '';
    const lang = el('book-lang')?.value || 'English';
    const consent = el('book-consent')?.checked;

    if (!full_name || !dob || !phone || !email || !date || !symptoms) {
      toast('Please fill in all mandatory fields (*)', 'error');
      btn.disabled = false;
      btn.textContent = 'Book Appointment & Submit Intake';
      return;
    }

    if (!consent) {
      toast('Patient consent is required to submit the intake form', 'error');
      btn.disabled = false;
      btn.textContent = 'Book Appointment & Submit Intake';
      return;
    }

    const payload = {
      full_name,
      dob,
      phone,
      email,
      department: dept,
      appointment_date: date,
      appointment_time: time,
      clinician_name: clinician,
      symptoms_description: symptoms,
      current_medications: meds,
      allergies,
      insurance_provider: insProv,
      insurance_id: insId,
      preferred_language: lang,
      consent_given: true
    };

    const appt = await apiFetch('/appointments/book-with-intake', {
      method: 'POST',
      body: JSON.stringify(payload)
    });

    toast('Appointment requested successfully!', 'success');

    // Auto-trigger summarization in background for staff dashboard
    const intakeForms = await apiFetch(`/appointments/${appt.appointment_id}/intake`).catch(() => []);
    if (intakeForms.length > 0) {
      apiFetch(`/intake-forms/${intakeForms[0].intake_id}/summarize`, { method: 'POST' }).catch(() => {});
    }

    // Success Screen
    el('view-container').innerHTML = `
      <div style="max-width:540px;margin:50px auto;text-align:center;animation:viewSlideIn 0.4s ease both;">
        <div style="font-size:3.5rem;margin-bottom:16px;">🎉</div>
        <h2 style="font-size:1.5rem;font-weight:800;color:var(--text-bright);margin-bottom:12px;">Booking & Intake Completed!</h2>
        <p style="color:var(--text-muted);margin-bottom:24px;line-height:1.5;">Thank you. Your appointment has been booked. Our staff will review your intake details and send a confirmation message shortly.</p>
        
        <div class="card" style="text-align:left;display:flex;flex-direction:column;gap:12px;">
          <div class="detail-row"><span class="detail-key">Patient</span><span class="detail-val">${appt.patient?.full_name || full_name}</span></div>
          <div class="detail-row"><span class="detail-key">Department</span><span class="detail-val">${appt.department}</span></div>
          <div class="detail-row"><span class="detail-key">Date & Time</span><span class="detail-val">${fmtDate(appt.appointment_date)} at ${appt.appointment_time}</span></div>
          <div class="detail-row"><span class="detail-key">Booking Status</span><span class="detail-val">${badge(appt.status)}</span></div>
        </div>

        <button class="btn btn-primary mt-24" onclick="navigate('book')">Book Another Appointment</button>
      </div>`;

  } catch (e) {
    toast(e.message, 'error');
    btn.disabled = false;
    btn.textContent = 'Book Appointment & Submit Intake';
  }
}

/* ============================================================
   INIT
   ============================================================ */
window._prefillApptId = '';
window._prefillPatientId = '';

const overlay = el('modal-overlay');
if (overlay) {
  overlay.addEventListener('click', function(e) {
    if (e.target === this) closeModal();
  });
}

// Boot
setTimeout(() => {
  initTheme();
  navigate('dashboard');
}, 300);
