class Dashboard {
    constructor() {
        this.resultsPanel = document.getElementById('results-panel');
        this.loadingIndicator = document.getElementById('loading-indicator');
        this.steps = document.querySelectorAll('.pipeline-progress .step');
    }

    showLoading(useRag = false) {
        this.resultsPanel.classList.add('hidden');
        this.loadingIndicator.classList.remove('hidden');

        // Swap progress bars
        const standardBar = document.getElementById('pipeline-progress-standard');
        const ragBar      = document.getElementById('pipeline-progress-rag');
        const loadingText = document.getElementById('loading-text');

        if (useRag) {
            standardBar?.classList.add('hidden');
            ragBar?.classList.remove('hidden');
            if (loadingText) loadingText.textContent = 'Running 11-Step RAG Pipeline...';
            this.steps = ragBar ? ragBar.querySelectorAll('.step') : this.steps;
        } else {
            ragBar?.classList.add('hidden');
            standardBar?.classList.remove('hidden');
            if (loadingText) loadingText.textContent = 'Analyzing through Neural Verification Engine...';
            this.steps = standardBar ? standardBar.querySelectorAll('.step') : this.steps;
        }

        this.resetSteps();

        let currentStep = 0;
        this.progressInterval = setInterval(() => {
            if (currentStep < this.steps.length) {
                this.steps.forEach(step => step.classList.remove('active'));
                this.steps[currentStep].classList.add('active');
                currentStep++;
            }
        }, useRag ? 600 : 800);
    }

    hideLoading() {
        clearInterval(this.progressInterval);
        this.loadingIndicator.classList.add('hidden');
    }

    resetSteps() {
        this.steps.forEach(step => step.classList.remove('active'));
        if (this.steps.length > 0) {
            this.steps[0].classList.add('active');
        }
    }

    renderResult(data) {
        this.hideLoading();
        this.resultsPanel.classList.remove('hidden');

        if (!data || typeof data !== 'object') {
            this.renderError('Invalid response data received from server');
            return;
        }

        if (!data.success) {
            this.renderError(data.error || 'Failed to analyze the input.');
            return;
        }

        if (!data.prediction || data.confidence === undefined) {
            this.renderError('Incomplete analysis data received from server');
            return;
        }

        const verdictBanner = document.getElementById('verdict-banner');
        verdictBanner.className = 'verdict-banner ' + data.prediction.toLowerCase();

        document.getElementById('prediction-text').textContent = data.prediction;

        const confidencePercent = typeof data.confidence === 'number'
            ? Math.round(data.confidence * 100)
            : parseInt(data.confidence) || 0;
        document.getElementById('confidence-score').textContent = confidencePercent + '%';

        document.getElementById('domain-badge').textContent = data.isRag ? 'RAG Pipeline' : 'Multi-Model AI';
        document.getElementById('explanation-text').textContent = data.explanation || 'No explanation available';

        this.renderLlmAnalysis(data.llm_analysis, data.input_type);

        const warningsList = document.getElementById('warnings-list');
        warningsList.innerHTML = '';
        if (data.warnings && data.warnings.length > 0) {
            data.warnings.forEach(warning => {
                const li = document.createElement('li');
                li.textContent = `Warning: ${warning}`;
                warningsList.appendChild(li);
            });
        }

        const sourcesList = document.getElementById('sources-list');
        sourcesList.innerHTML = '';
        if (data.verified_sources && data.verified_sources.length > 0) {
            data.verified_sources.forEach(source => {
                const div = document.createElement('div');
                div.className = 'source-item';

                const sourceTitle = source.title || source.article_title || 'Untitled';
                const sourceUrl = source.url || source.article_url || '#';
                const sourceName = source.source || 'Unknown Source';
                const similarity = source.similarity || '';
                const isTrusted = source.is_trusted ? ' ✓' : '';

                // Stance badge (RAG-specific)
                let stanceBadge = '';
                if (source.stance) {
                    const stanceColor = source.stance === 'support'
                        ? '#22c55e' : source.stance === 'contradict'
                        ? '#ef4444' : '#94a3b8';
                    stanceBadge = `<span style="
                        display:inline-block; padding:1px 7px; border-radius:10px;
                        font-size:11px; font-weight:600; color:#fff;
                        background:${stanceColor}; margin-left:6px; text-transform:uppercase;">
                        ${source.stance}
                    </span>`;
                }

                div.innerHTML = `
                    <strong>${sourceName}${isTrusted}${stanceBadge}
                        <span style="font-weight:400; color:var(--text-muted); font-size:12px; margin-left:6px;">${similarity}</span>
                    </strong>
                    <p>${sourceTitle}</p>
                    ${sourceUrl !== '#' ? `<a href="${sourceUrl}" target="_blank" rel="noopener noreferrer">View Source</a>` : ''}
                `;
                sourcesList.appendChild(div);
            });
        } else {
            sourcesList.innerHTML = '<p>No reliable sources found for this claim.</p>';
        }

        // Render RAG-specific evidence panel if present
        if (data.isRag && data.rag) {
            this.renderRagPanel(data.rag, data.metrics, data.request_id);
        } else {
            this._hideRagPanel();
        }
    }

    renderLlmAnalysis(llmAnalysis, inputType) {
        const llmSection = document.getElementById('llm-section');
        const llmVerdict = document.getElementById('llm-verdict-text');
        const llmStatusBadge = document.getElementById('llm-status-badge');
        const llmSummary = document.getElementById('llm-summary-text');
        const llmReasoningList = document.getElementById('llm-reasoning-list');
        const llmWarning = document.getElementById('llm-warning-text');

        if (!llmSection || !llmVerdict || !llmStatusBadge || !llmSummary || !llmReasoningList || !llmWarning) {
            return;
        }

        // Only show LLM section for URL analysis
        if (inputType !== 'url') {
            llmSection.classList.add('hidden');
            llmReasoningList.innerHTML = '';
            llmWarning.textContent = '';
            llmWarning.classList.add('hidden');
            return;
        }

        const hasSummary = llmAnalysis && (llmAnalysis.summary || llmAnalysis.warning);
        if (!hasSummary) {
            llmSection.classList.add('hidden');
            llmReasoningList.innerHTML = '';
            llmWarning.textContent = '';
            llmWarning.classList.add('hidden');
            return;
        }

        llmSection.classList.remove('hidden');
        llmVerdict.textContent = llmAnalysis.verdict || 'UNVERIFIED';

        const providerLabel = llmAnalysis.provider ? String(llmAnalysis.provider).toUpperCase() : 'LLM';
        llmStatusBadge.textContent = llmAnalysis.enabled
            ? `${providerLabel} | ${llmAnalysis.model || 'Configured'}`
            : `${providerLabel} Optional`;

        llmSummary.textContent = llmAnalysis.summary || 'The frontend submitted a URL, but no Groq result is available yet. Configure GROQ_API_KEY to enable context-aware URL reasoning.';

        llmReasoningList.innerHTML = '';
        const reasoning = Array.isArray(llmAnalysis.reasoning) ? llmAnalysis.reasoning : [];
        reasoning.forEach(item => {
            const li = document.createElement('li');
            li.textContent = item;
            llmReasoningList.appendChild(li);
        });

        if (llmAnalysis.warning) {
            llmWarning.textContent = llmAnalysis.warning;
            llmWarning.classList.remove('hidden');
        } else {
            llmWarning.textContent = '';
            llmWarning.classList.add('hidden');
        }
    }

    renderError(msg) {
        const verdictBanner = document.getElementById('verdict-banner');
        verdictBanner.className = 'verdict-banner fake';
        document.getElementById('prediction-text').textContent = 'ERROR';
        document.getElementById('confidence-score').textContent = '-';
        document.getElementById('domain-badge').textContent = 'System';
        document.getElementById('explanation-text').textContent = msg;
        document.getElementById('warnings-list').innerHTML = '';
        document.getElementById('sources-list').innerHTML = '';
        this.renderLlmAnalysis(null, null);
        this._hideRagPanel();
    }

    // ── RAG Evidence Panel ──────────────────────────────────────────────────

    /**
     * Render the full RAG evidence + metrics panel (STEP 13).
     * Creates or updates #rag-panel inside #results-panel.
     */
    renderRagPanel(rag, metrics, requestId) {
        let panel = document.getElementById('rag-panel');
        if (!panel) {
            panel = document.createElement('div');
            panel.id = 'rag-panel';
            panel.className = 'rag-panel-root';
            const resultsPanel = document.getElementById('results-panel');
            if (resultsPanel) resultsPanel.appendChild(panel);
        }

        const gapColors = {
            'Fully Supported':    '#22c55e',
            'Partially Supported':'#f59e0b',
            'Unsupported':        '#94a3b8',
            'Contradicted':       '#ef4444',
        };
        const gapColor = gapColors[rag.gap_analysis] || '#94a3b8';

        // ── Evidence rows ──
        const newsRows = (rag.news_api_evidence || []).map(ev => {
            const sc = ev.stance === 'support' ? '#22c55e'
                     : ev.stance === 'contradict' ? '#ef4444' : '#94a3b8';
            const link = ev.url
                ? `<a href="${ev.url}" target="_blank" rel="noopener noreferrer"
                      class="rag-ev-link">View ↗</a>` : '';
            return `<div class="rag-ev-row">
                <span class="rag-stance-badge" style="background:${sc}">${ev.stance||'neutral'}</span>
                <div class="rag-ev-body">
                    <div class="rag-ev-title">${ev.title||'—'}</div>
                    <div class="rag-ev-meta">${ev.source||''} · sim ${ev.similarity||'—'} ${link}</div>
                    ${ev.summary ? `<div class="rag-ev-summary">${ev.summary}</div>` : ''}
                </div>
            </div>`;
        }).join('');

        const ragRows = (rag.rag_evidence || []).map(ev => {
            const sc = ev.stance === 'support' ? '#22c55e'
                     : ev.stance === 'contradict' ? '#ef4444' : '#94a3b8';
            return `<div class="rag-ev-row">
                <span class="rag-stance-badge" style="background:${sc}">${ev.stance||'neutral'}</span>
                <div class="rag-ev-body">
                    <div class="rag-ev-title">${ev.content||'—'}</div>
                    <div class="rag-ev-meta">${ev.source||''} · sim ${ev.similarity||'—'}</div>
                </div>
            </div>`;
        }).join('');

        // ── Metrics panel (STEP 13) ──
        let metricsHtml = '';
        if (metrics) {
            const latColor  = metrics.latency_ms < 8000 ? '#22c55e'
                            : metrics.latency_ms < 15000 ? '#f59e0b' : '#ef4444';
            const accPct    = Math.round((metrics.retrieval_accuracy || 0) * 100);
            const accColor  = accPct >= 60 ? '#22c55e' : accPct >= 40 ? '#f59e0b' : '#ef4444';
            const covColor  = (metrics.evidence_coverage || 0) >= 2 ? '#22c55e'
                            : (metrics.evidence_coverage || 0) >= 1 ? '#f59e0b' : '#94a3b8';

            const compRows = metrics.confidence_components
                ? Object.entries(metrics.confidence_components).map(([k, v]) =>
                    `<div class="rag-metric-comp-row">
                        <span class="rag-metric-comp-key">${k.replace(/_/g,' ')}</span>
                        <div class="rag-metric-bar-wrap">
                            <div class="rag-metric-bar-fill"
                                 style="width:${Math.round(v*100)}%;background:#f97316"></div>
                        </div>
                        <span class="rag-metric-comp-val">${(v*100).toFixed(1)}%</span>
                    </div>`).join('')
                : '';

            metricsHtml = `
            <div class="rag-metrics-section">
                <div class="rag-section-label">📊 Pipeline Metrics (STEP 10)</div>
                <div class="rag-metrics-grid">
                    <div class="rag-metric-card">
                        <div class="rag-metric-value" style="color:${latColor}">
                            ${metrics.latency_ms < 1000
                                ? metrics.latency_ms.toFixed(0)+'ms'
                                : (metrics.latency_ms/1000).toFixed(1)+'s'}
                        </div>
                        <div class="rag-metric-label">Response Time</div>
                    </div>
                    <div class="rag-metric-card">
                        <div class="rag-metric-value" style="color:${accColor}">${accPct}%</div>
                        <div class="rag-metric-label">Retrieval Quality</div>
                    </div>
                    <div class="rag-metric-card">
                        <div class="rag-metric-value" style="color:${covColor}">
                            ${metrics.evidence_coverage || 0}
                        </div>
                        <div class="rag-metric-label">Evidence Strength</div>
                    </div>
                    <div class="rag-metric-card">
                        <div class="rag-metric-value" style="color:#f97316">
                            ${(metrics.confidence_score||0).toFixed(1)}%
                        </div>
                        <div class="rag-metric-label">Confidence Score</div>
                    </div>
                </div>
                ${compRows ? `
                <div class="rag-conf-breakdown">
                    <div class="rag-section-label" style="margin-top:12px;margin-bottom:8px;">
                        Confidence Breakdown
                    </div>
                    ${compRows}
                </div>` : ''}
                <div class="rag-latency-detail">
                    <span>News API: ${(metrics.news_api_latency_ms||0).toFixed(0)}ms</span>
                    <span>Vector DB: ${(metrics.rag_db_latency_ms||0).toFixed(0)}ms</span>
                    <span>Re-rank: ${(metrics.rerank_latency_ms||0).toFixed(0)}ms</span>
                    <span>LLM: ${(metrics.llm_latency_ms||0).toFixed(0)}ms</span>
                </div>
            </div>`;
        }

        // ── Request ID trace ──
        const traceHtml = requestId
            ? `<div class="rag-trace-id">🔍 Request ID: <code>${requestId}</code></div>`
            : '';

        panel.innerHTML = `
            <div class="rag-panel-header">
                <h3 class="rag-panel-title">🔬 RAG Pipeline Evidence</h3>
                <span class="rag-gap-badge" style="background:${gapColor}">
                    ${rag.gap_analysis || 'Unknown'}
                </span>
            </div>

            ${traceHtml}

            ${rag.claim_summary ? `
            <div class="rag-claim-box">
                <strong>Claim:</strong> ${rag.claim_summary}
            </div>` : ''}

            ${(rag.expanded_queries && rag.expanded_queries.length > 0) ? `
            <div class="rag-ev-section" style="margin-bottom:14px;">
                <div class="rag-section-label">🔍 Expanded Queries (STEP 2)</div>
                <div style="display:flex;flex-wrap:wrap;gap:6px;margin-top:6px;">
                    ${rag.expanded_queries.map(q =>
                        `<span style="background:rgba(249,115,22,.1);color:#f97316;
                            padding:2px 10px;border-radius:12px;font-size:11px;
                            border:1px solid rgba(249,115,22,.25);">${q}</span>`
                    ).join('')}
                </div>
            </div>` : ''}

            ${rag.retrieval_stats && rag.retrieval_stats.total_results !== undefined ? `
            <div class="rag-ev-section" style="margin-bottom:14px;">
                <div class="rag-section-label">📡 Retrieval Stats (STEP 3)</div>
                <div style="display:flex;gap:16px;flex-wrap:wrap;margin-top:6px;font-size:12px;color:var(--text-muted,#94a3b8);">
                    <span>Total: <strong style="color:#f1f5f9">${rag.retrieval_stats.total_results}</strong></span>
                    <span>News API: <strong style="color:#f1f5f9">${rag.retrieval_stats.news_api_results || 0}</strong></span>
                    <span>RAG DB: <strong style="color:#f1f5f9">${rag.retrieval_stats.rag_results || 0}</strong></span>
                    <span>Sources: <strong style="color:#f1f5f9">${(rag.retrieval_stats.used_sources || []).join(', ')}</strong></span>
                </div>
            </div>` : ''}

            ${newsRows ? `
            <div class="rag-ev-section">
                <div class="rag-section-label">
                    🌐 News API Evidence (${(rag.news_api_evidence||[]).length})
                </div>
                ${newsRows}
            </div>` : ''}

            ${ragRows ? `
            <div class="rag-ev-section">
                <div class="rag-section-label">
                    📚 Historical Knowledge Base (${(rag.rag_evidence||[]).length})
                </div>
                ${ragRows}
            </div>` : ''}

            ${rag.reasoning ? `
            <div class="rag-reasoning-box">
                <div class="rag-section-label" style="margin-bottom:6px;">💭 Grounded Reasoning</div>
                ${rag.reasoning}
            </div>` : ''}

            ${metricsHtml}
        `;
    }

    _hideRagPanel() {
        const panel = document.getElementById('rag-panel');
        if (panel) panel.remove();
    }

    renderHistory(historyArray) {
        const tbody = document.getElementById('history-list-body');
        if (!tbody) {
            return;
        }

        tbody.innerHTML = '';

        const statCount = document.getElementById('stat-count');
        if (statCount) {
            statCount.textContent = historyArray ? historyArray.length : 0;
        }

        // Update profile total analyses
        const profileTotal = document.getElementById('profile-total-analyses');
        if (profileTotal) {
            profileTotal.textContent = historyArray ? historyArray.length : 0;
        }

        if (!historyArray || historyArray.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" style="text-align:center; padding: 40px; color: var(--text-muted);">No analysis history found.</td></tr>';
            return;
        }

        historyArray.forEach(item => {
            const tr = document.createElement('tr');

            const colorClass = item.prediction === 'REAL'
                ? 'var(--real-color)'
                : item.prediction === 'FAKE'
                    ? 'var(--fake-color)'
                    : 'var(--misleading-color)';

            const bgClass = item.prediction === 'REAL'
                ? 'var(--real-bg)'
                : item.prediction === 'FAKE'
                    ? 'var(--fake-bg)'
                    : 'var(--misleading-bg)';

            let typeIcon = '';
            if (item.input_type === 'url') {
                typeIcon = '<svg width="16" height="16" style="color:var(--primary-orange); margin-right:8px;" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>';
            } else if (item.input_type === 'image') {
                typeIcon = '<svg width="16" height="16" style="color:var(--primary-orange); margin-right:8px;" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>';
            } else {
                typeIcon = '<svg width="16" height="16" style="color:var(--primary-orange); margin-right:8px;" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>';
            }

            const typeLabel = item.input_type ? item.input_type.charAt(0).toUpperCase() + item.input_type.slice(1) : 'Text';

            tr.innerHTML = `
                <td style="font-weight:600; display:flex; align-items:center;">${typeIcon} ${typeLabel}</td>
                <td>
                    <div class="input-preview">
                        <strong>${(item.input_text || '').substring(0, 50)}...</strong>
                        <span>${item.domain || 'General Analysis'}</span>
                    </div>
                </td>
                <td><span class="badge" style="background:${bgClass}; color:${colorClass};">${item.prediction}</span></td>
                <td>
                    <div class="confidence-meter">
                        <div class="meter-bg" style="width:100px;">
                            <div class="meter-fill" style="width: ${item.confidence * 100}%; background: ${colorClass};"></div>
                        </div>
                        <span style="font-weight:600;">${Math.round(item.confidence * 100)}%</span>
                    </div>
                </td>
                <td style="color:var(--text-muted);">${new Date(item.timestamp).toLocaleDateString('en-US', {month: 'short', day: 'numeric', year: 'numeric'})}</td>
            `;
            tbody.appendChild(tr);
        });
    }
}
