/**
 * VerifyNews — Observatory Theme — Frontend Client
 * Handles verification, JWT auth, history drawer, profile modal.
 * All API contracts remain identical to the backend.
 */

// ── State ───────────────────────────────────────────────────────

let activeMode = 'url';
let allSources = [];
let stanceFilter = 'ALL';
let historyFilter = 'ALL';

let token = localStorage.getItem('vn_token') || null;
let user = null;
try { user = JSON.parse(localStorage.getItem('vn_user')); } catch { user = null; }

// ── Init ────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
    syncAuthUI();
    if (token) refreshMe();
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

// ── Mode Toggle ─────────────────────────────────────────────────

function switchMode(mode) {
    activeMode = mode;
    document.getElementById('modeUrl').classList.toggle('active', mode === 'url');
    document.getElementById('modeText').classList.toggle('active', mode === 'text');
    document.getElementById('panelUrl').classList.toggle('active', mode === 'url');
    document.getElementById('panelText').classList.toggle('active', mode === 'text');
    document.getElementById('modeSlider').classList.toggle('right', mode === 'text');
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
        document.getElementById(id).classList.toggle('done', i <= index);
    });
}

// ── Core Verification ───────────────────────────────────────────

async function startVerification() {
    hideError();
    document.getElementById('resultsSection').classList.add('hidden');

    let payload = {};
    if (activeMode === 'url') {
        const v = document.getElementById('inputUrl').value.trim();
        if (!v) { showError('Input Required', 'Please paste a news article URL.'); return; }
        payload = { url: v };
    } else {
        const v = document.getElementById('inputText').value.trim();
        if (!v || v.length < 20) { showError('Input Too Short', 'Paste at least one complete sentence (20+ chars).'); return; }
        payload = { text: v };
    }

    const btn = document.getElementById('verifyBtn');
    const ctaLabel = document.getElementById('ctaLabel');
    const ctaIcon = document.getElementById('ctaIcon');
    const pipeline = document.getElementById('pipelineSection');

    btn.disabled = true;
    ctaLabel.textContent = 'Investigating…';
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

        renderResults(data);
        if (token) refreshMe();

    } catch (err) {
        clearInterval(ticker);
        showError('Verification Failed', err.message || 'Could not reach backend.');
    } finally {
        btn.disabled = false;
        ctaLabel.textContent = 'Verify This Claim';
        ctaIcon.innerHTML = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>';
        pipeline.classList.add('hidden');
    }
}

// ── Render Results ──────────────────────────────────────────────

function renderResults(data) {
    allSources = data.sources || [];

    // Verdict badge
    const badge = document.getElementById('vrBadge');
    badge.textContent = data.verdict;
    badge.className = `vr-badge ${data.verdict}`;

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

function filterSources(stance) {
    stanceFilter = stance;
    document.querySelectorAll('.sf-btn').forEach(b => {
        b.classList.toggle('active', b.textContent.toUpperCase().includes(stance) || (stance === 'ALL' && b.textContent === 'All'));
    });
    renderSourceCards();
}

function renderSourceCards() {
    const grid = document.getElementById('srcGrid');
    grid.innerHTML = '';

    const filtered = allSources.filter(s => stanceFilter === 'ALL' || s.stance === stanceFilter);

    if (!filtered.length) {
        grid.innerHTML = '<div style="grid-column:1/-1;text-align:center;color:var(--t3);padding:32px 0;">No sources match this filter.</div>';
        return;
    }

    filtered.forEach(src => {
        const card = document.createElement('div');
        card.className = 'src-card';
        const pubDate = src.published_at ? new Date(src.published_at).toLocaleDateString() : 'Recent';

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
                <span>${esc(src.credibility_tier.replace(/_/g, ' '))}</span>
                <a href="${esc(src.url)}" target="_blank" rel="noopener" class="sc-link">Read ↗</a>
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
        syncAuthUI(); closeAuthModal();
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
    btn.disabled = true; btn.textContent = 'Creating…';

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
        syncAuthUI(); closeAuthModal();
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
        msgEl.textContent = 'Profile updated!'; msgEl.className = 'form-msg ok';
        document.getElementById('editCurPw').value = '';
        document.getElementById('editNewPw').value = '';
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
    list.innerHTML = '<div class="drawer-empty">Loading…</div>';

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
                    <span>${item.total_sources} sources · ${item.source_agreement_percentage}% agree</span>
                    <button class="hc-del" onclick="deleteHistoryItem(event,${item.id})">✕</button>
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
    } catch (err) { showError('History Error', err.message); }
}

async function deleteHistoryItem(e, id) {
    e.stopPropagation();
    try {
        const r = await fetch(`/api/v1/history/${id}`, { method: 'DELETE', headers: { Authorization: `Bearer ${token}` } });
        if (r.ok) { loadHistory(); refreshMe(); }
    } catch (err) { console.error('Delete failed', err); }
}

async function clearAllHistory() {
    if (!confirm('Delete all verification history? This cannot be undone.')) return;
    try {
        const r = await fetch('/api/v1/history', { method: 'DELETE', headers: { Authorization: `Bearer ${token}` } });
        if (r.ok) { loadHistory(); refreshMe(); }
    } catch (err) { console.error('Clear failed', err); }
}

// ── Utilities ───────────────────────────────────────────────────

function esc(str) {
    if (!str) return '';
    const d = document.createElement('div');
    d.textContent = str;
    return d.innerHTML;
}

function hide(id) { document.getElementById(id).classList.add('hidden'); }
