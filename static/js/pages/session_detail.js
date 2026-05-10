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
        referencing: '레퍼런스 수집', abstracting: '추상화', generating: '초안 이미지 생성', documenting: '보고서 작성',
        review_ready: '완료', failed: '실패'
    };

    // Stage list shown in left sidebar (visual progress)
    const STAGES = [
        { key: 'brief_input',  label: '브리프',  tab: 'brief'    },
        { key: 'researching',  label: '조사',    tab: 'research' },
        { key: 'concepting',   label: '컨셉',    tab: 'concepts' },
        { key: 'generating',   label: '생성',    tab: 'output'   },
        { key: 'review_ready', label: '보고서',  tab: 'spec'     }
    ];

    const INPUT_TABS = [
        { tab: 'brief',    label: '브리프' }
    ];
    const OUTPUT_TABS = [
        { tab: 'research', label: '트렌드·레퍼런스', stage: 'researching' },
        { tab: 'concepts', label: '컨셉',          stage: 'concepting'  },
        { tab: 'output',   label: '생성 이미지',     stage: 'generating'  },
        { tab: 'spec',     label: '보고서',        stage: 'review_ready' }
    ];

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

    function _isOutputLocked() {
        const s = state.session && state.session.pipeline_stage;
        // 결과 탭은 파이프라인이 실제로 진행되어 결과가 있는 상태에서만 활성
        return !s || s === 'brief_input';
    }

    function _renderTabButton(t, locked) {
        const isActive = t.tab === state.activeTab;
        const cls = 'tab-btn' + (isActive ? ' tab-active' : '') + (locked ? ' tab-locked' : '');
        const onClick = locked
            ? "SessionWorkspace.handleLockedTabClick()"
            : "SessionWorkspace.switchTab('" + t.tab + "')";
        const titleAttr = locked ? '아직 자동 생성이 실행되지 않았습니다. 클릭하면 입력 탭으로 이동합니다.' : t.label;
        const ariaSelected = isActive ? 'true' : 'false';
        const ariaDisabled = locked ? 'true' : 'false';
        const tabIndex = isActive ? '0' : '-1';
        return '<button id="tab-btn-' + t.tab + '" class="' + cls + '" role="tab" aria-selected="' + ariaSelected + '" ' +
            'aria-controls="tab-' + t.tab + '" aria-disabled="' + ariaDisabled + '" ' +
            'tabindex="' + tabIndex + '" data-tab="' + t.tab + '" data-locked="' + (locked ? '1' : '0') + '" ' +
            'onclick="' + onClick + '" title="' + esc(titleAttr) + '">' +
            esc(t.label) + '</button>';
    }

    function handleLockedTabClick() {
        showToast('아직 브리프 단계입니다. 「자동 생성」을 실행하면 결과 탭이 열립니다.', 'error');
        switchTab('brief');
    }

    function buildTabBar() {
        const bar = document.getElementById('ws-tab-bar');
        if (!bar) return;
        const locked = _isOutputLocked();
        if (locked && state.activeTab !== 'brief') state.activeTab = 'brief';
        const visibleTabs = locked ? INPUT_TABS : INPUT_TABS.concat(OUTPUT_TABS);
        bar.setAttribute('role', 'tablist');
        bar.setAttribute('aria-label', '디자인안 작업 단계');
        bar.innerHTML = visibleTabs.map(function (t) { return _renderTabButton(t, false); }).join('');
        // also wire panes
        ['brief'].concat(OUTPUT_TABS.map(function (t) { return t.tab; })).forEach(function (k) {
            const pane = document.getElementById('tab-' + k);
            if (pane) {
                pane.classList.toggle('active', k === state.activeTab);
                pane.setAttribute('role', 'tabpanel');
                pane.setAttribute('aria-labelledby', 'tab-btn-' + k);
                if (k !== state.activeTab) pane.setAttribute('hidden', '');
                else pane.removeAttribute('hidden');
            }
        });
    }

    function _handleTabBarKeydown(e) {
        if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(e.key)) return;
        const bar = document.getElementById('ws-tab-bar');
        if (!bar) return;
        const tabs = Array.from(bar.querySelectorAll('button[role="tab"]')).filter(function (b) { return b.getAttribute('data-locked') !== '1'; });
        if (tabs.length === 0) return;
        const currentIdx = tabs.findIndex(function (t) { return t.getAttribute('data-tab') === state.activeTab; });
        let nextIdx;
        if (e.key === 'ArrowLeft')  nextIdx = (currentIdx - 1 + tabs.length) % tabs.length;
        else if (e.key === 'ArrowRight') nextIdx = (currentIdx + 1) % tabs.length;
        else if (e.key === 'Home')  nextIdx = 0;
        else                        nextIdx = tabs.length - 1;
        e.preventDefault();
        const target = tabs[nextIdx];
        switchTab(target.getAttribute('data-tab'));
        target.focus();
    }

    function switchTab(tabKey) {
        // 결과 탭이 잠긴 상태면 차단
        const isOutput = OUTPUT_TABS.some(function (t) { return t.tab === tabKey; });
        if (isOutput && _isOutputLocked()) {
            showToast('아직 브리프 단계입니다. 「자동 생성」을 실행하면 결과 탭이 열립니다.', 'error');
            return;
        }
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
            case 'research':
                call('loadTrends');
                call('loadReferences');
                call('loadSketches');
                break;
            case 'concepts':    call('loadConcepts'); break;
            case 'output':
                call('loadGenerations');
                call('loadAbstraction');
                break;
            case 'spec':        call('loadSpec'); break;
        }
    }

    // ─── Sidebar stage list ───────────────────────────────────────────────────

    function buildStageList() {
        const pipelineStage = normalizeStage((state.session && state.session.pipeline_stage) || '');
        const stageOrder = STAGES.map(function (s) { return s.key; });
        const currentIdx = stageOrder.indexOf(pipelineStage);

        const outputLocked = _isOutputLocked();
        const visibleStages = outputLocked ? STAGES.slice(0, 1) : STAGES;
        const stageList = document.getElementById('stage-list');
        if (!stageList) {
            updateDecisionPanel();
            return;
        }
        stageList.innerHTML = visibleStages.map(function (s, idx) {
            let indicatorClass = 'pending';
            let indicatorChar = (idx + 1);
            if (idx < currentIdx) { indicatorClass = 'done'; indicatorChar = '✓'; }
            else if (s.key === pipelineStage) { indicatorClass = 'current'; indicatorChar = '●'; }

            const isActive = s.tab === state.activeTab;
            const isOutput = s.tab !== 'brief';
            const disabled = isOutput && outputLocked;
            const aria = isActive ? ' aria-current="true"' : '';
            const disAttr = disabled ? ' disabled aria-disabled="true"' : '';
            const onClick = disabled
                ? "SessionWorkspace.handleLockedTabClick()"
                : "SessionWorkspace.switchTab('" + s.tab + "')";
            return (
                '<button type="button" class="stage-item' + (isActive ? ' active' : '') + (idx < currentIdx ? ' completed' : '') + (disabled ? ' locked' : '') + '" ' +
                'onclick="' + onClick + '"' + aria + disAttr + '>' +
                '<span class="stage-indicator ' + indicatorClass + '" aria-hidden="true">' + indicatorChar + '</span>' +
                '<span>' + esc(s.label) + '</span>' +
                '</button>'
            );
        }).join('');
        updateDecisionPanel();
    }

    function normalizeStage(stage) {
        if (['researching', 'referencing'].includes(stage)) return 'researching';
        if (stage === 'concepting') return 'concepting';
        if (['abstracting', 'generating'].includes(stage)) return 'generating';
        if (['documenting', 'review_ready'].includes(stage)) return 'review_ready';
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
            generation: '추상화 규칙을 선택해 초안을 생성하세요.',
            generating: '초안 이미지 결과와 실패 사유를 확인하세요. 최종안은 검토 의견 입력 후 생성합니다.',
            spec: '기준 이미지를 선택해 디자인 보고서를 생성하세요.',
            documenting: '기준 이미지를 선택해 디자인 보고서를 생성하세요.',
            review_ready: '완료된 디자인 보고서를 확인하세요.',
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
        document.getElementById('session-title-el').textContent = '디자인안 ' + SESSION_ID.slice(0, 4).toUpperCase();
        const briefSummary = document.getElementById('session-brief-summary');
        if (briefSummary && s.brief && s.brief.purpose) {
            briefSummary.textContent = s.brief.purpose;
            briefSummary.style.display = 'block';
        } else if (briefSummary) {
            briefSummary.style.display = 'none';
        }
        const backLink = document.getElementById('back-to-project-link');
        if (backLink && s.project_id) {
            backLink.href = '/projects/' + s.project_id;
        }
        const badge = document.getElementById('session-status-badge');
        badge.textContent = s.status || '활성';
        badge.className = 'badge' + (s.status === 'completed' ? ' badge-success' : '');
        document.getElementById('session-stage-label').textContent = s.pipeline_stage ? ('단계: ' + s.pipeline_stage) : '';
        buildTabBar();
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
            '<label class="brief-label">통합 브리프</label>' +
            '<textarea id="brief-purpose" class="brief-main-input" placeholder="요구 조건, 목표, 분위기, 제약, 원하는 결과물을 한 번에 입력하세요.">' + esc(brief.purpose || '') + '</textarea>' +
            '<div class="brief-meta-grid">' +
            formField('도메인', 'select-domain', 'brief-domain', brief.domain, '') +
            formField('대상 사용자', 'text', 'brief-target-user', brief.target_user, '예: 1인 가구, 디자이너, 이동이 잦은 사용자') +
            formField('사용 형태', 'text', 'brief-use-case', brief.use_case, '예: 책상 위 독서, 휴대, 협소 공간') +
            '</div>' +
            '<div class="brief-run-panel">' +
            '<div><div style="font-size:13px;font-weight:700;color:var(--text-primary);">생성 방식</div><div class="brief-save-status" id="brief-save-status">자동 저장 대기 중</div></div>' +
            '<div class="brief-run-actions">' +
            '<button class="btn btn-primary" onclick="SessionWorkspace.saveAndRun()">자동 생성</button>' +
            '<button class="btn btn-secondary" onclick="SessionWorkspace.toggleManualPanel()">수동 생성</button>' +
            '</div>' +
            '</div>' +
            '<div class="manual-step-panel" id="manual-step-panel">' +
            '<div class="manual-step-title">다음 단계 수동 생성</div>' +
            '<div class="manual-step-actions">' +
            "<button class=\"btn btn-sm btn-outline\" onclick=\"SessionWorkspace.goManualStep('researching', 'research')\">조사 단계</button>" +
            "<button class=\"btn btn-sm btn-outline\" onclick=\"SessionWorkspace.goManualStep('concepting', 'concepts')\">컨셉 단계</button>" +
            "<button class=\"btn btn-sm btn-outline\" onclick=\"SessionWorkspace.goManualStep('generating', 'output')\">생성 단계</button>" +
            '</div>' +
            '</div>' +
            '<table class="brief-options-table">' +
            '<thead><tr><th style="width:190px;">생성 항목</th><th>역할</th><th style="width:42%;">방향 입력</th></tr></thead>' +
            '<tbody>' +
            optionRow('trend', '트렌드 조사', '브리프 관련 근거 텍스트 수집', 'brief-trend-direction', '조사 힌트', true) +
            optionRow('concept', '컨셉 생성', '디자인 방향 후보 생성', 'brief-context', '선호/회피 힌트', true) +
            optionRow('reference', '이미지 레퍼런스', '컨셉에 맞는 시각 이미지 수집', 'brief-reference-direction', '이미지 검색어', true) +
            optionRow('abstract', '디자인 규칙 도출', '형태/구조/소재 규칙화', 'brief-constraints', '유지/변형 요소', true) +
            optionRow('draft-generation', '초안 이미지', '선택 컨셉 기반 초안 생성', 'brief-sketch-output', '초안 스타일 힌트', true) +
            '</tbody></table>' +
            '</div>';
        bindBriefAutoSave();
    }

    function optionRow(key, title, desc, inputId, placeholder, checked) {
        return '<tr>' +
            '<td><label><input type="checkbox" id="opt-' + key + '"' + (checked ? ' checked' : '') + '> <span>' + esc(title) + '</span></label></td>' +
            '<td><div class="option-desc">' + esc(desc) + '</div></td>' +
            '<td><input type="text" id="' + inputId + '" placeholder="' + esc(placeholder) + ' (선택)"></td>' +
            '</tr>';
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
            return '<div class="brief-field"><label>' + esc(labelText) + '</label>' +
                '<select id="' + id + '">' + optHtml + '</select></div>';
        }
        if (type === 'textarea') {
            return '<div><label style="display:block;font-size:var(--font-sm);font-weight:600;margin-bottom:4px;">' + esc(labelText) + '</label>' +
                '<textarea id="' + id + '" placeholder="' + esc(ph) + '" style="min-height:80px;">' + esc(val) + '</textarea></div>';
        }
        return '<div class="brief-field"><label>' + esc(labelText) + '</label>' +
            '<input type="text" id="' + id + '" value="' + esc(val) + '" placeholder="' + esc(ph) + '"></div>';
    }

    let _briefAutoSaveTimer = null;

    function setBriefSaveStatus(text, isError) {
        const el = document.getElementById('brief-save-status');
        if (!el) return;
        el.textContent = text;
        el.style.color = isError ? 'var(--color-danger)' : 'var(--text-muted)';
    }

    function bindBriefAutoSave() {
        const ids = [
            'brief-purpose', 'brief-domain', 'brief-target-user', 'brief-use-case',
            'brief-trend-direction', 'brief-context', 'brief-reference-direction',
            'brief-constraints', 'brief-sketch-output',
            'opt-trend', 'opt-concept', 'opt-reference', 'opt-abstract', 'opt-draft-generation'
        ];
        ids.forEach(function (id) {
            const el = document.getElementById(id);
            if (!el || el._autoSaveBound) return;
            el.addEventListener('input', scheduleBriefAutoSave);
            el.addEventListener('change', scheduleBriefAutoSave);
            el._autoSaveBound = true;
        });
    }

    function scheduleBriefAutoSave() {
        setBriefSaveStatus('자동 저장 중...', false);
        clearTimeout(_briefAutoSaveTimer);
        _briefAutoSaveTimer = setTimeout(function () {
            saveBrief({ silent: true });
        }, 700);
    }

    async function saveBrief(options) {
        const silent = !!(options && options.silent);
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
            setBriefSaveStatus('자동 저장됨', false);
            if (!silent) showToast('브리프가 저장되었습니다.', 'success');
            await loadSession();
            bindBriefAutoSave();
        } catch (err) {
            setBriefSaveStatus('자동 저장 실패', true);
            if (!silent) showToast('브리프 저장 실패: ' + err.message, 'error');
        }
    }

    async function saveAndRun() {
        await saveBrief({ silent: true });
        await startAutoPipeline();
    }

    function toggleManualPanel() {
        const panel = document.getElementById('manual-step-panel');
        if (panel) panel.classList.toggle('open');
    }

    async function goManualStep(stage, tabKey) {
        try {
            await saveBrief({ silent: true });
            const res = await fetch('/api/sessions/' + SESSION_ID + '/stage', {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ pipeline_stage: stage })
            });
            if (!res.ok) throw new Error('단계 이동 실패');
            await loadSession();
            switchTab(tabKey);
        } catch (err) {
            showToast('단계 이동 실패: ' + err.message, 'error');
        }
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
        const generateDrafts = abstraction && isChecked('opt-draft-generation');
        return {
            research: isChecked('opt-trend'),
            concepts: isChecked('opt-concept'),
            references: isChecked('opt-reference'),
            abstraction: abstraction,
            generation: generateDrafts,
            generate_drafts: generateDrafts,
            generate_final_images: false,
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
        const cancelBtn = document.getElementById('auto-cancel-btn');
        if (cancelBtn) cancelBtn.style.display = 'inline-block';
        if (_progressPoller) clearInterval(_progressPoller);
        _progressPoller = setInterval(_pollProgress, 3000);
        _pollProgress();
    }

    async function cancelAutoPipeline() {
        if (!confirm('자동 생성을 취소하시겠습니까?\n\n현재 진행 중인 단계까지만 완료되고 이후 단계는 중단됩니다. 이미 생성된 결과는 유지됩니다.')) {
            return;
        }
        try {
            const res = await fetch('/api/sessions/' + SESSION_ID + '/cancel', { method: 'POST' });
            const data = await res.json();
            if (!res.ok) {
                showToast((data && data.detail) || '취소 요청에 실패했습니다.', 'error');
                return;
            }
            showToast('파이프라인 취소 요청이 전송되었습니다. 현재 단계 완료 후 중단됩니다.', 'success');
            var cancelBtn = document.getElementById('auto-cancel-btn');
            if (cancelBtn) cancelBtn.disabled = true;
        } catch (err) {
            showToast('취소 요청 실패: ' + err.message, 'error');
        }
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
                var cancelBtn = document.getElementById('auto-cancel-btn');
                if (cancelBtn) cancelBtn.style.display = 'none';
                document.getElementById('auto-mode-btn').disabled = false;
                await loadSession();
                lazyLoadTab('spec');
                if (data.pipeline_stage === 'review_ready') {
                    showToast('파이프라인 완료! 보고서를 검토하세요.', 'success');
                } else {
                    const log = data.auto_progress_log || [];
                    const last = log.length > 0 ? log[log.length - 1] : null;
                    const reason = (last && last.note) ? last.note : '실패 원인을 진행률 바에서 확인하세요.';
                    showToast('파이프라인 실패: ' + reason.replace(/^오류:\s*/, ''), 'error');
                }
            }
        } catch (_) {}
    }

    function _renderProgressBar(data) {
        const stage = data.pipeline_stage || '';
        const log = data.auto_progress_log || [];
        const failed = stage === 'failed';
        const completed = stage === 'review_ready';
        const stageEl = document.getElementById('auto-stage-label');
        if (stageEl) stageEl.textContent = AUTO_STAGE_LABELS[stage] || stage;

        const pipeline = ['researching', 'concepting', 'referencing', 'abstracting', 'generating', 'documenting', 'review_ready'];
        const completedStages = log.map(function (e) { return e.stage; });
        const doneCount = pipeline.filter(function (s) { return completedStages.includes(s) || (completed && s === 'review_ready'); }).length;
        const pct = completed ? 100 : Math.min(100, Math.round((doneCount / pipeline.length) * 100));

        const fill = document.getElementById('auto-progress-fill');
        if (fill) {
            fill.style.width = pct + '%';
            fill.classList.toggle('is-running', !completed && !failed);
            if (failed) fill.style.background = 'linear-gradient(90deg,#ef4444,#f97316)';
            else if (completed) fill.style.background = 'linear-gradient(90deg,#10b981,#22c55e)';
            else fill.style.background = 'linear-gradient(90deg,#3b82f6,#06b6d4)';
        }
        const pctEl = document.getElementById('auto-progress-percent');
        if (pctEl) pctEl.textContent = pct + '%';
        const cntEl = document.getElementById('auto-progress-count');
        if (cntEl) cntEl.textContent = doneCount + '/' + pipeline.length;

        const stepsEl = document.getElementById('auto-progress-steps');
        if (stepsEl) {
            const stageToTab = { researching: 'research', concepting: 'concepts', referencing: 'research',
                                 abstracting: 'output',  generating: 'output',   documenting: 'spec', review_ready: 'spec' };
            stepsEl.setAttribute('role', 'list');
            stepsEl.innerHTML = pipeline.map(function (s) {
                const done = completedStages.includes(s) || (completed && s === 'review_ready');
                const isCurrent = !done && !failed && s === stage;
                const isFailedHere = failed && s === stage;
                let cls = 'mc-step pending';
                let icon = '○';
                let aria = '대기';
                if (done) { cls = 'mc-step done'; icon = '✓'; aria = '완료'; }
                else if (isFailedHere) { cls = 'mc-step failed'; icon = '✕'; aria = '실패'; }
                else if (isCurrent) { cls = 'mc-step current'; icon = '⟳'; aria = '진행 중'; }
                const tab = stageToTab[s];
                const clickable = done && tab;
                const tag = clickable ? 'button' : 'span';
                const onclick = clickable ? ' onclick="SessionWorkspace.switchTab(\'' + tab + '\')"' : '';
                const role = ' role="listitem"';
                const ariaLabel = ' aria-label="' + esc((AUTO_STAGE_LABELS[s] || s) + ' (' + aria + ')' + (clickable ? ' — 클릭하면 결과 탭으로 이동' : '')) + '"';
                const cursor = clickable ? ' style="cursor:pointer;"' : '';
                const typeAttr = clickable ? ' type="button"' : '';
                return '<' + tag + ' class="' + cls + '"' + typeAttr + role + ariaLabel + onclick + cursor + '>' +
                    '<span class="mc-step-icon" aria-hidden="true">' + icon + '</span>' + esc(AUTO_STAGE_LABELS[s] || s) + '</' + tag + '>';
            }).join('');
        }

        const noteEl = document.getElementById('auto-latest-note');
        if (noteEl) {
            if (failed) {
                const errMsg = data.failure_reason || (log.length > 0 ? (log[log.length - 1].note || '') : '');
                noteEl.innerHTML = '<span style="color:#991b1b;font-weight:600;">⚠ 실패</span> ' + esc(errMsg || '오류가 발생했습니다.');
            } else if (log.length > 0) {
                const last = log[log.length - 1];
                noteEl.textContent = last.note || '';
            }
        }
    }

    // ─── Init & reload ────────────────────────────────────────────────────────

    async function init() {
        buildTabBar();
        const tabBar = document.getElementById('ws-tab-bar');
        if (tabBar && !tabBar._kbBound) { tabBar.addEventListener('keydown', _handleTabBarKeydown); tabBar._kbBound = true; }
        if (!document._mcEscBound) {
            document.addEventListener('keydown', function (e) {
                if (e.key !== 'Escape') return;
                const dlg = document.getElementById('gen-dialog');
                if (dlg && dlg.style.display === 'flex' && typeof window.SessionWorkspace.closeGenerationDialog === 'function') {
                    window.SessionWorkspace.closeGenerationDialog();
                }
                const imageModal = document.getElementById('gen-image-modal');
                if (imageModal && imageModal.style.display === 'block' && typeof window.SessionWorkspace.closeGenerationImage === 'function') {
                    window.SessionWorkspace.closeGenerationImage();
                }
            });
            document._mcEscBound = true;
        }
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
        handleLockedTabClick: handleLockedTabClick,
        buildTabBar: buildTabBar,
        buildStageList: buildStageList,
        updateDecisionPanel: updateDecisionPanel,

        // brief
        saveBrief: saveBrief,
        saveAndRun: saveAndRun,
        toggleManualPanel: toggleManualPanel,
        goManualStep: goManualStep,

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
        searchDesignReferences: function () {},
        openDesignRef: function () {},
        analyzeReference: function () {},
        loadAbstraction: function () {},
        generateAbstraction: function () {},
        loadGenerations: function () {},
        openGenerationDialog: function () {},
        closeGenerationDialog: function () {},
        closeGenerationImage: function () {},
        submitGeneration: function () {},
        loadSpec: function () {},
        generateSpec: function () {},
        printSpec: function () {},

        startAutoPipeline: startAutoPipeline,
        cancelAutoPipeline: cancelAutoPipeline,
        reload: reload
    };

    document.addEventListener('DOMContentLoaded', init);
}());
