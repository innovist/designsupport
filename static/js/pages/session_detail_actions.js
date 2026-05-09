/**
 * Session Workspace — Actions
 * Depends on session_detail.js (SessionWorkspace must be initialised first).
 * Handles: sketch, trend, concepts, references, abstraction, generation, spec.
 */
(function () {
    'use strict';

    function ws() { return window.SessionWorkspace; }
    function SID() { return ws().SESSION_ID; }
    function state() { return ws().state; }
    function esc(v) { return ws().esc(v); }
    function showToast(m, t) { ws().showToast(m, t); }
    function skeleton(h) { return ws().skeletonBlock(h); }
    function errBlock(m, fn) { return ws().errorBlock(m, fn); }
    function fmtTime(d) { return ws().formatTime(d); }

    // ─── Sketch ───────────────────────────────────────────────────────────────

    async function loadSketches() {
        const container = document.getElementById('sketch-list');
        container.innerHTML = skeleton(120) + skeleton(120);
        try {
            const res = await fetch('/api/sessions/' + SID() + '/sketches');
            if (!res.ok) throw new Error('스케치 로드 실패');
            const sketches = await res.json();
            state().sketches = sketches;
            renderSketches(sketches);
        } catch (err) {
            container.innerHTML = errBlock('스케치 로드 실패', 'SessionWorkspace.loadSketches()');
        }
    }

    function renderSketches(sketches) {
        const container = document.getElementById('sketch-list');
        if (!sketches || sketches.length === 0) {
            container.innerHTML = '<div style="color:var(--text-muted);font-size:var(--font-sm);text-align:center;padding:2rem;">스케치가 없습니다. 위에서 이미지를 업로드하세요.</div>';
            return;
        }
        container.innerHTML = sketches.map(function (sk) {
            const analysis = sk.analysis || null;
            const analysisHtml = analysis
                ? '<div style="background:var(--bg-secondary);border-radius:6px;padding:12px;margin-top:10px;">' +
                  '<div style="display:flex;align-items:center;gap:6px;margin-bottom:6px;">' +
                  '<span style="font-size:var(--font-xs);font-weight:700;color:var(--text-secondary);">AI 해석</span>' +
                  '<span class="badge badge-hypothesis">가설</span>' +
                  '</div>' +
                  (analysis.intent ? '<div style="font-size:var(--font-sm);margin-bottom:4px;"><strong>의도:</strong> ' + esc(analysis.intent) + '</div>' : '') +
                  (analysis.form_elements && analysis.form_elements.length
                      ? '<div style="font-size:var(--font-sm);margin-bottom:4px;"><strong>형태 요소:</strong> ' + esc(analysis.form_elements.join(', ')) + '</div>' : '') +
                  (analysis.keep_elements && analysis.keep_elements.length
                      ? '<div style="font-size:var(--font-sm);margin-bottom:4px;"><strong>유지 요소:</strong> ' + esc(analysis.keep_elements.join(', ')) + '</div>' : '') +
                  (analysis.vary_elements && analysis.vary_elements.length
                      ? '<div style="font-size:var(--font-sm);margin-bottom:4px;"><strong>변형 요소:</strong> ' + esc(analysis.vary_elements.join(', ')) + '</div>' : '') +
                  (analysis.questions_for_user && analysis.questions_for_user.length
                      ? '<div style="font-size:var(--font-sm);"><strong>질문:</strong> ' + esc(analysis.questions_for_user.join(' / ')) + '</div>' : '') +
                  '</div>'
                : '';
            return (
                '<div class="card" style="margin-bottom:0;">' +
                '<div style="display:grid;grid-template-columns:180px 1fr;gap:12px;">' +
                '<div><img src="' + esc(sk.image_url || sk.thumbnail_url || '') + '" alt="스케치" style="width:100%;border-radius:6px;object-fit:cover;aspect-ratio:1;"></div>' +
                '<div>' +
                '<div style="font-weight:600;font-size:var(--font-sm);margin-bottom:4px;">' + esc(sk.description || '스케치') + '</div>' +
                '<div style="font-size:var(--font-xs);color:var(--text-muted);margin-bottom:10px;">' + fmtTime(sk.created_at) + '</div>' +
                analysisHtml +
                '<div style="display:flex;gap:8px;margin-top:10px;">' +
                '<button class="btn btn-sm btn-secondary" onclick="SessionWorkspace.analyzeSketch(\'' + esc(sk.id) + '\')">분석 시작</button>' +
                '<button class="btn btn-sm btn-outline" onclick="SessionWorkspace.switchTab(\'references\')">레퍼런스 검색에 사용</button>' +
                '</div>' +
                '</div>' +
                '</div>' +
                '</div>'
            );
        }).join('');
    }

    async function uploadSketch(file) {
        if (!file) return;
        const zone = document.getElementById('sketch-upload-zone');
        zone.innerHTML = '<div style="color:var(--text-muted);font-size:var(--font-sm);">업로드 중...</div>';
        try {
            const form = new FormData();
            form.append('file', file);
            form.append('description', file.name);
            const res = await fetch('/api/sessions/' + SID() + '/sketches', { method: 'POST', body: form });
            if (!res.ok) throw new Error('업로드 실패');
            showToast('스케치가 업로드되었습니다.', 'success');
            await loadSketches();
        } catch (err) {
            showToast('업로드 실패: ' + err.message, 'error');
        } finally {
            zone.innerHTML = '<div style="font-size:2rem;margin-bottom:8px;">📎</div><div style="font-weight:600;font-size:var(--font-sm);">스케치 이미지 업로드</div><div style="font-size:var(--font-xs);color:var(--text-muted);margin-top:4px;">클릭하거나 파일을 드래그하세요 (PNG, JPG, WEBP)</div>';
        }
    }

    async function analyzeSketch(sketchId) {
        showToast('스케치 분석 중...', 'success');
        try {
            const res = await fetch('/api/sketches/' + sketchId + '/analyze', { method: 'POST' });
            if (!res.ok) throw new Error('분석 실패');
            showToast('분석이 완료되었습니다.', 'success');
            await loadSketches();
        } catch (err) {
            showToast('분석 실패: ' + err.message, 'error');
        }
    }

    // ─── Trend ────────────────────────────────────────────────────────────────

    async function loadTrends() {
        const container = document.getElementById('trend-results');
        container.innerHTML = skeleton(80) + skeleton(80) + skeleton(80);
        try {
            const res = await fetch('/api/sessions/' + SID() + '/trends');
            if (!res.ok) throw new Error('트렌드 로드 실패');
            const data = await res.json();
            const trends = data.insights || [];
            state().trends = trends;
            renderTrends(trends);
        } catch (err) {
            container.innerHTML = errBlock('트렌드 로드 실패', 'SessionWorkspace.loadTrends()');
        }
    }

    async function searchTrends() {
        const query = ws().getVal('trend-search-input');
        const domain = ws().getVal('trend-domain-filter');
        if (!query) { showToast('검색어를 입력하세요.', 'error'); return; }
        const container = document.getElementById('trend-results');
        container.innerHTML = skeleton(80) + skeleton(80) + skeleton(80);
        try {
            const res = await fetch('/api/sessions/' + SID() + '/trends/search', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: query, domain: domain || '' })
            });
            if (!res.ok) throw new Error('검색 실패');
            const data = await res.json();
            const trends = data.insights || [];
            state().trends = trends;
            renderTrends(trends);
        } catch (err) {
            container.innerHTML = errBlock('트렌드 검색 실패', 'SessionWorkspace.loadTrends()');
        }
    }

    function renderTrends(trends) {
        const container = document.getElementById('trend-results');
        if (!trends || trends.length === 0) {
            container.innerHTML = '<div style="color:var(--text-muted);font-size:var(--font-sm);text-align:center;padding:2rem;">트렌드 인사이트가 없습니다. 검색어를 입력하거나 트렌드 소스를 추가하세요.</div>';
            return;
        }
        container.innerHTML = trends.map(function (t) {
            const hypoHtml = t.is_hypothesis
                ? '<span class="badge badge-hypothesis" style="margin-right:6px;">가설</span>'
                : '';
            const quoteHtml = t.evidence_quote
                ? '<blockquote style="border-left:3px solid var(--color-primary);padding-left:10px;margin:8px 0;font-style:italic;color:var(--text-secondary);font-size:var(--font-xs);">' + esc(t.evidence_quote) + '</blockquote>'
                : '';
            return (
                '<div class="card" style="margin-bottom:0;">' +
                '<div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:6px;">' +
                '<div>' + hypoHtml + '<span style="font-weight:600;font-size:var(--font-sm);">' + esc(t.summary || t.title || '') + '</span></div>' +
                (t.source_url ? '<a href="' + esc(t.source_url) + '" target="_blank" rel="noopener" style="font-size:var(--font-xs);color:var(--color-primary);white-space:nowrap;">출처 ↗</a>' : '') +
                '</div>' +
                quoteHtml +
                '</div>'
            );
        }).join('');
    }

    // ─── Concepts ─────────────────────────────────────────────────────────────

    async function loadConcepts() {
        const container = document.getElementById('concepts-list');
        container.innerHTML = skeleton(100) + skeleton(100);
        try {
            const res = await fetch('/api/sessions/' + SID() + '/concepts');
            if (!res.ok) throw new Error('컨셉 로드 실패');
            const concepts = await res.json();
            state().concepts = concepts;
            renderConcepts(concepts);
            ws().updateDecisionPanel();
        } catch (err) {
            container.innerHTML = errBlock('컨셉 로드 실패', 'SessionWorkspace.loadConcepts()');
        }
    }

    async function generateConcepts() {
        const btn = document.getElementById('gen-concepts-btn');
        btn.disabled = true;
        btn.textContent = '생성 중...';
        const container = document.getElementById('concepts-list');
        container.innerHTML = skeleton(100) + skeleton(100) + skeleton(100);
        try {
            const res = await fetch('/api/sessions/' + SID() + '/concepts', { method: 'POST' });
            const body = await res.json().catch(function () { return null; });
            if (!res.ok) {
                const detail = (body && (body.detail || body.message)) || ('HTTP ' + res.status);
                throw new Error(detail);
            }
            state().concepts = body;
            renderConcepts(body);
            ws().updateDecisionPanel();
            showToast('컨셉 후보가 생성되었습니다.', 'success');
        } catch (err) {
            container.innerHTML = '<div style="padding:14px;border:1px solid #fca5a5;background:#fee2e2;border-radius:4px;color:#7f1d1d;font-size:13px;line-height:1.5;">' +
                '<div style="font-weight:700;margin-bottom:4px;">컨셉 생성 실패</div>' +
                '<div>' + esc(err.message || '알 수 없는 오류') + '</div>' +
                '<div style="margin-top:8px;font-size:12px;color:#991b1b;">브리프 작성을 완료한 뒤 다시 시도하거나, 트렌드 조사를 먼저 실행하세요.</div>' +
                '</div>';
            showToast('컨셉 생성 실패: ' + (err.message || ''), 'error');
        } finally {
            btn.disabled = false;
            btn.textContent = '후보 추가 생성';
        }
    }

    function renderConcepts(concepts) {
        const container = document.getElementById('concepts-list');
        if (!concepts || concepts.length === 0) {
            container.innerHTML = '<div style="color:var(--text-muted);font-size:var(--font-sm);text-align:center;padding:2rem;">컨셉 후보가 없습니다. "후보 생성" 버튼을 눌러주세요.</div>';
            return;
        }
        const riskColor = { low: '#d1fae5', medium: '#fef9c3', high: '#fee2e2' };
        const riskTextColor = { low: '#065f46', medium: '#713f12', high: '#b91c1c' };
        container.innerHTML = concepts.map(function (c) {
            const score = typeof c.score === 'number' ? c.score : 0;
            const scorePercent = Math.round(score * 100);
            const barColor = score >= 0.7 ? 'var(--color-success)' : score >= 0.4 ? 'var(--color-warning)' : 'var(--color-danger)';
            const riskBg = riskColor[c.risk] || '#f3f4f6';
            const riskFg = riskTextColor[c.risk] || '#374151';
            const hypoHtml = c.is_hypothesis ? '<span class="badge badge-hypothesis" style="margin-left:6px;">가설</span>' : '';
            return (
                '<div class="card" style="margin-bottom:0;">' +
                '<div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:8px;">' +
                '<div style="font-weight:700;font-size:var(--font-lg);">' + esc(c.name || c.title || '') + hypoHtml + '</div>' +
                '<span style="font-size:var(--font-xs);padding:3px 8px;border-radius:4px;background:' + riskBg + ';color:' + riskFg + ';">리스크 ' + esc(c.risk || '?') + '</span>' +
                '</div>' +
                '<p style="font-size:var(--font-sm);color:var(--text-secondary);margin-bottom:8px;">' + esc(c.description || '') + '</p>' +
                (c.rationale ? '<p style="font-size:var(--font-xs);color:var(--text-muted);margin-bottom:8px;font-style:italic;">' + esc(c.rationale) + '</p>' : '') +
                '<div style="margin-bottom:10px;">' +
                '<div style="display:flex;justify-content:space-between;font-size:var(--font-xs);color:var(--text-muted);">' +
                '<span>적합도 점수</span><span>' + scorePercent + '%</span></div>' +
                '<div class="score-bar-track"><div class="score-bar-fill" style="width:' + scorePercent + '%;background:' + barColor + ';"></div></div>' +
                '</div>' +
                '<div style="display:flex;gap:6px;flex-wrap:wrap;">' +
                '<button class="btn btn-sm btn-adopt"  onclick="SessionWorkspace.decideConcept(\'' + esc(c.id) + '\',\'adopt\')">채택</button>' +
                '<button class="btn btn-sm btn-hold"   onclick="SessionWorkspace.decideConcept(\'' + esc(c.id) + '\',\'hold\')">보류</button>' +
                '<button class="btn btn-sm btn-discard" onclick="SessionWorkspace.decideConcept(\'' + esc(c.id) + '\',\'discard\')">폐기</button>' +
                '<button class="btn btn-sm btn-explore" onclick="SessionWorkspace.decideConcept(\'' + esc(c.id) + '\',\'explore\')">더 탐색</button>' +
                '</div>' +
                '</div>'
            );
        }).join('');
    }

    async function decideConcept(conceptId, decision) {
        const reason = decision === 'discard' ? (prompt('폐기 이유를 입력하세요 (선택사항):') || '') : '';
        try {
            const res = await fetch('/api/concepts/' + conceptId + '/decisions', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ decision: decision, reason: reason })
            });
            if (!res.ok) throw new Error('결정 처리 실패');
            const labels = { adopt: '채택', hold: '보류', discard: '폐기', explore: '탐색' };
            showToast('컨셉이 ' + (labels[decision] || decision) + '되었습니다.', 'success');
            await loadConcepts();
            ws().updateDecisionPanel();
        } catch (err) {
            showToast('결정 처리 실패: ' + err.message, 'error');
        }
    }

    // ─── References ───────────────────────────────────────────────────────────

    function _renderAnalysisSummary(analysis) {
        if (!analysis) return '';
        const risk = analysis.replication_risk;
        const fitness = analysis.abstraction_fitness;
        const parts = [];
        if (analysis.form_grammar) parts.push('형태: ' + analysis.form_grammar.slice(0, 60));
        if (analysis.material_direction) parts.push('소재: ' + analysis.material_direction.slice(0, 40));
        if (!parts.length && !risk) return '';
        const riskColor = { low: '#065f46', medium: '#713f12', high: '#b91c1c' };
        const fitnessBar = fitness !== null && fitness !== undefined
            ? '<div style="margin-top:3px;"><div style="height:3px;background:#e5e7eb;border-radius:2px;overflow:hidden;"><div style="height:100%;width:' + Math.round(fitness * 100) + '%;background:var(--color-primary);"></div></div><span style="font-size:9px;color:var(--text-muted);">추상화 적합도 ' + Math.round(fitness * 100) + '%</span></div>'
            : '';
        return '<div style="margin-top:6px;padding:6px;background:#f0f9ff;border-radius:4px;font-size:var(--font-xs);color:var(--text-secondary);">' +
            (parts.length ? '<div style="margin-bottom:2px;">' + esc(parts.join(' / ')) + '</div>' : '') +
            (risk ? '<span style="color:' + (riskColor[risk] || '#374151') + ';font-weight:600;">복제위험: ' + esc(risk) + '</span>' : '') +
            fitnessBar +
            '</div>';
    }

    async function loadReferences() {
        const container = document.getElementById('references-list');
        container.innerHTML = skeleton(120) + skeleton(120) + skeleton(120) + skeleton(120);
        try {
            const res = await fetch('/api/sessions/' + SID() + '/references');
            if (!res.ok) throw new Error('레퍼런스 로드 실패');
            const refs = await res.json();
            state().references = refs;
            renderReferences(refs);
        } catch (err) {
            container.innerHTML = errBlock('레퍼런스 로드 실패', 'SessionWorkspace.loadReferences()');
        }
    }

    async function searchReferences() {
        const query = ws().getVal('ref-search-input');
        if (!query) { showToast('검색어를 입력하세요.', 'error'); return; }
        const container = document.getElementById('references-list');
        container.innerHTML = skeleton(120) + skeleton(120) + skeleton(120);
        try {
            const useSketch = document.getElementById('ref-sketch-ctx') && document.getElementById('ref-sketch-ctx').checked;
            const res = await fetch('/api/sessions/' + SID() + '/references/search', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: query, use_sketch_context: !!useSketch })
            });
            if (!res.ok) throw new Error('검색 실패');
            const refs = await res.json();
            state().references = refs;
            renderReferences(refs);
        } catch (err) {
            container.innerHTML = errBlock('레퍼런스 검색 실패', 'SessionWorkspace.loadReferences()');
        }
    }

    function renderReferences(refs) {
        const container = document.getElementById('references-list');
        if (!refs || refs.length === 0) {
            container.innerHTML = '<div style="color:var(--text-muted);font-size:var(--font-sm);text-align:center;padding:2rem;grid-column:1/-1;">레퍼런스가 없습니다. 검색어를 입력하세요.</div>';
            return;
        }
        const riskStyle = {
            low:    { bg: '#d1fae5', color: '#065f46', label: '저위험' },
            medium: { bg: '#fef9c3', color: '#713f12', label: '중위험' },
            high:   { bg: '#fee2e2', color: '#b91c1c', label: '고위험' }
        };
        container.innerHTML = refs.map(function (r) {
            const risk = r.copyright_risk || 'low';
            const rs = riskStyle[risk] || riskStyle.low;
            const isBlocked = risk === 'high';
            const thumbHtml = r.thumbnail_url
                ? '<div class="' + (isBlocked ? 'ref-blocked' : '') + '"><img src="' + esc(r.thumbnail_url) + '" alt="레퍼런스" style="width:100%;height:140px;object-fit:cover;display:block;border-radius:6px 6px 0 0;"></div>'
                : '<div style="height:100px;background:var(--bg-secondary);border-radius:6px 6px 0 0;display:flex;align-items:center;justify-content:center;color:var(--text-muted);font-size:var(--font-xs);">이미지 없음</div>';
            return (
                '<div class="img-card">' +
                thumbHtml +
                '<div style="padding:10px;">' +
                '<div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:4px;">' +
                '<div style="font-weight:600;font-size:var(--font-sm);">' + esc(r.title || r.source_url || '') + '</div>' +
                '<span style="font-size:var(--font-xs);padding:2px 6px;border-radius:3px;background:' + rs.bg + ';color:' + rs.color + ';white-space:nowrap;">' + rs.label + '</span>' +
                '</div>' +
                (r.relevance_reason ? '<p style="font-size:var(--font-xs);color:var(--text-secondary);margin-bottom:6px;">' + esc(r.relevance_reason) + '</p>' : '') +
                (r.source_url ? '<a href="' + esc(r.source_url) + '" target="_blank" rel="noopener" style="font-size:var(--font-xs);color:var(--color-primary);display:block;margin-bottom:6px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">' + esc(r.source_url) + '</a>' : '') +
                '<div style="display:flex;flex-wrap:wrap;gap:4px;margin-bottom:6px;font-size:var(--font-xs);color:var(--text-muted);">' +
                (r.collected_at ? '<span>수집: ' + fmtTime(r.collected_at) + '</span>' : '') +
                (r.license_type ? '<span style="padding:1px 4px;border-radius:3px;background:var(--bg-secondary);">' + esc(r.license_type) + '</span>' : '') +
                '</div>' +
                (r.domain_tags && r.domain_tags.length ? '<div style="display:flex;flex-wrap:wrap;gap:4px;margin-bottom:6px;">' + r.domain_tags.map(function(t) { return '<span style="font-size:var(--font-xs);padding:1px 6px;border-radius:3px;background:var(--bg-secondary);color:var(--text-secondary);">' + esc(t) + '</span>'; }).join('') + '</div>' : '') +
                _renderAnalysisSummary(r.analysis) +
                (!isBlocked ? '<button class="btn btn-sm btn-outline" style="margin-top:4px;" onclick="SessionWorkspace.analyzeReference(\'' + esc(r.id) + '\')">' + (r.analysis ? '재분석' : '분석 / 추상화에 추가') + '</button>' : '') +
                '</div>' +
                '</div>'
            );
        }).join('');
    }

    async function analyzeReference(refId) {
        showToast('레퍼런스 분석 중...', 'success');
        try {
            const res = await fetch('/api/references/' + refId + '/analyze', { method: 'POST' });
            if (!res.ok) throw new Error('분석 실패');
            showToast('레퍼런스 분석이 완료되었습니다.', 'success');
        } catch (err) {
            showToast('레퍼런스 분석 실패: ' + err.message, 'error');
        }
    }

    // ─── Abstraction ──────────────────────────────────────────────────────────

    async function loadAbstraction() {
        const container = document.getElementById('abstraction-list');
        container.innerHTML = skeleton(100) + skeleton(100);
        try {
            const res = await fetch('/api/sessions/' + SID() + '/abstractions');
            if (!res.ok) throw new Error('규칙 로드 실패');
            const rules = await res.json();
            state().abstractionRules = rules;
            renderAbstraction(rules);
        } catch (err) {
            container.innerHTML = errBlock('추상화 규칙 로드 실패', 'SessionWorkspace.loadAbstraction()');
        }
    }

    async function generateAbstraction(sourceType) {
        const container = document.getElementById('abstraction-list');
        container.innerHTML = skeleton(100) + skeleton(100) + skeleton(100);
        try {
            const res = await fetch('/api/sessions/' + SID() + '/abstractions', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ source_type: sourceType })
            });
            if (!res.ok) throw new Error('생성 실패');
            const rules = await res.json();
            state().abstractionRules = rules;
            renderAbstraction(rules);
            showToast('추상화 규칙이 생성되었습니다.', 'success');
        } catch (err) {
            container.innerHTML = errBlock('추상화 생성 실패', 'SessionWorkspace.loadAbstraction()');
            showToast('추상화 생성 실패: ' + err.message, 'error');
        }
    }

    function renderAbstraction(rules) {
        const container = document.getElementById('abstraction-list');
        if (!rules || rules.length === 0) {
            container.innerHTML = '<div style="color:var(--text-muted);font-size:var(--font-sm);text-align:center;padding:2rem;">추상화 규칙이 없습니다. 레퍼런스 또는 스케치에서 규칙을 생성하세요.</div>';
            return;
        }
        const axes = ['form', 'structure', 'surface', 'color_material', 'meaning', 'usability'];
        const axisLabels = { form: '형태', structure: '구조', surface: '표면', color_material: '색상/재료', meaning: '의미', usability: '사용성' };
        container.innerHTML = rules.map(function (rule) {
            const axesHtml = axes.filter(function (a) { return rule[a]; }).map(function (a) {
                return '<div style="margin-bottom:4px;"><span style="font-size:var(--font-xs);font-weight:700;color:var(--text-muted);">' + esc(axisLabels[a]) + '</span><div style="font-size:var(--font-sm);">' + esc(rule[a]) + '</div></div>';
            }).join('');
            return (
                '<div class="card" style="margin-bottom:0;">' +
                '<div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:8px;">' +
                '<div style="font-weight:700;font-size:var(--font-lg);">' + esc(rule.title || rule.name || '규칙') + '</div>' +
                '<button class="btn btn-sm btn-primary" onclick="SessionWorkspace.openGenerationDialog(\'' + esc(rule.id) + '\')">이미지 생성</button>' +
                '</div>' +
                '<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:8px;">' + axesHtml + '</div>' +
                '</div>'
            );
        }).join('');
    }

    // ─── Generation ───────────────────────────────────────────────────────────

    async function loadGenerations() {
        const container = document.getElementById('generations-list');
        container.innerHTML = skeleton(180) + skeleton(180) + skeleton(180);
        try {
            const res = await fetch('/api/sessions/' + SID() + '/generations');
            if (!res.ok) throw new Error('생성 목록 로드 실패');
            const gens = await res.json();
            state().generations = gens;
            renderGenerations(gens);
            gens.forEach(function (g) {
                if (g.status === 'pending' || g.status === 'processing') {
                    startPollingGeneration(g.id);
                }
            });
        } catch (err) {
            container.innerHTML = errBlock('이미지 목록 로드 실패', 'SessionWorkspace.loadGenerations()');
        }
    }

    function renderGenerations(gens) {
        const container = document.getElementById('generations-list');
        if (!gens || gens.length === 0) {
            container.innerHTML = '<div style="color:var(--text-muted);font-size:var(--font-sm);text-align:center;padding:2rem;grid-column:1/-1;">생성된 이미지가 없습니다. "새 이미지 생성" 버튼을 눌러주세요.</div>';
            return;
        }
        container.innerHTML = gens.map(function (g) {
            const isPending = g.status === 'pending' || g.status === 'processing';
            const imgHtml = isPending
                ? '<div class="skeleton" style="height:180px;border-radius:6px 6px 0 0;"></div>'
                : (g.image_url
                    ? '<img src="' + esc(g.image_url) + '" alt="생성 이미지" style="width:100%;height:180px;object-fit:cover;border-radius:6px 6px 0 0;">'
                    : '<div style="height:180px;background:var(--bg-secondary);border-radius:6px 6px 0 0;display:flex;align-items:center;justify-content:center;color:var(--color-danger);font-size:var(--font-xs);">생성 실패</div>');
            const statusBg = { completed: '#d1fae5', pending: '#fef9c3', processing: '#dbeafe', failed: '#fee2e2' };
            const statusLabel = { completed: '완료', pending: '대기', processing: '생성 중', failed: '실패' };
            const sbg = statusBg[g.status] || '#f3f4f6';
            const slabel = statusLabel[g.status] || g.status;
            return (
                '<div class="img-card" id="gen-card-' + esc(g.id) + '">' +
                imgHtml +
                '<div style="padding:10px;">' +
                '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">' +
                '<span style="font-size:var(--font-xs);padding:2px 6px;border-radius:3px;background:' + sbg + ';">' + slabel + '</span>' +
                '<span style="font-size:var(--font-xs);color:var(--text-muted);">' + fmtTime(g.created_at) + '</span>' +
                '</div>' +
                (g.prompt ? '<p style="font-size:var(--font-xs);color:var(--text-secondary);margin-top:4px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" title="' + esc(g.prompt) + '">' + esc(g.prompt) + '</p>' : '') +
                (g.provider ? '<div style="font-size:var(--font-xs);color:var(--text-muted);margin-top:2px;">' + esc(g.provider) + (g.model ? ' / ' + esc(g.model) : '') + '</div>' : '') +
                '</div>' +
                '</div>'
            );
        }).join('');
    }

    // @MX:WARN: [AUTO] Polling loop for async image generation
    // @MX:REASON: Unguarded interval could accumulate if loadGenerations called multiple times
    function startPollingGeneration(genId) {
        if (state().generationPollers[genId]) return;
        state().generationPollers[genId] = setInterval(async function () {
            try {
                const res = await fetch('/api/generations/' + genId);
                if (!res.ok) {
                    clearInterval(state().generationPollers[genId]);
                    delete state().generationPollers[genId];
                    return;
                }
                const gen = await res.json();
                if (gen.status !== 'pending' && gen.status !== 'processing') {
                    clearInterval(state().generationPollers[genId]);
                    delete state().generationPollers[genId];
                    await loadGenerations();
                }
            } catch (err) {
                clearInterval(state().generationPollers[genId]);
                delete state().generationPollers[genId];
            }
        }, 3000);
    }

    function openGenerationDialog(preselectedRuleId) {
        const ruleSelect = document.getElementById('gen-rule-select');
        const conceptSelect = document.getElementById('gen-concept-select');
        ruleSelect.innerHTML = state().abstractionRules.map(function (r) {
            return '<option value="' + esc(r.id) + '"' + (r.id === preselectedRuleId ? ' selected' : '') + '>' + esc(r.title || r.name || r.id) + '</option>';
        }).join('') || '<option value="">규칙 없음 (먼저 추상화 규칙을 생성하세요)</option>';
        conceptSelect.innerHTML = '<option value="">컨셉 없음</option>' + state().concepts.map(function (c) {
            return '<option value="' + esc(c.id) + '">' + esc(c.name || c.title || c.id) + '</option>';
        }).join('');
        document.getElementById('gen-dialog').style.display = 'flex';
    }

    function closeGenerationDialog() {
        document.getElementById('gen-dialog').style.display = 'none';
    }

    async function submitGeneration() {
        const ruleId = document.getElementById('gen-rule-select').value;
        const conceptId = document.getElementById('gen-concept-select').value;
        if (!ruleId) { showToast('추상화 규칙을 선택하세요.', 'error'); return; }

        const sessionData = state().session;
        const briefId = sessionData && sessionData.brief && sessionData.brief.id ? sessionData.brief.id : null;

        closeGenerationDialog();
        showToast('이미지 생성 요청을 전송했습니다.', 'success');

        try {
            const body = { rule_id: ruleId };
            if (briefId) body.brief_id = briefId;
            if (conceptId) body.concept_id = conceptId;

            const res = await fetch('/api/sessions/' + SID() + '/generations', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body)
            });
            if (!res.ok) throw new Error('생성 요청 실패');
            const gen = await res.json();
            await loadGenerations();
            if (gen.status === 'pending' || gen.status === 'processing') {
                startPollingGeneration(gen.id);
            }
        } catch (err) {
            showToast('이미지 생성 실패: ' + err.message, 'error');
        }
    }

    // ─── Spec ─────────────────────────────────────────────────────────────────

    async function loadSpec() {
        const container = document.getElementById('spec-document');
        container.innerHTML = skeleton(200);
        try {
            const res = await fetch('/api/sessions/' + SID() + '/specs');
            if (!res.ok) throw new Error('스펙 로드 실패');
            const specList = await res.json();
            if (!specList || specList.length === 0) {
                container.innerHTML = '<div style="color:var(--text-muted);font-size:var(--font-sm);text-align:center;padding:2rem;">스펙 문서가 없습니다. "스펙 문서 생성" 버튼을 눌러주세요.</div>';
                return;
            }
            const spec = specList[0];
            state().spec = spec;
            renderSpec(spec);
            ws().updateDecisionPanel();
        } catch (err) {
            container.innerHTML = errBlock('스펙 로드 실패', 'SessionWorkspace.loadSpec()');
        }
    }

    async function generateSpec() {
        const container = document.getElementById('spec-document');
        container.innerHTML = skeleton(200);
        try {
            const res = await fetch('/api/sessions/' + SID() + '/specs', { method: 'POST' });
            if (!res.ok) throw new Error('스펙 생성 실패');
            const spec = await res.json();
            state().spec = spec;
            renderSpec(spec);
            ws().updateDecisionPanel();
            showToast('스펙 문서가 생성되었습니다.', 'success');
        } catch (err) {
            container.innerHTML = errBlock('스펙 생성 실패', 'SessionWorkspace.loadSpec()');
            showToast('스펙 생성 실패: ' + err.message, 'error');
        }
    }

    function renderSpec(spec) {
        const container = document.getElementById('spec-document');
        if (!spec) { container.innerHTML = '<div style="color:var(--text-muted);">스펙이 없습니다.</div>'; return; }
        const content = spec.content_json || {};

        const sections = [
            { title: '브리프 요약', content: content.brief },
            { title: '트렌드 근거', content: content.trend_evidence },
            { title: '컨셉 후보와 결정', content: content.concept_candidates },
            { title: '최종 컨셉', content: content.final_concept },
            { title: '스케치 분석', content: content.sketch_analysis },
            { title: '레퍼런스 보드', content: content.reference_board },
            { title: '추상화 규칙', content: content.abstraction_rules },
            { title: '생성된 이미지', content: content.generated_designs },
            { title: '제외된 대안', content: content.discarded_alternatives },
            { title: '결정 근거', content: content.decision_rationale },
            { title: '출처', content: content.sources }
        ];

        container.innerHTML = sections.filter(function (s) { return s.content; }).map(function (s) {
            const contentHtml = typeof s.content === 'string'
                ? '<p style="font-size:var(--font-sm);color:var(--text-secondary);line-height:1.7;">' + esc(s.content) + '</p>'
                : '<pre style="font-size:var(--font-xs);color:var(--text-secondary);white-space:pre-wrap;word-break:break-word;">' + esc(JSON.stringify(s.content, null, 2)) + '</pre>';
            return (
                '<div class="spec-section">' +
                '<h4 style="font-size:var(--font-lg);font-weight:700;margin-bottom:0.75rem;color:var(--text-primary);">' + esc(s.title) + '</h4>' +
                contentHtml +
                '</div>'
            );
        }).join('') || '<div style="color:var(--text-muted);font-size:var(--font-sm);">스펙 내용이 없습니다.</div>';
    }

    function printSpec() {
        window.print();
    }

    // ─── Wire up overrides on SessionWorkspace after DOM ready ────────────────

    document.addEventListener('DOMContentLoaded', function () {
        // Wait for session_detail.js to run first, then override stubs
        const sw = window.SessionWorkspace;
        if (!sw) { console.error('SessionWorkspace not found — check script load order'); return; }
        sw.loadSketches = loadSketches;
        sw.uploadSketch = uploadSketch;
        sw.analyzeSketch = analyzeSketch;
        sw.loadTrends = loadTrends;
        sw.searchTrends = searchTrends;
        sw.loadConcepts = loadConcepts;
        sw.generateConcepts = generateConcepts;
        sw.decideConcept = decideConcept;
        sw.loadReferences = loadReferences;
        sw.searchReferences = searchReferences;
        sw.analyzeReference = analyzeReference;
        sw.loadAbstraction = loadAbstraction;
        sw.generateAbstraction = generateAbstraction;
        sw.loadGenerations = loadGenerations;
        sw.openGenerationDialog = openGenerationDialog;
        sw.closeGenerationDialog = closeGenerationDialog;
        sw.submitGeneration = submitGeneration;
        sw.loadSpec = loadSpec;
        sw.generateSpec = generateSpec;
        sw.printSpec = printSpec;
    });
}());
