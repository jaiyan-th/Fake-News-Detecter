class Dashboard {
    constructor() {
        this.resultsPanel = document.getElementById('results-panel');
        this.loadingIndicator = document.getElementById('loading-indicator');
        this.steps = document.querySelectorAll('.pipeline-progress .step');
    }

    showLoading() {
        this.resultsPanel.classList.add('hidden');
        this.loadingIndicator.classList.remove('hidden');
        this.resetSteps();

        let currentStep = 0;
        this.progressInterval = setInterval(() => {
            if (currentStep < this.steps.length) {
                this.steps.forEach(step => step.classList.remove('active'));
                this.steps[currentStep].classList.add('active');
                currentStep++;
            }
        }, 800);
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

        // Check if data exists and has required fields
        if (!data || typeof data !== 'object') {
            this.renderError('Invalid response data received from server');
            return;
        }

        if (!data.success) {
            this.renderError(data.error || 'Failed to analyze the input.');
            return;
        }

        // Validate required fields
        if (!data.prediction || data.confidence === undefined) {
            this.renderError('Incomplete analysis data received from server');
            return;
        }

        const verdictBanner = document.getElementById('verdict-banner');
        verdictBanner.className = 'verdict-banner ' + data.prediction.toLowerCase();

        document.getElementById('prediction-text').textContent = data.prediction;
        
        // Handle confidence display
        const confidencePercent = typeof data.confidence === 'number' 
            ? Math.round(data.confidence * 100) 
            : parseInt(data.confidence) || 0;
        document.getElementById('confidence-score').textContent = confidencePercent + '%';
        
        // Show Multi-Model AI badge
        document.getElementById('domain-badge').textContent = 'Multi-Model AI';
        document.getElementById('explanation-text').textContent = data.explanation || 'No explanation available';

        // Only show LLM analysis for URL analysis
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
                
                // Handle different source formats
                const sourceTitle = source.title || source.article_title || 'Untitled';
                const sourceUrl = source.url || source.article_url || '#';
                const sourceName = source.source || 'Unknown Source';
                const similarity = source.similarity || '';
                const isTrusted = source.is_trusted ? ' (Trusted)' : '';
                
                div.innerHTML = `
                    <strong>${sourceName}${isTrusted} ${similarity}</strong>
                    <p>${sourceTitle}</p>
                    <a href="${sourceUrl}" target="_blank" rel="noopener noreferrer">View Source</a>
                `;
                sourcesList.appendChild(div);
            });
        } else {
            sourcesList.innerHTML = '<p>No reliable sources found for this claim.</p>';
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
