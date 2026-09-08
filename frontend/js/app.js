/**
 * VerifyNews — Premium Executive White Theme — Frontend Client
 * Handles verification, JWT auth, history drawer, profile modal, and UI utilities.
 * All API contracts remain strictly aligned with the backend.
 */

// ── State ───────────────────────────────────────────────────────

let activeMode = 'url';
let allSources = [];
let stanceFilter = 'ALL';
let historyFilter = 'ALL';
let lastVerificationData = null;

let token = localStorage.getItem('vn_token') || null;
let user = null;
try { user = JSON.parse(localStorage.getItem('vn_user')); } catch { user = null; }

// ── Init ────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
    syncAuthUI();
    if (token) refreshMe();
    updateCharCount();
});

// ── Auth UI Sync ────────────────────────────────────────────────

function syncAuthUI() {
    const guest = document.getElementById('guestNav');
    const authed = document.getElementById('userNav');

    if (token && user) {
        guest.classList.add('hidden');
        authed.classList.remove('hidden');

        const initials = (user.full_name || 'U').split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2);
        document.getElementById('avCircle').textContent = initials;
        document.getElementById('avName').textContent = user.full_name || 'User';
        document.getElementById('avdName').textContent = user.full_name || 'User';
        document.getElementById('avdEmail').textContent = user.email || '';
        document.getElementById('histBadge').textContent = user.total_verifications || 0;
    } else {
        guest.classList.remove('hidden');
        authed.classList.add('hidden');
    }
}

async function refreshMe() {
    if (!token) return;
    try {
        const r = await fetch('/api/v1/auth/me', { headers: { Authorization: `Bearer ${token}` } });
        if (r.ok) {
            user = await r.json();
            localStorage.setItem('vn_user', JSON.stringify(user));
            syncAuthUI();
        } else if (r.status === 401) { logoutUser(); }
    } catch (e) { console.warn('refreshMe failed', e); }
}

// ── Mode Toggle & Inputs ────────────────────────────────────────

function switchMode(mode) {
    activeMode = mode;
    document.getElementById('modeUrl').classList.toggle('active', mode === 'url');
    document.getElementById('modeText').classList.toggle('active', mode === 'text');
    document.getElementById('panelUrl').classList.toggle('active', mode === 'url');
    document.getElementById('panelText').classList.toggle('active', mode === 'text');
    document.getElementById('modeSlider').classList.toggle('right', mode === 'text');
}

function updateCharCount() {
    const txt = document.getElementById('inputText');
    const counter = document.getElementById('textCharCounter');
    if (txt && counter) {
        counter.textContent = `${txt.value.length} chars`;
    }
}

function clearInput(id) {
    const el = document.getElementById(id);
    if (el) {
        el.value = '';
        el.focus();
        updateCharCount();
    }
}

async function pasteClipboardToInput(id) {
    try {
        const text = await navigator.clipboard.readText();
        const el = document.getElementById(id);
        if (el && text) {
            el.value = text;
            updateCharCount();
            showToast('Pasted from clipboard');
        }
    } catch (err) {
        showToast('Please press Ctrl+V to paste');
    }
}

function fillSample(mode, content) {
    switchMode(mode);
    if (mode === 'url') {
        const el = document.getElementById('inputUrl');
        el.value = content;
        el.focus();
    } else {
        const el = document.getElementById('inputText');
        el.value = content;
        updateCharCount();
        el.focus();
    }
    showToast('Sample claim loaded. Click Verify.');
}

// ── Toast Feedback ──────────────────────────────────────────────

let toastTimer = null;
function showToast(msg) {
    const toast = document.getElementById('toastMsg');
    if (!toast) return;
    toast.textContent = msg;
    toast.classList.add('show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => {
        toast.classList.remove('show');
    }, 2800);
}

// ── Error Helpers ───────────────────────────────────────────────

function showError(title, msg) {
    const el = document.getElementById('errBanner');
    document.getElementById('errTitle').textContent = title;
    document.getElementById('errMsg').textContent = msg;
    el.classList.remove('hidden');
    el.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

function hideError() {
    document.getElementById('errBanner').classList.add('hidden');
}

// ── Pipeline Stepper ────────────────────────────────────────────

const STEP_IDS = ['ps-ingest', 'ps-claim', 'ps-search', 'ps-rag', 'ps-stance', 'ps-verdict'];

function markStep(index) {
    STEP_IDS.forEach((id, i) => {
        const el = document.getElementById(id);
        if (el) el.classList.toggle('done', i <= index);
    });
}

// ── Core Verification ───────────────────────────────────────────

async function startVerification() {
    hideError();
    document.getElementById('resultsSection').classList.add('hidden');

    let payload = {};
    if (activeMode === 'url') {
        const v = document.getElementById('inputUrl').value.trim();
        if (!v) { showError('URL Required', 'Please paste a valid news article URL.'); return; }
        payload = { url: v };
    } else {
        const v = document.getElementById('inputText').value.trim();
        if (!v || v.length < 20) { showError('Input Too Short', 'Please paste at least one complete sentence or news statement (20+ characters).'); return; }
        payload = { text: v };
    }

    const btn = document.getElementById('verifyBtn');
    const ctaLabel = document.getElementById('ctaLabel');
    const ctaIcon = document.getElementById('ctaIcon');
    const pipeline = document.getElementById('pipelineSection');

    btn.disabled = true;
    ctaLabel.textContent = 'Cross-Examining Live Sources…';
    ctaIcon.innerHTML = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>';
    pipeline.classList.remove('hidden');
    markStep(0);

    let step = 0;
    const ticker = setInterval(() => { step = Math.min(step + 1, 4); markStep(step); }, 1100);

    try {
        const headers = { 'Content-Type': 'application/json' };
        if (token) headers.Authorization = `Bearer ${token}`;

        const res = await fetch('/api/v1/verify', {
            method: 'POST', headers, body: JSON.stringify(payload)
        });

        clearInterval(ticker);
        markStep(5);

        const data = await res.json();
        if (!res.ok) throw new Error(data.message || data.error || 'Verification failed');

        lastVerificationData = data;
        renderResults(data);
        if (token) refreshMe();

    } catch (err) {
        clearInterval(ticker);
        showError('Verification Failed', err.message || 'Could not reach backend service.');
    } finally {
        btn.disabled = false;
        ctaLabel.textContent = 'Verify Claim Across Newsrooms';
        ctaIcon.innerHTML = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>';
        pipeline.classList.add('hidden');
    }
}

// ── Render Results ──────────────────────────────────────────────

function renderResults(data) {
    allSources = data.sources || [];
    lastVerificationData = data;

    // Verdict badge with visual indicator icon
    const badge = document.getElementById('vrBadge');
    let iconSvg = '';
    if (data.verdict === 'REAL') {
        iconSvg = '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><polyline points="20 6 9 17 4 12"/></svg>';
    } else if (data.verdict === 'FALSE') {
        iconSvg = '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>';
    } else if (data.verdict === 'MISLEADING') {
        iconSvg = '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>';
    } else {
        iconSvg = '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>';
    }
    badge.className = `vr-badge ${data.verdict}`;
    badge.innerHTML = `${iconSvg} <span>${data.verdict}</span>`;

    // Confidence
    document.getElementById('vrConfVal').textContent = `${data.confidence}%`;

    // Claim
    document.getElementById('vrClaim').textContent = `"${data.claim.primary_claim}"`;

    // Entities
    const er = document.getElementById('entityRow');
    er.innerHTML = '';
    (data.claim.entities || []).forEach(e => {
        const s = document.createElement('span');
        s.className = 'e-tag';
        s.textContent = e;
        er.appendChild(s);
    });

    // Explanation
    document.getElementById('vrExplanation').textContent = data.explanation;

    // Agreement bar
    const ev = data.evidence_summary || { supporting: 0, contradicting: 0, neutral: 0 };
    const total = ev.total_sources_evaluated || (ev.supporting + ev.contradicting + ev.neutral) || 1;
    const sp = Math.round((ev.supporting / total) * 100);
    const cp = Math.round((ev.contradicting / total) * 100);
    const np = 100 - sp - cp;

    document.getElementById('agSupport').style.width = sp + '%';
    document.getElementById('agContradict').style.width = cp + '%';
    document.getElementById('agNeutral').style.width = np + '%';
    document.getElementById('cntSupport').textContent = ev.supporting;
    document.getElementById('cntContradict').textContent = ev.contradicting;
    document.getElementById('cntNeutral').textContent = ev.neutral;
    document.getElementById('agPct').textContent = `${data.source_agreement_percentage}%`;

    // Sources
    renderSourceCards();

    // Limitations
    const ul = document.getElementById('limitsList');
    ul.innerHTML = '';
    (data.limitations || []).forEach(l => {
        const li = document.createElement('li');
        li.textContent = l;
        ul.appendChild(li);
    });

    const section = document.getElementById('resultsSection');
    section.classList.remove('hidden');
    section.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function copyReportSummary() {
    if (!lastVerificationData) return;
    const d = lastVerificationData;
    const summary = `VERIFYNEWS FACT-CHECK REPORT
Verdict: ${d.verdict} (${d.confidence}% Confidence)
Claim: "${d.claim.primary_claim}"
Analysis: ${d.explanation}
Source Agreement: ${d.source_agreement_percentage}%
Sources: ${d.sources?.length || 0} evaluated
Verified at: ${new Date().toLocaleString()}`;

    navigator.clipboard.writeText(summary).then(() => {
        showToast('Report copied to clipboard');
    }).catch(() => {
        showToast('Failed to copy report');
    });
}

function filterSources(stance) {
    stanceFilter = stance;
    document.querySelectorAll('.sf-btn').forEach(b => {
        b.classList.toggle('active', b.textContent.toUpperCase().includes(stance) || (stance === 'ALL' && b.textContent === 'All Sources'));
    });
    renderSourceCards();
}

function renderSourceCards() {
    const grid = document.getElementById('srcGrid');
    grid.innerHTML = '';

    const filtered = allSources.filter(s => stanceFilter === 'ALL' || s.stance === stanceFilter);

    if (!filtered.length) {
        grid.innerHTML = '<div style="grid-column:1/-1;text-align:center;color:var(--t3);padding:36px 0;background:#ffffff;border-radius:12px;border:1px dashed var(--b);">No sources match this stance filter.</div>';
        return;
    }

    filtered.forEach(src => {
        const card = document.createElement('div');
        card.className = 'src-card';
        const pubDate = src.published_at ? new Date(src.published_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' }) : 'Recent';

        card.innerHTML = `
            <div>
                <div class="sc-top">
                    <div>
                        <div class="sc-source">${esc(src.source_name)}</div>
                        <div class="sc-meta">${esc(src.domain || '')} · ${pubDate}</div>
                    </div>
                    <span class="sc-stance ${src.stance}">${src.stance}</span>
                </div>
                <div class="sc-title">${esc(src.title)}</div>
                <div class="sc-snippet">"${esc(src.evidence_snippet)}"</div>
            </div>
            <div class="sc-foot">
                <span class="sc-cred-badge">
                    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
                    ${esc(src.credibility_tier.replace(/_/g, ' '))}
                </span>
                <a href="${esc(src.url)}" target="_blank" rel="noopener" class="sc-link">
                    Read original source
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>
                </a>
            </div>
        `;
        grid.appendChild(card);
    });
}

// ── Auth Modal ──────────────────────────────────────────────────

function openAuthModal(tab) {
    switchAuthTab(tab || 'login');
    hide('loginErr'); hide('regErr');
    document.getElementById('authBackdrop').classList.remove('hidden');
}
function closeAuthModal() { document.getElementById('authBackdrop').classList.add('hidden'); }
function closeAuthOnBackdrop(e) { if (e.target.id === 'authBackdrop') closeAuthModal(); }

function switchAuthTab(tab) {
    const isLogin = tab === 'login';
    document.getElementById('atLogin').classList.toggle('active', isLogin);
    document.getElementById('atRegister').classList.toggle('active', !isLogin);
    document.getElementById('formLogin').classList.toggle('hidden', !isLogin);
    document.getElementById('formRegister').classList.toggle('hidden', isLogin);
}

async function handleLogin(e) {
    e.preventDefault();
    const email = document.getElementById('loginEmail').value.trim();
    const pw = document.getElementById('loginPassword').value;
    const errEl = document.getElementById('loginErr');
    const btn = document.getElementById('loginBtn');

    hide('loginErr');
    btn.disabled = true; btn.textContent = 'Signing in…';

    try {
        const r = await fetch('/api/v1/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password: pw })
        });
        const d = await r.json();
        if (!r.ok) throw new Error(d.detail || d.message || 'Login failed');

        token = d.access_token; user = d.user;
        localStorage.setItem('vn_token', token);
        localStorage.setItem('vn_user', JSON.stringify(user));
        syncAuthUI();
        closeAuthModal();
        showToast('Successfully signed in');
    } catch (err) {
        errEl.textContent = err.message;
        errEl.classList.remove('hidden');
    } finally { btn.disabled = false; btn.textContent = 'Sign In'; }
}

async function handleRegister(e) {
    e.preventDefault();
    const name = document.getElementById('regName').value.trim();
    const email = document.getElementById('regEmail').value.trim();
    const pw = document.getElementById('regPassword').value;
    const errEl = document.getElementById('regErr');
    const btn = document.getElementById('regBtn');

    hide('regErr');
    btn.disabled = true; btn.textContent = 'Creating account…';

    try {
        const r = await fetch('/api/v1/auth/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ full_name: name, email, password: pw })
        });
        const d = await r.json();
        if (!r.ok) throw new Error(d.detail || d.message || 'Registration failed');

        token = d.access_token; user = d.user;
        localStorage.setItem('vn_token', token);
        localStorage.setItem('vn_user', JSON.stringify(user));
        syncAuthUI();
        closeAuthModal();
        showToast('Account created successfully');
    } catch (err) {
        errEl.textContent = err.message;
        errEl.classList.remove('hidden');
    } finally { btn.disabled = false; btn.textContent = 'Create Account'; }
}

function logoutUser() {
    token = null; user = null;
    localStorage.removeItem('vn_token');
    localStorage.removeItem('vn_user');
    syncAuthUI();
    document.getElementById('avDropdown').classList.add('hidden');
    showToast('Signed out');
}

// Avatar dropdown
function toggleAvatarMenu() {
    document.getElementById('avDropdown').classList.toggle('hidden');
}
document.addEventListener('click', e => {
    const menu = document.getElementById('avatarMenu');
    if (menu && !menu.contains(e.target)) {
        document.getElementById('avDropdown').classList.add('hidden');
    }
});

// ── Profile Modal ───────────────────────────────────────────────

function openProfileModal() {
    document.getElementById('avDropdown').classList.add('hidden');
    if (!user) return;

    const initials = (user.full_name || 'U').split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2);
    document.getElementById('profAvatar').textContent = initials;
    document.getElementById('profName').textContent = user.full_name;
    document.getElementById('profEmail').textContent = user.email;
    document.getElementById('editName').value = user.full_name || '';
    document.getElementById('editCurPw').value = '';
    document.getElementById('editNewPw').value = '';
    hide('profMsg');

    const since = user.created_at ? new Date(user.created_at).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' }) : 'Recently';
    document.getElementById('profSince').textContent = `Member since ${since}`;

    document.getElementById('stTotal').textContent = user.total_verifications || 0;
    const vs = user.verdict_stats || {};
    document.getElementById('stReal').textContent = vs.REAL || 0;
    document.getElementById('stFalse').textContent = vs.FALSE || 0;
    document.getElementById('stMislead').textContent = vs.MISLEADING || 0;

    document.getElementById('profileBackdrop').classList.remove('hidden');
}
function closeProfileModal() { document.getElementById('profileBackdrop').classList.add('hidden'); }
function closeProfileOnBackdrop(e) { if (e.target.id === 'profileBackdrop') closeProfileModal(); }

async function handleProfileUpdate(e) {
    e.preventDefault();
    const name = document.getElementById('editName').value.trim();
    const curPw = document.getElementById('editCurPw').value;
    const newPw = document.getElementById('editNewPw').value;
    const msgEl = document.getElementById('profMsg');
    const btn = document.getElementById('profSaveBtn');

    msgEl.className = 'form-msg hidden';

    const body = {};
    if (name) body.full_name = name;
    if (newPw) {
        if (!curPw) { msgEl.textContent = 'Enter current password to change it.'; msgEl.className = 'form-msg err'; return; }
        body.current_password = curPw;
        body.new_password = newPw;
    }

    btn.disabled = true; btn.textContent = 'Saving…';

    try {
        const r = await fetch('/api/v1/auth/me', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
            body: JSON.stringify(body)
        });
        const d = await r.json();
        if (!r.ok) throw new Error(d.detail || d.message || 'Update failed');

        user = d; localStorage.setItem('vn_user', JSON.stringify(user));
        syncAuthUI();
        msgEl.textContent = 'Profile updated successfully!'; msgEl.className = 'form-msg ok';
        document.getElementById('editCurPw').value = '';
        document.getElementById('editNewPw').value = '';
        showToast('Profile updated');
    } catch (err) {
        msgEl.textContent = err.message; msgEl.className = 'form-msg err';
    } finally { btn.disabled = false; btn.textContent = 'Save Changes'; }
}

// ── History Drawer ──────────────────────────────────────────────

function toggleHistoryDrawer() {
    document.getElementById('avDropdown').classList.add('hidden');
    const drawer = document.getElementById('drawer');
    const backdrop = document.getElementById('drawerBackdrop');
    const isOpen = drawer.classList.contains('open');

    if (!isOpen) {
        if (!token) { openAuthModal('login'); return; }
        drawer.classList.add('open');
        backdrop.classList.remove('hidden');
        loadHistory();
    } else {
        drawer.classList.remove('open');
        backdrop.classList.add('hidden');
    }
}

function filterHistory(verdict) {
    historyFilter = verdict;
    document.querySelectorAll('.df-pill').forEach(p => {
        p.classList.toggle('active', p.textContent.toUpperCase().includes(verdict) || (verdict === 'ALL' && p.textContent === 'All'));
    });
    loadHistory();
}

async function loadHistory() {
    const list = document.getElementById('drawerList');
    list.innerHTML = '<div class="drawer-empty">Loading records…</div>';

    try {
        let url = '/api/v1/history?page_size=30';
        if (historyFilter !== 'ALL') url += `&verdict=${historyFilter}`;

        const r = await fetch(url, { headers: { Authorization: `Bearer ${token}` } });
        if (!r.ok) throw new Error('Could not load history');
        const d = await r.json();

        document.getElementById('drawerCount').textContent = `${d.total} items`;

        if (!d.items || !d.items.length) {
            list.innerHTML = '<div class="drawer-empty">No verifications found.</div>';
            return;
        }

        list.innerHTML = '';
        d.items.forEach(item => {
            const card = document.createElement('div');
            card.className = 'h-card';
            const date = new Date(item.created_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });

            card.innerHTML = `
                <div class="hc-top">
                    <span class="hc-date">${date}</span>
                    <span class="sc-stance ${item.verdict}">${item.verdict} (${item.confidence}%)</span>
                </div>
                <div class="hc-claim">"${esc(item.primary_claim)}"</div>
                <div class="hc-bottom">
                    <span>${item.total_sources} sources · ${item.source_agreement_percentage}% agreement</span>
                    <button class="hc-del" onclick="deleteHistoryItem(event,${item.id})" title="Delete item">✕</button>
                </div>
            `;
            card.addEventListener('click', e => {
                if (!e.target.classList.contains('hc-del')) replayHistory(item.id);
            });
            list.appendChild(card);
        });
    } catch (err) {
        list.innerHTML = `<div class="drawer-empty" style="color:var(--v-false)">${err.message}</div>`;
    }
}

async function replayHistory(id) {
    try {
        const r = await fetch(`/api/v1/history/${id}`, { headers: { Authorization: `Bearer ${token}` } });
        if (!r.ok) throw new Error('Failed to load detail');
        const d = await r.json();
        toggleHistoryDrawer();
        renderResults(d);
        showToast('Loaded verification from history');
    } catch (err) { showError('History Error', err.message); }
}

async function deleteHistoryItem(e, id) {
    e.stopPropagation();
    try {
        const r = await fetch(`/api/v1/history/${id}`, { method: 'DELETE', headers: { Authorization: `Bearer ${token}` } });
        if (r.ok) { loadHistory(); refreshMe(); showToast('Item deleted'); }
    } catch (err) { console.error('Delete failed', err); }
}

async function clearAllHistory() {
    if (!confirm('Are you sure you want to delete all verification history? This cannot be undone.')) return;
    try {
        const r = await fetch('/api/v1/history', { method: 'DELETE', headers: { Authorization: `Bearer ${token}` } });
        if (r.ok) { loadHistory(); refreshMe(); showToast('History cleared'); }
    } catch (err) { console.error('Clear failed', err); }
}

// ── Utilities ───────────────────────────────────────────────────

function esc(str) {
    if (!str) return '';
    const d = document.createElement('div');
    d.textContent = str;
    return d.innerHTML;
}

function hide(id) {
    const el = document.getElementById(id);
    if (el) el.classList.add('hidden');
}
