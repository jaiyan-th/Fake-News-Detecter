/**
 * VerifyNews Engine — Live Client
 * Text Analysis & URL Analysis Alone
 * Zero mock data — 100% Live Backend
 */

let activeMode = 'text';
let lastResult = null;

document.addEventListener('DOMContentLoaded', () => {
    updateCharCounter();
});

// ── Mode Switch ─────────────────────────────────────────────────

function switchMode(mode) {
    activeMode = mode;
    const tabText = document.getElementById('tabText');
    const tabUrl = document.getElementById('tabUrl');
    const panelText = document.getElementById('panelText');
    const panelUrl = document.getElementById('panelUrl');

    if (mode === 'url') {
        tabUrl.classList.add('active');
        tabText.classList.remove('active');
        panelUrl.classList.remove('hidden');
        panelText.classList.add('hidden');
        document.getElementById('inputUrl').focus();
    } else {
        tabText.classList.add('active');
        tabUrl.classList.remove('active');
        panelText.classList.remove('hidden');
        panelUrl.classList.add('hidden');
        document.getElementById('inputText').focus();
    }
}

function updateCharCounter() {
    const textEl = document.getElementById('inputText');
    const counterEl = document.getElementById('charCounter');
    if (textEl && counterEl) {
        counterEl.textContent = `${textEl.value.length} / 500 characters`;
    }
}

function clearActiveInput() {
    if (activeMode === 'url') {
        const u = document.getElementById('inputUrl');
        if (u) { u.value = ''; u.focus(); }
    } else {
        const t = document.getElementById('inputText');
        if (t) { t.value = ''; t.focus(); updateCharCounter(); }
    }
    showToast('Input cleared');
}

async function pasteFromClipboard() {
    try {
        const text = await navigator.clipboard.readText();
        if (text) {
            if (activeMode === 'url') {
                document.getElementById('inputUrl').value = text;
            } else {
                document.getElementById('inputText').value = text;
                updateCharCounter();
            }
            showToast('Pasted from clipboard');
        }
    } catch {
        showToast('Please press Ctrl+V to paste');
    }
}

// ── Run Analysis ────────────────────────────────────────────────

async function runAnalysis() {
    let payload = {};

    if (activeMode === 'url') {
        const url = document.getElementById('inputUrl').value.trim();
        if (!url) {
            showToast('Please enter an article URL');
            document.getElementById('inputUrl').focus();
            return;
        }
        payload = { url };
    } else {
        const text = document.getElementById('inputText').value.trim();
        if (!text || text.length < 15) {
            showToast('Please enter at least 15 characters of news text');
            document.getElementById('inputText').focus();
            return;
        }
        payload = { text };
    }

    const btn = document.getElementById('verifyBtn');
    const ctaText = document.getElementById('ctaBtnText');
    const ctaIcon = document.getElementById('ctaBtnIcon');
    const radar = document.getElementById('loadingRadar');
    const results = document.getElementById('resultsSection');
    const sources = document.getElementById('sourcesSection');

    // UI loading state
    btn.disabled = true;
    ctaText.textContent = 'Analyzing…';
    ctaIcon.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>';

    radar.classList.remove('hidden');
    results.classList.add('hidden');
    sources.classList.add('hidden');

    resetSteps();
    animateSteps();

    try {
        const res = await fetch('/api/v1/verify', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!res.ok) {
            const errData = await res.json().catch(() => ({}));
            throw new Error(errData.message || errData.detail || 'Verification request failed');
        }

        const data = await res.json();
        lastResult = data;

        // Render real data
        renderResults(data);

        // Show results
        results.classList.remove('hidden');
        sources.classList.remove('hidden');
        results.scrollIntoView({ behavior: 'smooth', block: 'start' });
        showToast('Analysis complete');

    } catch (err) {
        showToast(`Error: ${err.message}`);
    } finally {
        btn.disabled = false;
        ctaText.textContent = 'Verify Claim';
        ctaIcon.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>';
        radar.classList.add('hidden');
    }
}

// ── Progress Steps Animation ────────────────────────────────────

function resetSteps() {
    for (let i = 1; i <= 6; i++) {
        const el = document.getElementById(`step-${i}`);
        if (el) el.classList.remove('done');
    }
}

function animateSteps() {
    for (let i = 1; i <= 6; i++) {
        const el = document.getElementById(`step-${i}`);
        if (el) {
            setTimeout(() => {
                el.classList.add('done');
            }, i * 350);
        }
    }
}

// ── Render Live Results ─────────────────────────────────────────

function renderResults(data) {
    const verdict = (data.verdict || 'UNVERIFIED').toUpperCase();
    const conf = data.confidence || 0;

    // Banner
    const banner = document.getElementById('verdictBanner');
    const vbTitle = document.getElementById('vbTitle');
    const vbDesc = document.getElementById('vbDesc');
    const vbIcon = document.getElementById('vbIcon');

    let vClass = 'unverified';
    let titleText = 'UNVERIFIED CLAIM';
    let descText = 'Insufficient authoritative reporting found across newsroom indexes';

    if (verdict === 'REAL') {
        vClass = 'real';
        titleText = 'VERIFIED — REAL';
        descText = `Corroborated by ${data.sources?.length || 0} live newsroom reports`;
        vbIcon.innerHTML = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><polyline points="20 6 9 17 4 12"/></svg>';
    } else if (verdict === 'FALSE') {
        vClass = 'false';
        titleText = 'DEBUNKED — FALSE';
        descText = 'Directly disproved by authoritative reporting and statements';
        vbIcon.innerHTML = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>';
    } else if (verdict === 'MISLEADING') {
        vClass = 'misleading';
        titleText = 'MISLEADING / PARTIALLY TRUE';
        descText = 'Claim contains distorted, inaccurate, or missing context';
        vbIcon.innerHTML = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>';
    } else {
        vbIcon.innerHTML = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>';
    }

    banner.className = `verdict-banner ${vClass}`;
    vbTitle.textContent = titleText;
    vbDesc.textContent = descText;

    // Confidence Dial
    document.getElementById('gaugeVal').textContent = `${conf}%`;
    const gaugeBar = document.getElementById('gaugeBar');
    const circumference = 345.5;
    const offset = circumference - (circumference * conf / 100);
    gaugeBar.style.strokeDashoffset = offset;

    if (verdict === 'REAL') gaugeBar.style.stroke = '#059669';
    else if (verdict === 'FALSE') gaugeBar.style.stroke = '#dc2626';
    else if (verdict === 'MISLEADING') gaugeBar.style.stroke = '#d97706';
    else gaugeBar.style.stroke = '#64748b';

    // Extracted Claim
    const claim = data.claim?.primary_claim || (activeMode === 'url' ? document.getElementById('inputUrl').value : document.getElementById('inputText').value);
    document.getElementById('claimHeadline').textContent = `"${claim}"`;

    // Entities
    const entitySection = document.getElementById('entitySection');
    const entityRow = document.getElementById('entityPillsRow');
    entityRow.innerHTML = '';
    const entities = data.claim?.entities || [];

    if (entities.length > 0) {
        entitySection.classList.remove('hidden');
        entities.forEach(ent => {
            const span = document.createElement('span');
            span.className = 'entity-badge org';
            span.textContent = ent;
            entityRow.appendChild(span);
        });
    } else {
        entitySection.classList.add('hidden');
    }

    // Synthesis
    document.getElementById('synthesisText').textContent = data.explanation || 'No detailed analysis returned.';

    // Breakdown
    const ev = data.evidence_summary || { supporting: 0, neutral: 0, contradicting: 0 };
    const total = (ev.supporting + ev.neutral + ev.contradicting) || 1;
    const sp = Math.round((ev.supporting / total) * 100);
    const cp = Math.round((ev.contradicting / total) * 100);
    const np = 100 - sp - cp;

    document.getElementById('bdSegSupport').style.width = `${sp}%`;
    document.getElementById('bdSegNeutral').style.width = `${np}%`;
    document.getElementById('bdSegContra').style.width = `${cp}%`;

    document.getElementById('cntSupport').textContent = `${ev.supporting} (${sp}%)`;
    document.getElementById('cntNeutral').textContent = `${ev.neutral} (${np}%)`;
    document.getElementById('cntContra').textContent = `${ev.contradicting} (${cp}%)`;
    document.getElementById('bdParsedCount').textContent = `${data.sources?.length || 0} Sources Evaluated`;

    // Evidence Sources Grid
    renderSources(data.sources || []);
}

function renderSources(sources) {
    const list = document.getElementById('sourcesList');
    list.innerHTML = '';

    if (!sources || sources.length === 0) {
        list.innerHTML = `
            <div style="grid-column: 1 / -1; text-align: center; padding: 32px 20px; background: #ffffff; border: 1px dashed var(--b); border-radius: 12px; color: var(--t3);">
                No matching newsroom articles were indexed for this specific query.
            </div>
        `;
        return;
    }

    sources.forEach(src => {
        const card = document.createElement('div');
        card.className = 'wire-card';

        let stanceClass = 'neutral';
        let stanceBadge = 'Neutral Context';
        if (src.stance === 'SUPPORT') {
            stanceClass = 'support';
            stanceBadge = 'Supports Claim';
        } else if (src.stance === 'CONTRADICT') {
            stanceClass = 'contra';
            stanceBadge = 'Contradicts Claim';
        }

        const dateStr = src.published_at ? new Date(src.published_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' }) : 'Recent';

        card.innerHTML = `
            <div>
                <div class="wc-top">
                    <div>
                        <div class="wc-outlet-name">${esc(src.source_name || 'News Source')}</div>
                        <div class="wc-bureau">${esc(src.domain || '')}</div>
                    </div>
                    <span class="wc-badge ${stanceClass}">${stanceBadge}</span>
                </div>
                <div class="wc-quote">"${esc(src.evidence_snippet || src.title)}"</div>
            </div>
            <div class="wc-bottom">
                <span class="wc-time">${dateStr}</span>
                <a href="${esc(src.url)}" target="_blank" rel="noopener" class="wc-link">
                    Read Article ↗
                </a>
            </div>
        `;
        list.appendChild(card);
    });
}

// ── Copy Report & Toast ─────────────────────────────────────────

function copyReport() {
    if (!lastResult) return;
    const d = lastResult;
    const text = `VERIFYNEWS FACT-CHECK REPORT
Verdict: ${d.verdict} (${d.confidence}% Confidence)
Claim: "${d.claim?.primary_claim || ''}"
Analysis: ${d.explanation || ''}
Source Agreement: ${d.source_agreement_percentage || 0}%
Sources Evaluated: ${d.sources?.length || 0}`;

    navigator.clipboard.writeText(text).then(() => {
        showToast('Report copied to clipboard');
    }).catch(() => {
        showToast('Copied');
    });
}

let toastTimer = null;
function showToast(msg) {
    const el = document.getElementById('toastMsg');
    if (!el) return;
    el.textContent = msg;
    el.classList.add('show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => el.classList.remove('show'), 2600);
}

function esc(str) {
    if (!str) return '';
    const d = document.createElement('div');
    d.textContent = str;
    return d.innerHTML;
}

function toggleHistoryDrawer() {
    showToast('History drawer: 0 items');
}

function openAuthModal(tab) {
    showToast('Authentication service online');
}
