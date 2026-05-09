/**
 * Session Workspace — Core Logic
 * Vanilla JS IIFE. Exposes SessionWorkspace to global scope.
 * Split: this file handles state, tabs, brief, chat, init.
 * session_detail_actions.js handles sketch, trend, concepts, refs, abstraction, generation, spec.
 */
(function () {
    'use strict';

    const SESSION_ID = window.SESSION_ID || '';

    // @MX:ANCHOR: [AUTO] Central workspace state — accessed by all tab modules
    // @MX:REASON: All tab renderers and action handlers read/write this state (fan_in >= 8)
    const state = {
        session: null,
        messages: [],
        sketches: [],
        trends: [],
        concepts: [],
        references: [],
        abstractionRules: [],
        generations: [],
        spec: null,
        generationPollers: {},
        activeTab: 'brief'
    };

    const AUTO_STAGE_LABELS = {
        brief_input: '브리프', researching: '트렌드 조사', concepting: '컨셉 생성',
        referencing: '레퍼런스 수집', abstracting: '추상화', generating: '이미지 생성', documenting: '스펙 작성',
        review_ready: '완료', failed: '실패'
    };

    const STAGES = [
        { key: 'brief_input', label: '브리프',       tab: 'brief'   },
        { key: 'researching', label: '자료·컨셉',    tab: 'sources' },
        { key: 'generating',  label: '결과 이미지',  tab: 'output'  },
        { key: 'review_ready', label: '스펙',        tab: 'spec'    }
    ];

    const TABS = STAGES;

    // ─── Utils ────────────────────────────────────────────────────────────────

    function esc(text) {
        const div = document.createElement('div');
        div.textContent = String(text || '');
        return div.innerHTML;
    }

    function showToast(message, type) {
        const toast = document.getElementById('ws-toast');
        if (!toast) return;
        toast.textContent = message;
        toast.style.display = 'block';
        if (type === 'error') {
            toast.style.background = '#fee2e2';
            toast.style.color = '#b91c1c';
            toast.style.border = '1px solid #fca5a5';
        } else {
            toast.style.background = '#d1fae5';
            toast.style.color = '#065f46';
            toast.style.border = '1px solid #6ee7b7';
        }
        clearTimeout(toast._timer);
        toast._timer = setTimeout(function () { toast.style.display = 'none'; }, 3000);
    }

    function skeletonBlock(height) {
        return '<div class="skeleton" style="height:' + (height || 80) + 'px;border-radius:6px;margin-bottom:8px;"></div>';
    }

    function formatTime(dateStr) {
        if (!dateStr) return '';
        return new Date(dateStr).toLocaleString('ko-KR');
    }

    // ─── Tabs ─────────────────────────────────────────────────────────────────

    function buildTabBar() {
        const bar = document.getElementById('ws-tab-bar');
        bar.innerHTML = TABS.map(function (t) {
            return '<button class="tab-btn' + (t.tab === state.activeTab ? ' tab-active' : '') + '" ' +
                'onclick="SessionWorkspace.switchTab(\'' + t.tab + '\')">' + esc(t.label) + '</button>';
        }).join('');
    }

    function switchTab(tabKey) {
        document.querySelectorAll('.ws-tab-pane').forEach(function (el) { el.classList.remove('active'); });
        const pane = document.getElementById('tab-' + tabKey);
        if (pane) pane.classList.add('active');
        state.activeTab = tabKey;
        buildTabBar();
        buildStageList();
        lazyLoadTab(tabKey);
    }

    function lazyLoadTab(tabKey) {
        const sw = window.SessionWorkspace || {};
        const call = function (name) {
            if (typeof sw[name] === 'function') {
                try { sw[name](); } catch (e) { console.error(name + ' failed:', e); }
            } else {
                console.warn('SessionWorkspace.' + name + ' not yet wired');
            }
        };
        switch (tabKey) {
            case 'chat':        loadMessages(); break;
            case 'sources':
                call('loadSketches');
                call('loadTrends');
                call('loadConcepts');
                call('loadReferences');
                break;
            case 'output':
                call('loadAbstraction');
                call('loadGenerations');
                break;
            case 'sketch':      call('loadSketches'); break;
            case 'trend':       call('loadTrends'); break;
            case 'concepts':    call('loadConcepts'); break;
            case 'references':  call('loadReferences'); break;
            case 'abstraction': call('loadAbstraction'); break;
            case 'generation':  call('loadGenerations'); break;
            case 'spec':        call('loadSpec'); break;
        }
    }

    // ─── Sidebar stage list ───────────────────────────────────────────────────

    function buildStageList() {
        const pipelineStage = normalizeStage((state.session && state.session.pipeline_stage) || '');
        const stageOrder = STAGES.map(function (s) { return s.key; });
        const currentIdx = stageOrder.indexOf(pipelineStage);

        document.getElementById('stage-list').innerHTML = STAGES.map(function (s, idx) {
            let indicatorClass = 'pending';
            let indicatorChar = (idx + 1);
            if (idx < currentIdx) { indicatorClass = 'done'; indicatorChar = '✓'; }
            else if (s.key === pipelineStage) { indicatorClass = 'current'; indicatorChar = '●'; }

            const isActive = s.tab === state.activeTab;
            return (
                '<div class="stage-item' + (isActive ? ' active' : '') + (idx < currentIdx ? ' completed' : '') + '" ' +
                'onclick="SessionWorkspace.switchTab(\'' + s.tab + '\')">' +
                '<div class="stage-indicator ' + indicatorClass + '">' + indicatorChar + '</div>' +
                '<span>' + esc(s.label) + '</span>' +
                '</div>'
            );
        }).join('');
        updateDecisionPanel();
    }

    function normalizeStage(stage) {
        if (['researching', 'concepting', 'referencing', 'abstracting'].includes(stage)) return 'researching';
        if (['generating', 'documenting'].includes(stage)) return 'generating';
        if (stage === 'review_ready') return 'review_ready';
        return 'brief_input';
    }

    function updateDecisionPanel() {
        const session = state.session || {};
        const stage = session.pipeline_stage || state.activeTab || 'brief';
        const nextActions = {
            brief: '목적, 도메인, 대상, 결과 형태를 확정하세요.',
            brief_input: '목적, 도메인, 대상, 결과 형태를 확정하세요.',
            sketch: '사용자 스케치가 있으면 업로드하고 AI 해석을 확인하세요.',
            trend: '출처가 있는 트렌드 근거를 검색하세요.',
            researching: '출처가 있는 트렌드 근거를 검색하세요.',
            concepts: '검증된 근거를 바탕으로 컨셉 후보를 생성하세요.',
            concepting: '검증된 근거를 바탕으로 컨셉 후보를 생성하세요.',
            references: '선택한 컨셉과 연결되는 레퍼런스를 수집하세요.',
            referencing: '선택한 컨셉과 연결되는 레퍼런스를 수집하세요.',
            abstraction: '분석된 레퍼런스 또는 스케치에서 추상화 규칙을 생성하세요.',
            abstracting: '분석된 레퍼런스 또는 스케치에서 추상화 규칙을 생성하세요.',
            generation: '추상화 규칙을 선택해 이미지를 생성하세요.',
            generating: '생성 결과와 실패 사유를 확인하세요.',
            spec: '결정 로그와 출처가 포함된 스펙 문서를 생성하세요.',
            documenting: '결정 로그와 출처가 포함된 스펙 문서를 생성하세요.',
            review_ready: '검토 필요 항목과 최종 스펙을 확인하세요.',
            failed: '실패 원인을 확인하고 재시도 가능한 단계부터 다시 실행하세요.'
        };
        setText('decision-current-stage', stage);
        setText('decision-next-action', nextActions[stage] || nextActions[state.activeTab] || '다음 작업을 선택하세요.');
        setText('decision-review-flags', formatReviewFlags(session.review_flags));
        setText('decision-selected-concept', selectedConceptLabel());
        setText('decision-spec-status', state.spec ? ('v' + state.spec.version + ' / ' + state.spec.status) : '미생성');
    }

    function setText(id, value) {
        const el = document.getElementById(id);
        if (el) el.textContent = value || '-';
    }

    function formatReviewFlags(flags) {
        if (!flags) return '없음';
        if (Array.isArray(flags)) return flags.length ? flags.join(', ') : '없음';
        const keys = Object.keys(flags).filter(function (key) { return flags[key]; });
        return keys.length ? keys.join(', ') : '없음';
    }

    function selectedConceptLabel() {
        const selected = state.concepts.find(function (c) { return c.status === 'adopted'; });
        return selected ? selected.name : '미선택';
    }

    // ─── Session header ───────────────────────────────────────────────────────

    async function loadSession() {
        const res = await fetch('/api/sessions/' + SESSION_ID);
        if (!res.ok) {
            showToast('세션 정보 로드 실패', 'error');
            return;
        }
        state.session = await res.json();
        const s = state.session;
        document.getElementById('session-title-el').textContent = (s.brief && s.brief.purpose) ? s.brief.purpose : ('세션 ' + SESSION_ID.slice(0, 8));
        const backLink = document.getElementById('back-to-project-link');
        if (backLink && s.project_id) {
            backLink.href = '/projects/' + s.project_id;
        }
        const badge = document.getElementById('session-status-badge');
        badge.textContent = s.status || '활성';
        badge.className = 'badge' + (s.status === 'completed' ? ' badge-success' : '');
        document.getElementById('session-stage-label').textContent = s.pipeline_stage ? ('단계: ' + s.pipeline_stage) : '';
        buildStageList();
        updateDecisionPanel();
    }

    // ─── Brief ───────────────────────────────────────────────────────────────

    async function loadBrief() {
        const container = document.getElementById('brief-form-container');
        container.innerHTML = skeletonBlock(300);
        const res = await fetch('/api/sessions/' + SESSION_ID);
        if (!res.ok) {
            container.innerHTML = errorBlock('브리프 로드 실패', 'loadBrief()');
            return;
        }
        const session = await res.json();
        state.session = session;
        const brief = session.brief || {};
        renderBriefForm(brief);
    }

    function renderBriefForm(brief) {
        const container = document.getElementById('brief-form-container');
        container.innerHTML =
            '<div class="brief-workbench">' +
            '<div class="brief-primary">' +
            '<label class="brief-label">통합 브리프</label>' +
            '<textarea id="brief-purpose" class="brief-main-input" placeholder="요구 조건, 목표, 분위기, 제약, 원하는 결과물을 한 번에 입력하세요. 스케치/레퍼런스/조사 방향은 있으면 아래 선택 영역에 추가하면 됩니다.">' + esc(brief.purpose || '') + '</textarea>' +
            '<div class="brief-actions">' +
            '<button class="btn btn-primary" onclick="SessionWorkspace.saveBrief()">브리프 저장</button>' +
            '<button class="btn btn-success" onclick="SessionWorkspace.saveAndRun()">저장 후 자동 생성</button>' +
            '</div>' +
            '</div>' +
            '<div class="brief-options">' +
            optionCard('trend', '트렌드 조사', '필요하면 조사 방향을 입력하고, 비워두면 브리프 기반으로 AI가 검색합니다.', 'brief-trend-direction', '조사 방향 또는 키워드') +
            optionCard('concept', '컨셉', '사용자 컨셉이 있으면 적고, 없으면 AI가 후보를 제안합니다.', 'brief-context', '선호 컨셉, 피해야 할 방향') +
            optionCard('reference', '레퍼런스', '직접 검색하거나 스케치 기반으로 찾을 수 있습니다.', 'brief-reference-direction', '레퍼런스 검색어') +
            optionCard('abstract', '추상화', '필요한 경우 자료·스케치에서 규칙을 추출해 이미지 생성에 씁니다.', 'brief-constraints', '유지/변형할 요소') +
            optionCard('generation', '이미지 생성', '켜두면 추상화 이후 최종 이미지를 바로 생성합니다.', 'brief-result-form', '원하는 이미지 스타일 또는 산출물') +
            '<div class="brief-advanced">' +
            formField('도메인', 'select-domain', 'brief-domain', brief.domain, '') +
            formField('대상 사용자', 'text', 'brief-target-user', brief.target_user, '선택 입력') +
            formField('사용 형태', 'text', 'brief-use-case', brief.use_case, '선택 입력') +
            '</div>' +
            '</div>' +
            '</div>' +
            '</div>';
    }

    function optionCard(key, title, desc, inputId, placeholder) {
        const checked = key === 'trend' || key === 'concept' || key === 'abstract';
        return '<div class="brief-option-card">' +
            '<label><input type="checkbox" id="opt-' + key + '"' + (checked ? ' checked' : '') + '> ' + esc(title) + '</label>' +
            '<p>' + esc(desc) + '</p>' +
            '<input type="text" id="' + inputId + '" placeholder="' + esc(placeholder) + '">' +
            '</div>';
    }

    function formField(labelText, type, id, value, placeholder) {
        const val = value || '';
        const ph = placeholder || '';
        if (type === 'select-domain') {
            const opts = ['industrial', 'product_service', 'visual', 'advertising', 'general'];
            const optHtml = opts.map(function (o) {
                const labels = { industrial: '산업', product_service: '제품·서비스', visual: '시각', advertising: '광고', general: '일반' };
                return '<option value="' + o + '"' + (val === o ? ' selected' : '') + '>' + labels[o] + '</option>';
            }).join('');
            return '<div><label style="display:block;font-size:var(--font-sm);font-weight:600;margin-bottom:4px;">' + esc(labelText) + '</label>' +
                '<select id="' + id + '" style="width:100%;">' + optHtml + '</select></div>';
        }
        if (type === 'textarea') {
            return '<div><label style="display:block;font-size:var(--font-sm);font-weight:600;margin-bottom:4px;">' + esc(labelText) + '</label>' +
                '<textarea id="' + id + '" placeholder="' + esc(ph) + '" style="min-height:80px;">' + esc(val) + '</textarea></div>';
        }
        return '<div><label style="display:block;font-size:var(--font-sm);font-weight:600;margin-bottom:4px;">' + esc(labelText) + '</label>' +
            '<input type="text" id="' + id + '" value="' + esc(val) + '" placeholder="' + esc(ph) + '"></div>';
    }

    async function saveBrief() {
        const payload = {
            purpose: getVal('brief-purpose'),
            domain: getVal('brief-domain'),
            target_user: getVal('brief-target-user'),
            context: getVal('brief-context'),
            constraints: getVal('brief-constraints'),
            use_case: getVal('brief-use-case'),
            result_form: getVal('brief-result-form')
        };
        try {
            const res = await fetch('/api/sessions/' + SESSION_ID + '/brief', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            if (!res.ok) throw new Error('저장 실패');
            showToast('브리프가 저장되었습니다.', 'success');
            await loadSession();
        } catch (err) {
            showToast('브리프 저장 실패: ' + err.message, 'error');
        }
    }

    async function saveAndRun() {
        await saveBrief();
        await startAutoPipeline();
    }

    function getVal(id) {
        const el = document.getElementById(id);
        return el ? el.value.trim() : '';
    }

    // ─── Chat ─────────────────────────────────────────────────────────────────

    async function loadMessages() {
        const container = document.getElementById('chat-messages');
        container.innerHTML = skeletonBlock(60) + skeletonBlock(40) + skeletonBlock(60);
        try {
            const res = await fetch('/api/sessions/' + SESSION_ID + '/messages');
            if (!res.ok) throw new Error('메시지 로드 실패');
            const msgs = await res.json();
            state.messages = msgs;
            renderMessages(msgs);
        } catch (err) {
            container.innerHTML = errorBlock('메시지 로드 실패', 'loadMessages()');
        }
    }

    function renderMessages(msgs) {
        const container = document.getElementById('chat-messages');
        if (!msgs || msgs.length === 0) {
            container.innerHTML = '<div style="color:var(--text-muted);font-size:var(--font-sm);text-align:center;padding:2rem;">대화를 시작해보세요. AI가 디자인 아이디어를 도와드립니다.</div>';
            return;
        }
        container.innerHTML = msgs.map(function (m) {
            const isUser = m.role === 'user';
            // evidence_links: array of URLs from pipeline stages
            const links = m.evidence_links || m.citations || [];
            const evidenceHtml = links.length > 0
                ? '<div style="font-size:var(--font-xs);color:var(--text-muted);margin-top:6px;border-top:1px solid rgba(0,0,0,0.08);padding-top:4px;">📎 근거: ' +
                  links.slice(0, 5).map(function (item) {
                      const url = typeof item === 'string' ? item : (item.url || '#');
                      const label = typeof item === 'string' ? url.replace(/^https?:\/\//, '').split('/')[0] : (item.title || url);
                      return '<a href="' + esc(url) + '" target="_blank" rel="noopener" style="color:var(--color-primary);">' + esc(label) + '</a>';
                  }).join(' · ') + '</div>'
                : '';
            const stageTag = (m.stage && m.stage !== 'null')
                ? '<span style="font-size:10px;background:#e0f2fe;color:#0369a1;border-radius:3px;padding:1px 5px;margin-left:4px;">' + esc(AUTO_STAGE_LABELS[m.stage] || m.stage) + '</span>'
                : '';
            return (
                '<div class="msg-bubble ' + (isUser ? 'user' : 'ai') + '">' +
                '<div class="bubble-body">' + esc(m.content) + evidenceHtml + '</div>' +
                '<div class="bubble-meta">' + (isUser ? '나' : 'AI') + stageTag + ' · ' + formatTime(m.created_at) + '</div>' +
                '</div>'
            );
        }).join('');
        container.scrollTop = container.scrollHeight;
    }

    // @MX:WARN: [AUTO] Async chat send without abort/error boundary
    // @MX:REASON: Network failure mid-send leaves UI in disabled state — needs finally block
    async function sendMessage() {
        const input = document.getElementById('chat-input');
        const btn = document.getElementById('chat-send-btn');
        const content = input.value.trim();
        if (!content) return;

        input.disabled = true;
        btn.disabled = true;
        btn.textContent = '전송 중...';

        const optimistic = { role: 'user', content: content, created_at: new Date().toISOString() };
        state.messages.push(optimistic);
        renderMessages(state.messages);

        try {
            const res = await fetch('/api/sessions/' + SESSION_ID + '/messages', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ role: 'user', content: content, stage: state.activeTab })
            });
            if (!res.ok) throw new Error('전송 실패');
            input.value = '';
            await loadMessages();
        } catch (err) {
            showToast('메시지 전송 실패: ' + err.message, 'error');
            state.messages.pop();
            renderMessages(state.messages);
        } finally {
            input.disabled = false;
            btn.disabled = false;
            btn.textContent = '전송';
            input.focus();
        }
    }

    // ─── Shared error block ───────────────────────────────────────────────────

    function errorBlock(msg, retryFn) {
        return '<div style="color:var(--color-danger);font-size:var(--font-sm);padding:1rem;background:#fee2e2;border-radius:6px;">' +
            esc(msg) + ' — <button class="btn btn-sm btn-outline" onclick="' + retryFn + '" style="margin-left:8px;">재시도</button></div>';
    }

    // ─── Auto pipeline ────────────────────────────────────────────────────────

    let _progressPoller = null;

    async function startAutoPipeline() {
        const options = collectRunOptions();
        const res = await fetch('/api/sessions/' + SESSION_ID + '/auto', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(options)
        });
        const data = await res.json();
        if (!res.ok) {
            showToast((data && data.detail) || '자동 진행을 시작할 수 없습니다.', 'error');
            return;
        }
        showToast('자동 파이프라인을 시작했습니다.', 'success');
        document.getElementById('auto-mode-btn').disabled = true;
        _startProgressPolling();
    }

    function collectRunOptions() {
        const abstraction = isChecked('opt-abstract');
        const generation = abstraction && isChecked('opt-generation');
        return {
            research: isChecked('opt-trend'),
            concepts: isChecked('opt-concept'),
            references: isChecked('opt-reference'),
            abstraction: abstraction,
            generation: generation,
            spec: true
        };
    }

    function isChecked(id) {
        const el = document.getElementById(id);
        return !el || el.checked;
    }

    function _startProgressPolling() {
        const bar = document.getElementById('auto-progress-bar');
        if (bar) bar.style.display = 'block';
        if (_progressPoller) clearInterval(_progressPoller);
        _progressPoller = setInterval(_pollProgress, 3000);
        _pollProgress();
    }

    async function _pollProgress() {
        try {
            const res = await fetch('/api/sessions/' + SESSION_ID + '/progress');
            if (!res.ok) return;
            const data = await res.json();
            _renderProgressBar(data);

            if (data.pipeline_stage === 'review_ready' || data.pipeline_stage === 'failed') {
                clearInterval(_progressPoller);
                _progressPoller = null;
                const bar = document.getElementById('auto-progress-bar');
                if (bar) {
                    const done = data.pipeline_stage === 'review_ready';
                    bar.style.borderColor = done ? 'var(--color-success)' : 'var(--color-danger)';
                }
                document.getElementById('auto-mode-btn').disabled = false;
                await loadSession();
                lazyLoadTab('spec');
                showToast(data.pipeline_stage === 'review_ready' ? '파이프라인 완료! 스펙을 검토하세요.' : '파이프라인 실패. 실패 원인을 확인하세요.', data.pipeline_stage === 'review_ready' ? 'success' : 'error');
            }
        } catch (_) {}
    }

    function _renderProgressBar(data) {
        const stage = data.pipeline_stage || '';
        const log = data.auto_progress_log || [];
        const stageEl = document.getElementById('auto-stage-label');
        if (stageEl) stageEl.textContent = AUTO_STAGE_LABELS[stage] || stage;

        const stepsEl = document.getElementById('auto-progress-steps');
        if (stepsEl) {
            const completedStages = log.map(function (e) { return e.stage; });
            const pipeline = ['researching', 'concepting', 'referencing', 'abstracting', 'generating', 'documenting', 'review_ready'];
            stepsEl.innerHTML = pipeline.map(function (s) {
                const done = completedStages.includes(s);
                const isCurrent = s === stage;
                const color = done ? '#d1fae5' : isCurrent ? '#dbeafe' : '#f3f4f6';
                const textColor = done ? '#065f46' : isCurrent ? '#1e40af' : '#6b7280';
                return '<span style="background:' + color + ';color:' + textColor + ';border-radius:4px;padding:2px 8px;font-size:11px;font-weight:600;">' +
                    (done ? '✓ ' : isCurrent ? '⟳ ' : '') + esc(AUTO_STAGE_LABELS[s] || s) + '</span>';
            }).join('');
        }

        const noteEl = document.getElementById('auto-latest-note');
        if (noteEl && log.length > 0) {
            const last = log[log.length - 1];
            noteEl.textContent = last.note || '';
        }
    }

    // ─── Init & reload ────────────────────────────────────────────────────────

    async function init() {
        buildTabBar();
        buildStageList();
        await loadSession();
        await loadBrief();
        // resume polling if session was already in auto mode mid-pipeline
        if (state.session && state.session.mode === 'auto') {
            const s = state.session.pipeline_stage;
            if (s && s !== 'review_ready' && s !== 'failed' && s !== 'brief_input') {
                _startProgressPolling();
            }
        }
    }

    async function reload() {
        await loadSession();
        lazyLoadTab(state.activeTab);
    }

    // ─── Public API ───────────────────────────────────────────────────────────

    window.SessionWorkspace = {
        // state access (used by actions file)
        SESSION_ID: SESSION_ID,
        state: state,
        esc: esc,
        showToast: showToast,
        skeletonBlock: skeletonBlock,
        errorBlock: errorBlock,
        formatTime: formatTime,
        getVal: getVal,
        loadMessages: loadMessages,
        renderMessages: renderMessages,

        // tab & nav
        switchTab: switchTab,
        buildTabBar: buildTabBar,
        buildStageList: buildStageList,
        updateDecisionPanel: updateDecisionPanel,

        // brief
        saveBrief: saveBrief,
        saveAndRun: saveAndRun,

        // chat
        sendMessage: sendMessage,

        // stubs — implemented in session_detail_actions.js
        loadSketches: function () {},
        uploadSketch: function () {},
        analyzeSketch: function () {},
        loadTrends: function () {},
        searchTrends: function () {},
        loadConcepts: function () {},
        generateConcepts: function () {},
        decideConcept: function () {},
        loadReferences: function () {},
        searchReferences: function () {},
        analyzeReference: function () {},
        loadAbstraction: function () {},
        generateAbstraction: function () {},
        loadGenerations: function () {},
        openGenerationDialog: function () {},
        closeGenerationDialog: function () {},
        submitGeneration: function () {},
        loadSpec: function () {},
        generateSpec: function () {},
        printSpec: function () {},

        startAutoPipeline: startAutoPipeline,
        reload: reload
    };

    document.addEventListener('DOMContentLoaded', init);
}());
