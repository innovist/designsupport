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
        trends = (trends || []).filter(function (t) {
            const text = (t.summary || t.title || '').trim();
            return text && text.indexOf('기사가 제공되지 않아') === -1;
        });
        if (!trends || trends.length === 0) {
            container.innerHTML = '<div style="color:var(--text-muted);font-size:var(--font-sm);text-align:center;padding:2rem;">트렌드 분석 결과가 없습니다. 브리프를 작성하고 트렌드를 조사하세요.</div>';
            return;
        }
        window._trendDetailCache = trends;
        const rows = trends.map(function (t, idx) {
            const keywords = (t.keywords || []).slice(0, 3);
            const kwHtml = keywords.length
                ? '<div class="trend-keyword-line">' + keywords.map(function (k) {
                    return '<span class="trend-keyword-chip" title="' + esc(k) + '">' + esc(k) + '</span>';
                }).join('') + '</div>'
                : '<span style="color:var(--text-muted);font-size:12px;">-</span>';
            const srcCount = (t.source_urls && t.source_urls.length) ? t.source_urls.length : 0;
            return (
                '<tr class="trend-row" onclick="SessionWorkspace.showTrendSources(window._trendDetailCache[' + idx + '])" title="클릭하여 상세보기">' +
                '<td style="width:46px;color:var(--text-muted);font-size:12px;">' + (idx + 1) + '</td>' +
                '<td style="width:20%;"><div class="trend-cell-title">' + esc(t.title || t.summary || '') + '</div></td>' +
                '<td><div class="trend-cell-summary">' + esc(t.summary || '-') + '</div></td>' +
                '<td style="width:210px;">' + kwHtml + '</td>' +
                '<td style="width:72px;color:var(--text-muted);font-size:12px;text-align:right;">' + srcCount + '건</td>' +
                '</tr>'
            );
        }).join('');
        container.innerHTML =
            '<div class="trend-table-wrap">' +
            '<table class="trend-table">' +
            '<thead><tr>' +
            '<th style="width:46px;">#</th>' +
            '<th style="width:20%;">제목</th>' +
            '<th>요약</th>' +
            '<th style="width:210px;">키워드</th>' +
            '<th style="width:72px;text-align:right;">출처</th>' +
            '</tr></thead>' +
            '<tbody>' + rows + '</tbody>' +
            '</table>' +
            '</div>';
    }

    // @MX:ANCHOR: [AUTO] showTrendSources — shows reference source list modal for a trend insight
    // @MX:REASON: called from multiple renderTrends-generated onclick handlers; public API boundary
    function showTrendSources(trendData) {
        const modal = document.getElementById('trend-detail-modal');
        const t = trendData || {};
        const sources = t.source_urls || [];
        const keywordHtml = (t.keywords || []).length
            ? '<div style="display:flex;gap:5px;flex-wrap:wrap;margin-top:10px;">' +
              t.keywords.map(function (k) {
                  return '<span class="trend-keyword-chip" style="max-width:none;">' + esc(k) + '</span>';
              }).join('') + '</div>'
            : '';
        const srcListHtml = sources.length
            ? sources.map(function (s, i) {
                return '<div style="padding:8px 0;border-bottom:1px solid var(--border-color);display:flex;align-items:flex-start;gap:8px;">' +
                    '<span style="flex-shrink:0;color:var(--text-muted);font-size:var(--font-xs);padding-top:2px;">' + (i + 1) + '</span>' +
                    '<div style="min-width:0;">' +
                    '<div style="font-size:var(--font-sm);font-weight:600;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;margin-bottom:2px;">' + esc(s.title || s.url || '') + '</div>' +
                    '<a href="' + esc(s.url || '') + '" target="_blank" rel="noopener" style="font-size:var(--font-xs);color:var(--color-primary);word-break:break-all;">' + esc(s.url || '') + '</a>' +
                    '</div></div>';
            }).join('')
            : '<div style="color:var(--text-muted);font-size:var(--font-sm);padding:1rem 0;">참고자료 정보가 없습니다.</div>';

        modal.innerHTML =
            '<div style="position:fixed;inset:0;z-index:9001;background:rgba(0,0,0,0.5);display:flex;align-items:center;justify-content:center;padding:1rem;" onclick="if(event.target===this)SessionWorkspace.closeTrendDetailModal()">' +
            '<div class="card" style="width:560px;max-width:94vw;max-height:85vh;overflow-y:auto;margin:0;" onclick="event.stopPropagation()">' +
            '<div class="card-header" style="display:flex;justify-content:space-between;align-items:center;">' +
            '<h4 class="card-title" style="margin:0;">트렌드 상세</h4>' +
            '<button onclick="SessionWorkspace.closeTrendDetailModal()" aria-label="닫기" style="background:none;border:none;font-size:1.25rem;cursor:pointer;color:var(--text-secondary);">×</button>' +
            '</div>' +
            '<div style="font-weight:800;font-size:16px;line-height:1.45;margin-bottom:8px;">' + esc(t.title || '') + '</div>' +
            (t.summary ? '<div style="font-size:13px;color:var(--text-secondary);line-height:1.65;margin-bottom:10px;white-space:pre-wrap;">' + esc(t.summary) + '</div>' : '') +
            keywordHtml +
            '<div style="font-weight:700;font-size:13px;margin:16px 0 4px;padding-top:12px;border-top:1px solid var(--border-color);">출처</div>' +
            srcListHtml +
            '</div>' +
            '</div>';
        modal.style.display = 'block';
    }

    function closeTrendDetailModal() {
        const modal = document.getElementById('trend-detail-modal');
        if (modal) { modal.innerHTML = ''; modal.style.display = 'none'; }
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
            container.innerHTML = '<div style="grid-column:1/-1;color:var(--text-muted);font-size:13px;text-align:center;padding:2rem;border:1px dashed var(--border-color);border-radius:4px;">컨셉 후보가 없습니다. 우측 상단 "후보 추가 생성" 버튼을 눌러 시작하세요.</div>';
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
            const hypoHtml = c.is_hypothesis ? '<span class="badge badge-hypothesis" style="margin-left:6px;flex-shrink:0;">가설</span>' : '';
            return (
                '<div class="card" role="button" tabindex="0" onclick="SessionWorkspace.showConceptDetail(\'' + esc(c.id) + '\')" onkeydown="if(event.key===\'Enter\'||event.key===\' \'){event.preventDefault();SessionWorkspace.showConceptDetail(\'' + esc(c.id) + '\')}" style="margin-bottom:0;display:flex;flex-direction:column;min-height:0;cursor:pointer;">' +
                '<div style="display:flex;flex-direction:column;align-items:stretch;margin-bottom:8px;gap:6px;">' +
                '<div style="font-weight:700;font-size:var(--font-base);line-height:1.4;white-space:normal;overflow-wrap:break-word;word-break:keep-all;width:100%;max-width:100%;">' + esc(c.name || c.title || '') + '</div>' +
                '<div style="display:flex;align-items:center;gap:4px;flex-wrap:wrap;min-width:0;">' +
                hypoHtml +
                '<span style="font-size:var(--font-xs);line-height:1.45;padding:4px 6px;border-radius:3px;background:' + riskBg + ';color:' + riskFg + ';white-space:normal;overflow-wrap:break-word;word-break:keep-all;min-width:0;max-width:100%;">리스크 ' + esc(c.risk || '?') + '</span>' +
                '</div>' +
                '</div>' +
                '<p style="font-size:var(--font-sm);color:var(--text-secondary);margin-bottom:6px;line-height:1.5;overflow:hidden;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;">' + esc(c.description || '') + '</p>' +
                (c.rationale ? '<p style="font-size:var(--font-xs);color:var(--text-muted);margin-bottom:6px;font-style:italic;line-height:1.4;overflow:hidden;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;">' + esc(c.rationale) + '</p>' : '') +
                '<div style="margin-bottom:8px;">' +
                '<div style="display:flex;justify-content:space-between;font-size:var(--font-xs);color:var(--text-muted);">' +
                '<span>적합도</span><span>' + scorePercent + '%</span></div>' +
                '<div class="score-bar-track"><div class="score-bar-fill" style="width:' + scorePercent + '%;background:' + barColor + ';"></div></div>' +
                '</div>' +
                '<div style="display:flex;gap:4px;flex-wrap:wrap;margin-top:auto;">' +
                '<button class="btn btn-sm btn-adopt"  onclick="event.stopPropagation();SessionWorkspace.decideConcept(\'' + esc(c.id) + '\',\'adopt\')">채택</button>' +
                '<button class="btn btn-sm btn-hold"   onclick="event.stopPropagation();SessionWorkspace.decideConcept(\'' + esc(c.id) + '\',\'hold\')">보류</button>' +
                '<button class="btn btn-sm btn-discard" onclick="event.stopPropagation();SessionWorkspace.decideConcept(\'' + esc(c.id) + '\',\'discard\')">폐기</button>' +
                '<button class="btn btn-sm btn-explore" onclick="event.stopPropagation();SessionWorkspace.decideConcept(\'' + esc(c.id) + '\',\'explore\')">탐색</button>' +
                '</div>' +
                '</div>'
            );
        }).join('');
    }

    function showConceptDetail(conceptId) {
        const concept = (state().concepts || []).find(function (c) { return c.id === conceptId; });
        const modal = document.getElementById('concept-detail-modal');
        if (!concept || !modal) return;
        const score = typeof concept.score === 'number' ? Math.round(concept.score * 100) : null;
        const evidence = Array.isArray(concept.trend_evidence) ? concept.trend_evidence : [];
        const evidenceHtml = evidence.length
            ? evidence.map(function (item) {
                const source = item.source || item.url || '';
                const quote = item.quote || item.summary || '';
                return '<div style="padding:10px;border:1px solid var(--border-color);border-radius:6px;background:var(--bg-secondary);">' +
                    (quote ? '<div style="font-size:13px;line-height:1.55;color:var(--text-secondary);">' + esc(quote) + '</div>' : '') +
                    (source ? '<a href="' + esc(source) + '" target="_blank" rel="noopener" style="display:block;margin-top:6px;font-size:12px;color:var(--color-primary);overflow-wrap:anywhere;">' + esc(source) + '</a>' : '') +
                    '</div>';
            }).join('')
            : '<div style="font-size:13px;color:var(--text-muted);">표시할 트렌드 근거가 없습니다.</div>';
        modal.innerHTML =
            '<div style="position:fixed;inset:0;z-index:9003;background:rgba(15,23,42,0.62);display:flex;align-items:center;justify-content:center;padding:24px;" onclick="if(event.target===this)SessionWorkspace.closeConceptDetail()">' +
            '<div class="card" style="width:min(720px,94vw);max-height:88vh;overflow:auto;margin:0;padding:0;" onclick="event.stopPropagation()">' +
            '<div style="position:sticky;top:0;background:var(--bg-card);z-index:1;padding:18px 20px;border-bottom:1px solid var(--border-color);display:flex;justify-content:space-between;gap:12px;align-items:flex-start;">' +
            '<div style="min-width:0;">' +
            '<div style="font-size:18px;font-weight:800;line-height:1.35;overflow-wrap:anywhere;word-break:keep-all;">' + esc(concept.name || concept.title || '컨셉 상세') + '</div>' +
            '<div style="margin-top:6px;font-size:12px;color:var(--text-muted);">' +
            (score !== null ? '적합도 ' + score + '% · ' : '') + '리스크 ' + esc(concept.risk || '-') +
            '</div>' +
            '</div>' +
            '<button type="button" onclick="SessionWorkspace.closeConceptDetail()" aria-label="닫기" style="border:1px solid var(--border-color);background:white;border-radius:4px;width:32px;height:32px;font-size:20px;cursor:pointer;flex-shrink:0;">×</button>' +
            '</div>' +
            '<div style="padding:20px;display:grid;gap:16px;">' +
            '<section><h4 style="margin-bottom:6px;">디자인 방향</h4><div style="font-size:14px;line-height:1.7;color:var(--text-secondary);white-space:pre-wrap;">' + esc(concept.description || '-') + '</div></section>' +
            '<section><h4 style="margin-bottom:6px;">디자인 근거</h4><div style="font-size:14px;line-height:1.7;color:var(--text-secondary);white-space:pre-wrap;">' + esc(concept.rationale || '-') + '</div></section>' +
            '<section><h4 style="margin-bottom:6px;">디자인 리스크</h4><div style="font-size:14px;line-height:1.7;color:var(--text-secondary);white-space:pre-wrap;">' + esc(concept.risk || '-') + '</div></section>' +
            '<section><h4 style="margin-bottom:8px;">트렌드 근거</h4><div style="display:grid;gap:8px;">' + evidenceHtml + '</div></section>' +
            '<div style="display:flex;gap:6px;flex-wrap:wrap;justify-content:flex-end;border-top:1px solid var(--border-color);padding-top:14px;">' +
            '<button class="btn btn-sm btn-adopt" onclick="SessionWorkspace.decideConcept(\'' + esc(concept.id) + '\',\'adopt\');SessionWorkspace.closeConceptDetail()">채택</button>' +
            '<button class="btn btn-sm btn-hold" onclick="SessionWorkspace.decideConcept(\'' + esc(concept.id) + '\',\'hold\');SessionWorkspace.closeConceptDetail()">보류</button>' +
            '<button class="btn btn-sm btn-discard" onclick="SessionWorkspace.decideConcept(\'' + esc(concept.id) + '\',\'discard\');SessionWorkspace.closeConceptDetail()">폐기</button>' +
            '<button class="btn btn-sm btn-explore" onclick="SessionWorkspace.decideConcept(\'' + esc(concept.id) + '\',\'explore\');SessionWorkspace.closeConceptDetail()">탐색</button>' +
            '</div>' +
            '</div>' +
            '</div>' +
            '</div>';
        modal.style.display = 'block';
    }

    function closeConceptDetail() {
        const modal = document.getElementById('concept-detail-modal');
        if (modal) { modal.innerHTML = ''; modal.style.display = 'none'; }
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
            if ((!refs || refs.length === 0) && !state()._autoReferenceSearchTried) {
                const autoQuery = _buildAutoReferenceQuery();
                if (autoQuery) {
                    state()._autoReferenceSearchTried = true;
                    const input = document.getElementById('ref-search-input');
                    if (input && !input.value) input.value = autoQuery;
                    await _searchReferencesWithQuery(autoQuery, false);
                    return;
                }
            }
            renderReferences(refs);
        } catch (err) {
            container.innerHTML = errBlock('레퍼런스 로드 실패', 'SessionWorkspace.loadReferences()');
        }
    }

    async function searchReferences() {
        const query = ws().getVal('ref-search-input');
        if (!query) { showToast('검색어를 입력하세요.', 'error'); return; }
        state()._autoReferenceSearchTried = true;
        await _searchReferencesWithQuery(query, true);
    }

    async function _searchReferencesWithQuery(query, useSketchControl) {
        const container = document.getElementById('references-list');
        container.innerHTML = skeleton(120) + skeleton(120) + skeleton(120);
        try {
            const useSketch = useSketchControl && document.getElementById('ref-sketch-ctx') && document.getElementById('ref-sketch-ctx').checked;
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

    function _buildAutoReferenceQuery() {
        const session = state().session || {};
        const brief = session.brief || {};
        const adopted = (state().concepts || []).find(function (c) { return c.status === 'adopted'; });
        return [
            brief.purpose,
            brief.domain,
            adopted && adopted.name,
            'design reference image'
        ].filter(Boolean).join(' ').replace(/\s+/g, ' ').trim().slice(0, 180);
    }

    function renderReferences(refs) {
        const container = document.getElementById('references-list');
        if (!refs || refs.length === 0) {
            container.innerHTML = '<div style="grid-column:1/-1;color:var(--text-muted);font-size:13px;text-align:center;padding:2rem;border:1px dashed var(--border-color);border-radius:4px;">레퍼런스가 없습니다. 검색어를 입력하고 "검색"을 누르세요.</div>';
            return;
        }
        const riskStyle = {
            low:    { bg: '#d1fae5', color: '#065f46', label: '저위험' },
            medium: { bg: '#fef9c3', color: '#713f12', label: '중위험' },
            high:   { bg: '#fee2e2', color: '#b91c1c', label: '고위험' }
        };
        const sortedRefs = refs.filter(function (r) { return !!r.thumbnail_url; });
        if (sortedRefs.length === 0) {
            container.innerHTML = '<div style="grid-column:1/-1;color:var(--text-muted);font-size:13px;text-align:center;padding:2rem;border:1px dashed var(--border-color);border-radius:4px;">이미지 레퍼런스가 없습니다. 이미지 검색을 실행하거나 검색어를 더 구체화하세요.</div>';
            return;
        }
        // Store sorted refs for onclick reference
        window._refDetailCache = sortedRefs;

        container.innerHTML = sortedRefs.map(function (r, idx) {
            const risk = r.copyright_risk || 'low';
            const rs = riskStyle[risk] || riskStyle.low;
            const isBlocked = risk === 'high';
            const click = isBlocked
                ? ''
                : ' onclick="SessionWorkspace.showRefDetail(window._refDetailCache[' + idx + '])"';
            return (
                '<button type="button" class="reference-image-card' + (isBlocked ? ' ref-blocked' : '') + '"' + click + ' title="이미지 상세보기"' + (isBlocked ? ' disabled' : '') + '>' +
                '<img src="' + esc(r.thumbnail_url) + '" alt="' + esc(r.title || '이미지 레퍼런스') + '">' +
                '<div class="reference-image-meta">' +
                '<span class="reference-image-title">' + esc(r.title || '이미지 레퍼런스') + '</span>' +
                '<span class="reference-risk" style="background:' + rs.bg + ';color:' + rs.color + ';">' + rs.label + '</span>' +
                '</div>' +
                '</button>'
            );
        }).join('');
    }

    // @MX:ANCHOR: [AUTO] showRefDetail — called from dynamically rendered reference image cards
    // @MX:REASON: fan_in from multiple renderReferences-generated onclick handlers; public API boundary
    function showRefDetail(refData) {
        const modal = document.getElementById('ref-detail-modal');
        const r = refData || {};
        const analysis = r.analysis || {};
        const analysisFields = [
            { key: 'form_grammar', label: '형태 문법' },
            { key: 'material_direction', label: '소재 방향' },
            { key: 'meaning_symbols', label: '의미·상징' },
            { key: 'usability_notes', label: '사용성 메모' },
            { key: 'relevance_reason', label: '관련성 이유' }
        ];
        const analysisRows = analysisFields
            .filter(function (f) { return analysis[f.key] || (f.key === 'relevance_reason' && r.relevance_reason); })
            .map(function (f) {
                const val = f.key === 'relevance_reason' ? (analysis[f.key] || r.relevance_reason) : analysis[f.key];
                return '<div style="margin-bottom:8px;"><div style="font-size:var(--font-xs);font-weight:700;color:var(--text-muted);margin-bottom:2px;">' + esc(f.label) + '</div>' +
                    '<div style="font-size:var(--font-sm);color:var(--text-primary);line-height:1.5;">' + esc(val) + '</div></div>';
            }).join('');
        const imgSection = r.thumbnail_url
            ? '<div style="margin-bottom:14px;border-radius:6px;overflow:hidden;"><img src="' + esc(r.thumbnail_url) + '" alt="레퍼런스 이미지" style="width:100%;max-height:320px;object-fit:contain;display:block;background:var(--bg-secondary);"></div>'
            : '';
        modal.innerHTML =
            '<div style="position:fixed;inset:0;z-index:9001;background:rgba(0,0,0,0.5);display:flex;align-items:center;justify-content:center;padding:1rem;" onclick="if(event.target===this)SessionWorkspace.closeRefDetailModal()">' +
            '<div class="card" style="width:600px;max-width:94vw;max-height:88vh;overflow-y:auto;margin:0;" onclick="event.stopPropagation()">' +
            '<div class="card-header" style="display:flex;justify-content:space-between;align-items:center;">' +
            '<h4 class="card-title" style="margin:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:480px;">' + esc(r.title || '레퍼런스 상세') + '</h4>' +
            '<button onclick="SessionWorkspace.closeRefDetailModal()" aria-label="닫기" style="background:none;border:none;font-size:1.25rem;cursor:pointer;color:var(--text-secondary);flex-shrink:0;">×</button>' +
            '</div>' +
            imgSection +
            (r.source_url ? '<div style="margin-bottom:10px;"><a href="' + esc(r.source_url) + '" target="_blank" rel="noopener" style="font-size:var(--font-sm);color:var(--color-primary);word-break:break-all;">' + esc(r.source_url) + '</a></div>' : '') +
            (analysisRows ? '<div style="border-top:1px solid var(--border-color);padding-top:12px;">' + analysisRows + '</div>' : '<div style="color:var(--text-muted);font-size:var(--font-sm);">분석 정보가 없습니다. 분석 버튼을 눌러 추상화 정보를 생성하세요.</div>') +
            '</div>' +
            '</div>';
        modal.style.display = 'block';
    }

    function closeRefDetailModal() {
        const modal = document.getElementById('ref-detail-modal');
        if (modal) { modal.innerHTML = ''; modal.style.display = 'none'; }
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

    // ─── Design Reference Images (Unsplash/Pexels/Pixabay) ──────────────────────

    async function searchDesignReferences() {
        const query = ws().getVal('design-ref-search-input');
        if (!query) { showToast('검색어를 입력하세요.', 'error'); return; }
        const grid = document.getElementById('design-references-grid');
        grid.innerHTML = Array.from({length: 10}, function () { return skeleton(200); }).join('');
        try {
            const res = await fetch('/api/design-references/search', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: query, per_page: 10 })
            });
            if (!res.ok) throw new Error('검색 실패');
            const data = await res.json();
            renderDesignReferences(data.images || []);
        } catch (err) {
            grid.innerHTML = errBlock('이미지 검색 실패', 'SessionWorkspace.searchDesignReferences()');
        }
    }

    function renderDesignReferences(images) {
        var grid = document.getElementById('design-references-grid');
        if (!images || images.length === 0) {
            grid.innerHTML = '<div style="grid-column:1/-1;color:var(--text-muted);font-size:13px;text-align:center;padding:2rem;border:1px dashed var(--border-color);border-radius:6px;">검색 결과가 없습니다. 다른 키워드를 시도해보세요.</div>';
            return;
        }
        window._designRefCache = images;
        grid.innerHTML = images.map(function (img, idx) {
            return (
                '<div class="img-card" style="cursor:pointer;" onclick="SessionWorkspace.openDesignRef(' + idx + ')">' +
                '<div style="position:relative;overflow:hidden;border-radius:6px 6px 0 0;">' +
                '<img src="' + esc(img.thumbnail_url) + '" alt="' + esc(img.title || '') + '" ' +
                'style="width:100%;height:200px;object-fit:cover;display:block;transition:transform 0.2s,opacity 0.15s;" ' +
                'onmouseover="this.style.transform=\'scale(1.03)\';this.style.opacity=\'0.9\'" ' +
                'onmouseout="this.style.transform=\'scale(1)\';this.style.opacity=\'1\'" ' +
                'loading="lazy">' +
                '</div>' +
                '<div style="padding:6px 8px;">' +
                '<div style="font-size:11px;color:var(--text-muted);display:flex;justify-content:space-between;align-items:center;">' +
                '<span style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:65%;">' + esc(img.photographer || '') + '</span>' +
                '<span style="font-size:10px;padding:1px 4px;border-radius:3px;background:var(--bg-secondary);">' + esc(img.source) + '</span>' +
                '</div>' +
                '</div>' +
                '</div>'
            );
        }).join('');
    }

    function openDesignRef(idx) {
        var cached = window._designRefCache;
        if (cached && cached[idx] && cached[idx].source_url) {
            window.open(cached[idx].source_url, '_blank');
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
                '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">' +
                '<div style="font-weight:700;font-size:var(--font-base);">' + esc(rule.title || rule.name || '규칙') + '</div>' +
                '<button class="btn btn-sm btn-primary" onclick="SessionWorkspace.openGenerationDialog(\'' + esc(rule.id) + '\')">산출물 생성</button>' +
                '</div>' +
                '<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:8px;">' + axesHtml + '</div>' +
                '</div>'
            );
        }).join('');
    }

    // ─── Generation ───────────────────────────────────────────────────────────

    // @MX:NOTE: [AUTO] Legacy output_kind values mapped to new workflow terminology
    function normalizeOutputKind(kind) {
        if (kind === 'sketch') return 'draft';
        if (kind === 'final_image') return 'final';
        return kind || 'draft';
    }

    async function loadGenerations() {
        const draftList = document.getElementById('gen-draft-list');
        const finalList = document.getElementById('gen-final-list');
        const skeletonHtml = skeleton(180) + skeleton(180);
        if (draftList) draftList.innerHTML = skeletonHtml;
        if (finalList) finalList.innerHTML = skeletonHtml;
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
            const errHtml = errBlock('이미지 목록 로드 실패', 'SessionWorkspace.loadGenerations()');
            if (draftList) draftList.innerHTML = errHtml;
            if (finalList) finalList.innerHTML = '';
        }
    }

    function _buildGenCard(g) {
        const isPending = g.status === 'pending' || g.status === 'processing';
        const rawKind = (g.generation_params && g.generation_params.output_kind) || 'draft';
        const outputKind = normalizeOutputKind(rawKind);
        const outputLabel = outputKind === 'draft' ? '초안' : (outputKind === 'final' ? '최종안' : '이미지');
        const imageUrl = g.image_url || '';
        const imgHtml = isPending
            ? '<div class="skeleton" style="height:180px;border-radius:6px 6px 0 0;"></div>'
            : (imageUrl
                ? '<button type="button" onclick="SessionWorkspace.showGenerationImage(\'' + esc(g.id) + '\')" aria-label="' + esc(outputLabel) + ' 확대 보기" style="display:block;width:100%;padding:0;border:0;background:transparent;cursor:zoom-in;">' +
                  '<img src="' + esc(imageUrl) + '" alt="' + esc(outputLabel) + '" style="width:100%;height:180px;object-fit:cover;border-radius:6px 6px 0 0;">' +
                  '</button>'
                : '<div style="height:180px;background:var(--bg-secondary);border-radius:6px 6px 0 0;display:flex;align-items:center;justify-content:center;color:var(--color-danger);font-size:var(--font-xs);">생성 실패</div>');
        const statusBg = { completed: '#d1fae5', pending: '#fef9c3', processing: '#dbeafe', failed: '#fee2e2' };
        const statusLabel = { completed: '완료', pending: '대기', processing: '생성 중', failed: '실패' };
        const sbg = statusBg[g.status] || '#f3f4f6';
        const slabel = statusLabel[g.status] || g.status;
        const retryHtml = g.status === 'failed'
            ? '<button class="btn btn-sm btn-secondary" style="margin-top:8px;width:100%;" onclick="SessionWorkspace.retryGeneration(\'' + esc(g.id) + '\')">다시 생성</button>'
            : '';
        const failureHtml = g.status === 'failed' && g.failure_reason
            ? '<div style="font-size:var(--font-xs);color:var(--color-danger);margin-top:6px;line-height:1.4;max-height:42px;overflow:hidden;" title="' + esc(g.failure_reason) + '">' + esc(g.failure_reason) + '</div>'
            : '';
        return (
            '<div class="img-card" id="gen-card-' + esc(g.id) + '">' +
            imgHtml +
            '<div style="padding:10px;">' +
            '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">' +
            '<span style="font-size:var(--font-xs);padding:2px 6px;border-radius:3px;background:' + sbg + ';">' + slabel + '</span>' +
            '<span style="font-size:var(--font-xs);color:var(--text-muted);">' + esc(outputLabel) + ' · ' + fmtTime(g.created_at) + '</span>' +
            '</div>' +
            (g.prompt ? '<p style="font-size:var(--font-xs);color:var(--text-secondary);margin-top:4px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" title="' + esc(g.prompt) + '">' + esc(g.prompt) + '</p>' : '') +
            (g.provider ? '<div style="font-size:var(--font-xs);color:var(--text-muted);margin-top:2px;">' + esc(g.provider) + (g.model ? ' / ' + esc(g.model) : '') + '</div>' : '') +
            failureHtml +
            retryHtml +
            '</div>' +
            '</div>'
        );
    }

    function _buildGenerationAddCard(kind) {
        const label = kind === 'final' ? '최종안 만들기' : '초안 생성';
        return (
            '<button type="button" class="gen-add-card" onclick="SessionWorkspace.openGenerationDialog(null, \'' + kind + '\')" aria-label="' + esc(label) + '">' +
            '<span class="gen-add-icon" aria-hidden="true">+</span>' +
            '<span class="gen-add-label">' + esc(label) + '</span>' +
            '</button>'
        );
    }

    function renderGenerations(gens) {
        const draftList = document.getElementById('gen-draft-list');
        const finalList = document.getElementById('gen-final-list');
        if (!draftList || !finalList) return;

        if (!gens || gens.length === 0) {
            draftList.innerHTML = _buildGenerationAddCard('draft');
            finalList.innerHTML = _buildGenerationAddCard('final');
            return;
        }

        const drafts = gens.filter(function (g) {
            const kind = normalizeOutputKind((g.generation_params && g.generation_params.output_kind) || '');
            return kind === 'draft';
        });
        const finals = gens.filter(function (g) {
            const kind = normalizeOutputKind((g.generation_params && g.generation_params.output_kind) || '');
            return kind === 'final';
        });

        draftList.innerHTML = drafts.map(_buildGenCard).join('') + _buildGenerationAddCard('draft');
        finalList.innerHTML = finals.map(_buildGenCard).join('') + _buildGenerationAddCard('final');
        renderReportDesignSelector();
    }

    function showGenerationImage(generationId) {
        const gen = (state().generations || []).find(function (g) { return g.id === generationId; });
        if (!gen || !gen.image_url) return;
        const kind = normalizeOutputKind((gen.generation_params && gen.generation_params.output_kind) || '');
        const label = kind === 'final' ? '최종안' : '초안';
        const modal = document.getElementById('gen-image-modal');
        if (!modal) return;
        modal.innerHTML =
            '<div style="position:fixed;inset:0;z-index:9002;background:rgba(15,23,42,0.82);display:flex;align-items:center;justify-content:center;padding:24px;" onclick="if(event.target===this)SessionWorkspace.closeGenerationImage()">' +
            '<div style="max-width:min(1100px,96vw);max-height:94vh;display:flex;flex-direction:column;gap:10px;" onclick="event.stopPropagation()">' +
            '<div style="display:flex;justify-content:space-between;align-items:center;color:white;gap:12px;">' +
            '<div style="font-size:13px;font-weight:700;">' + esc(label) + (gen.provider ? ' · ' + esc(gen.provider) : '') + '</div>' +
            '<button type="button" onclick="SessionWorkspace.closeGenerationImage()" aria-label="닫기" style="border:1px solid rgba(255,255,255,.4);background:rgba(255,255,255,.12);color:white;border-radius:4px;width:34px;height:34px;font-size:20px;cursor:pointer;">×</button>' +
            '</div>' +
            '<img src="' + esc(gen.image_url) + '" alt="' + esc(label) + '" style="max-width:100%;max-height:82vh;object-fit:contain;border-radius:6px;background:white;">' +
            (gen.prompt ? '<div style="max-width:900px;color:#e5e7eb;font-size:12px;line-height:1.5;">' + esc(gen.prompt) + '</div>' : '') +
            '</div>' +
            '</div>';
        modal.style.display = 'block';
    }

    function closeGenerationImage() {
        const modal = document.getElementById('gen-image-modal');
        if (modal) { modal.innerHTML = ''; modal.style.display = 'none'; }
    }

    async function retryGeneration(generationId) {
        showToast('실패한 이미지를 다시 생성합니다.', 'success');
        try {
            const res = await fetch('/api/generations/' + generationId + '/retry', { method: 'POST' });
            if (!res.ok) {
                let message = '재생성 요청 실패';
                try {
                    const payload = await res.json();
                    message = payload.detail || message;
                } catch (_) {}
                throw new Error(message);
            }
            const gen = await res.json();
            await loadGenerations();
            startPollingGeneration(gen.id);
        } catch (err) {
            showToast('재생성 실패: ' + err.message, 'error');
        }
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

    function _setChoiceSelected(containerId, selectedId) {
        const container = document.getElementById(containerId);
        if (!container) return;
        container.querySelectorAll('.gen-choice-card').forEach(function (card) {
            card.classList.toggle('selected', card.getAttribute('data-id') === selectedId);
        });
    }

    function selectGenerationConcept(conceptId) {
        const input = document.getElementById('gen-concept-id');
        if (input) input.value = conceptId || '';
        _setChoiceSelected('gen-concept-grid', conceptId);
    }

    function selectGenerationDraft(draftId) {
        const input = document.getElementById('gen-source-draft');
        if (input) input.value = draftId || '';
        _setChoiceSelected('gen-source-draft-grid', draftId);
    }

    function _populateConceptChoices() {
        const grid = document.getElementById('gen-concept-grid');
        const input = document.getElementById('gen-concept-id');
        if (!grid || !input) return;
        const concepts = state().concepts || [];
        if (concepts.length === 0) {
            input.value = '';
            grid.innerHTML = '<div style="grid-column:1/-1;color:var(--text-muted);font-size:13px;padding:1rem;border:1px dashed var(--border-color);border-radius:6px;text-align:center;">컨셉 후보가 없습니다. 먼저 컨셉을 생성하세요.</div>';
            return;
        }
        const adopted = concepts.find(function (c) { return c.status === 'adopted'; });
        const selectedId = input.value || (adopted ? adopted.id : concepts[0].id);
        input.value = selectedId;
        grid.innerHTML = concepts.map(function (c) {
            const selected = c.id === selectedId ? ' selected' : '';
            const badge = c.status === 'adopted'
                ? '<span style="font-size:10px;color:var(--color-success);font-weight:700;">채택됨</span>'
                : '';
            return (
                '<button type="button" class="gen-choice-card' + selected + '" data-id="' + esc(c.id) + '" onclick="SessionWorkspace.selectGenerationConcept(\'' + esc(c.id) + '\')">' +
                '<div style="display:flex;justify-content:space-between;gap:6px;align-items:flex-start;">' +
                '<div class="gen-choice-title">' + esc(c.name || c.title || '컨셉') + '</div>' + badge +
                '</div>' +
                '<div class="gen-choice-desc">' + esc(c.description || c.rationale || '') + '</div>' +
                '</button>'
            );
        }).join('');
    }

    function _populateDraftChoices(selectedDraftId) {
        const input = document.getElementById('gen-source-draft');
        const grid = document.getElementById('gen-source-draft-grid');
        if (!input || !grid) return;
        const gens = state().generations || [];
        const drafts = gens.filter(function (g) {
            const kind = normalizeOutputKind((g.generation_params && g.generation_params.output_kind) || '');
            return kind === 'draft' && g.status === 'completed' && g.image_url;
        });
        if (drafts.length === 0) {
            input.value = '';
            grid.innerHTML = '<div style="grid-column:1/-1;color:var(--text-muted);font-size:13px;padding:1rem;border:1px dashed var(--border-color);border-radius:6px;text-align:center;">완료된 초안이 없습니다. 먼저 초안을 생성하세요.</div>';
            return;
        }
        const selectedId = selectedDraftId || input.value || drafts[0].id;
        input.value = selectedId;
        grid.innerHTML = drafts.map(function (g, idx) {
            const selected = g.id === selectedId ? ' selected' : '';
            const label = '초안 ' + (idx + 1);
            return (
                '<button type="button" class="gen-choice-card' + selected + '" data-id="' + esc(g.id) + '" onclick="SessionWorkspace.selectGenerationDraft(\'' + esc(g.id) + '\')">' +
                '<img class="gen-draft-thumb" src="' + esc(g.image_url) + '" alt="' + esc(label) + '">' +
                '<div class="gen-choice-title">' + esc(label) + '</div>' +
                '<div class="gen-choice-desc">' + esc(fmtTime(g.created_at)) + '</div>' +
                '</button>'
            );
        }).join('');
    }

    function onOutputKindChange() {
        const kind = document.getElementById('gen-output-kind').value;
        const draftSection = document.getElementById('draft-gen-section');
        const finalSection = document.getElementById('final-gen-section');
        if (kind === 'draft') {
            draftSection.style.display = 'block';
            finalSection.style.display = 'none';
            _populateConceptChoices();
        } else {
            draftSection.style.display = 'none';
            finalSection.style.display = 'block';
            _populateDraftChoices();
        }
    }

    // @MX:ANCHOR: [AUTO] Generation dialog entry point
    // @MX:REASON: Called from abstraction rule cards and main toolbar button (fan_in >= 3)
    async function openGenerationDialog(preselectedRuleId, initialKind, selectedDraftId) {
        void preselectedRuleId;
        const kindSelect = document.getElementById('gen-output-kind');
        const selectedKind = initialKind === 'final' ? 'final' : 'draft';
        if (selectedKind === 'draft' && (!state().concepts || state().concepts.length === 0)) {
            await loadConcepts();
        }
        if (selectedKind === 'final' && (!state().generations || state().generations.length === 0)) {
            await loadGenerations();
        }
        if (kindSelect) kindSelect.value = selectedKind;
        const draftSection = document.getElementById('draft-gen-section');
        const finalSection = document.getElementById('final-gen-section');
        if (draftSection) draftSection.style.display = selectedKind === 'draft' ? 'block' : 'none';
        if (finalSection) finalSection.style.display = selectedKind === 'final' ? 'block' : 'none';
        if (selectedKind === 'final') _populateDraftChoices(selectedDraftId);
        else _populateConceptChoices();
        document.getElementById('gen-dialog').style.display = 'flex';
    }

    function closeGenerationDialog() {
        document.getElementById('gen-dialog').style.display = 'none';
    }

    // @MX:WARN: [AUTO] Branch count >= 8 across draft/final paths and validation
    // @MX:REASON: Two distinct submission flows (draft vs final) with independent validation and payload construction
    async function submitGeneration() {
        const outputKind = document.getElementById('gen-output-kind').value || 'draft';
        const sessionData = state().session;
        const briefId = sessionData && sessionData.brief && sessionData.brief.id ? sessionData.brief.id : null;

        let body = { output_kind: outputKind };
        if (briefId) body.brief_id = briefId;

        if (outputKind === 'draft') {
            const conceptId = document.getElementById('gen-concept-id').value;
            if (!conceptId) { showToast('초안 생성에는 컨셉을 선택해야 합니다.', 'error'); return; }
            body.concept_id = conceptId;
        } else {
            const sourceDraftId = document.getElementById('gen-source-draft').value;
            if (!sourceDraftId) { showToast('기반 초안을 선택하세요.', 'error'); return; }
            const sourceDraft = (state().generations || []).find(function (g) { return g.id === sourceDraftId; });
            if (!sourceDraft) { showToast('초안 정보를 찾을 수 없습니다.', 'error'); return; }
            if (sourceDraft.rule_id) body.rule_id = sourceDraft.rule_id;
            body.source_draft_id = sourceDraftId;
            const feedbackNote = document.getElementById('gen-feedback-note').value.trim();
            if (!feedbackNote) { showToast('최종안 생성에는 수정 피드백을 입력해야 합니다.', 'error'); return; }
            body.feedback_note = feedbackNote;
        }

        closeGenerationDialog();
        showToast('생성 요청을 전송했습니다.', 'success');

        try {
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
            showToast('생성 실패: ' + err.message, 'error');
        }
    }

    // ─── Spec ─────────────────────────────────────────────────────────────────

    function _completedReportDesigns() {
        return (state().generations || []).filter(function (g) {
            return g.status === 'completed' && g.image_url;
        }).sort(function (a, b) {
            const ak = normalizeOutputKind((a.generation_params && a.generation_params.output_kind) || '');
            const bk = normalizeOutputKind((b.generation_params && b.generation_params.output_kind) || '');
            if (ak === 'final' && bk !== 'final') return -1;
            if (ak !== 'final' && bk === 'final') return 1;
            return new Date(b.created_at || 0) - new Date(a.created_at || 0);
        });
    }

    function _reportDesignLabel(gen, idx) {
        const kind = normalizeOutputKind((gen.generation_params && gen.generation_params.output_kind) || '');
        return (kind === 'final' ? '최종안 ' : '초안 ') + (idx + 1);
    }

    function _specsForDesign(designId) {
        return (state().specList || []).filter(function (spec) {
            const selectedId = spec.selected_design_id || (spec.content_json && spec.content_json.selected_design && spec.content_json.selected_design.id);
            return selectedId === designId;
        });
    }

    function selectReportDesign(designId) {
        state().reportSelectedDesignId = designId || '';
        renderReportDesignSelector();
        const specs = _specsForDesign(state().reportSelectedDesignId);
        renderReportVersionTabs(specs.length ? specs[0].id : null);
        if (specs.length) renderSpec(specs[0]);
        else {
            const container = document.getElementById('spec-document');
            const selectedDesign = _completedReportDesigns().find(function (g) { return g.id === state().reportSelectedDesignId; });
            if (container) {
                container.innerHTML =
                    '<div class="spec-section">' +
                    (selectedDesign && selectedDesign.image_url ? '<img class="report-selected-image" src="' + esc(selectedDesign.image_url) + '" alt="선택한 보고서 기준 디자인">' : '') +
                    '<div style="color:var(--text-muted);font-size:13px;text-align:center;padding:18px;border:1px dashed var(--border-color);border-radius:6px;">선택한 이미지의 보고서가 아직 없습니다. 보고서 생성/갱신을 누르면 이 이미지를 기준으로 새 보고서를 작성합니다.</div>' +
                    '</div>';
            }
        }
    }

    function selectReportVersion(specId) {
        const spec = (state().specList || []).find(function (s) { return s.id === specId; });
        if (!spec) return;
        state().spec = spec;
        const selectedId = spec.selected_design_id || (spec.content_json && spec.content_json.selected_design && spec.content_json.selected_design.id);
        if (selectedId) state().reportSelectedDesignId = selectedId;
        renderReportDesignSelector();
        renderReportVersionTabs(spec.id);
        renderSpec(spec);
        ws().updateDecisionPanel();
    }

    function renderReportDesignSelector() {
        const box = document.getElementById('report-design-selector');
        if (!box) return;
        const designs = _completedReportDesigns();
        if (!designs.length) {
            box.innerHTML = '<div style="color:var(--text-muted);font-size:13px;padding:10px 0;">작성 완료된 생성 이미지가 없습니다.</div>';
            return;
        }
        const current = state().reportSelectedDesignId || (state().spec && state().spec.selected_design_id) || designs[0].id;
        state().reportSelectedDesignId = current;
        box.innerHTML = designs.map(function (g, idx) {
            const selected = g.id === current ? ' selected' : '';
            const specs = _specsForDesign(g.id);
            const done = specs.length ? '<span style="color:var(--color-success);">작성 완료</span>' : '<span style="color:var(--text-muted);">미작성</span>';
            const label = _reportDesignLabel(g, idx);
            return '<button type="button" class="report-design-chip' + selected + '" onclick="SessionWorkspace.selectReportDesign(\'' + esc(g.id) + '\')" title="' + esc(label) + '">' +
                '<img src="' + esc(g.image_url) + '" alt="' + esc(label) + '">' +
                '<div class="chip-title"><span>' + esc(label) + '</span>' + done + '</div>' +
                '<div class="chip-meta">' + esc(fmtTime(g.created_at)) + '</div>' +
                '</button>';
        }).join('');
    }

    function renderReportVersionTabs(activeSpecId) {
        const box = document.getElementById('report-version-tabs');
        if (!box) return;
        const designId = state().reportSelectedDesignId || '';
        const specs = designId ? _specsForDesign(designId) : (state().specList || []);
        if (!specs.length) {
            box.innerHTML = '';
            return;
        }
        box.innerHTML = specs.map(function (spec) {
            const active = spec.id === activeSpecId ? ' active' : '';
            return '<button type="button" class="report-version-tab' + active + '" onclick="SessionWorkspace.selectReportVersion(\'' + esc(spec.id) + '\')">v' +
                esc(spec.version || 1) + '</button>';
        }).join('');
    }

    async function loadSpec() {
        const container = document.getElementById('spec-document');
        container.innerHTML = skeleton(200);
        try {
            if (!state().generations || state().generations.length === 0) {
                await loadGenerations();
            }
            const res = await fetch('/api/sessions/' + SID() + '/specs');
            if (!res.ok) throw new Error('보고서 로드 실패');
            const specList = await res.json();
            state().specList = specList || [];
            renderReportDesignSelector();
            if (!specList || specList.length === 0) {
                renderReportVersionTabs(null);
                container.innerHTML = '<div style="color:var(--text-muted);font-size:13px;text-align:center;padding:24px;border:1px dashed var(--border-color);border-radius:6px;">보고서가 없습니다. 작성 완료 이미지를 선택하고 보고서 생성/갱신을 누르세요.</div>';
                return;
            }
            const selectedId = state().reportSelectedDesignId || specList[0].selected_design_id || (specList[0].content_json && specList[0].content_json.selected_design && specList[0].content_json.selected_design.id);
            if (selectedId) state().reportSelectedDesignId = selectedId;
            const filtered = selectedId ? _specsForDesign(selectedId) : specList;
            const spec = filtered[0] || specList[0];
            state().spec = spec;
            renderReportDesignSelector();
            renderReportVersionTabs(spec.id);
            renderSpec(spec);
            ws().updateDecisionPanel();
        } catch (err) {
            container.innerHTML = errBlock('보고서 로드 실패', 'SessionWorkspace.loadSpec()');
        }
    }

    async function generateSpec() {
        const container = document.getElementById('spec-document');
        if (!state().generations || state().generations.length === 0) {
            await loadGenerations();
        }
        renderReportDesignSelector();
        const selectedDesignId = state().reportSelectedDesignId;
        if (!selectedDesignId) {
            showToast('보고서 기준으로 사용할 작성 완료 이미지를 선택하세요.', 'error');
            return;
        }
        container.innerHTML = skeleton(200);
        try {
            const res = await fetch('/api/sessions/' + SID() + '/specs', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ selected_design_id: selectedDesignId })
            });
            if (!res.ok) throw new Error('보고서 생성 실패');
            const spec = await res.json();
            state().spec = spec;
            state().specList = [spec].concat((state().specList || []).filter(function (s) { return s.id !== spec.id; }));
            state().reportSelectedDesignId = spec.selected_design_id || selectedDesignId;
            renderReportDesignSelector();
            renderReportVersionTabs(spec.id);
            renderSpec(spec);
            ws().updateDecisionPanel();
            showToast('디자인 보고서가 생성되었습니다.', 'success');
        } catch (err) {
            container.innerHTML = errBlock('보고서 생성 실패', 'SessionWorkspace.loadSpec()');
            showToast('보고서 생성 실패: ' + err.message, 'error');
        }
    }

    function renderSpec(spec) {
        const container = document.getElementById('spec-document');
        if (!spec) { container.innerHTML = '<div style="color:var(--text-muted);">보고서가 없습니다.</div>'; return; }
        const c = spec.content_json || {};
        const html = [];
        const selectedDesign = c.selected_design;

        // 1. 표지 정보
        html.push(
            '<div class="spec-section">' +
            '<h4>1. 보고서 개요</h4>' +
            (selectedDesign && selectedDesign.image_url ? '<img class="report-selected-image" src="' + esc(selectedDesign.image_url) + '" alt="보고서 기준 디자인">' : '') +
            '<dl class="spec-meta-row">' +
            '<dt>버전</dt><dd>v' + (spec.version || 1) + ' · ' + esc(spec.status || 'draft') + '</dd>' +
            '<dt>기준 이미지</dt><dd>' + esc(selectedDesign ? ((selectedDesign.output_kind === 'final' ? '최종안' : '초안') + ' · ' + selectedDesign.id) : '-') + '</dd>' +
            '<dt>생성 시각</dt><dd>' + esc(c.generated_at ? new Date(c.generated_at).toLocaleString('ko-KR') : '-') + '</dd>' +
            '</dl>' +
            '</div>'
        );

        // 2. 브리프
        if (c.brief && Object.keys(c.brief).length) {
            const b = c.brief;
            html.push(
                '<div class="spec-section">' +
                '<h4>2. 디자인 브리프</h4>' +
                (b.purpose ? '<p>' + esc(b.purpose) + '</p>' : '') +
                '<dl class="spec-meta-row">' +
                (b.domain        ? '<dt>도메인</dt><dd>' + esc(b.domain) + '</dd>' : '') +
                (b.target_user   ? '<dt>타깃 사용자</dt><dd>' + esc(b.target_user) + '</dd>' : '') +
                (b.context       ? '<dt>맥락</dt><dd>' + esc(b.context) + '</dd>' : '') +
                (b.constraints   ? '<dt>제약</dt><dd>' + esc(b.constraints) + '</dd>' : '') +
                (b.use_case      ? '<dt>사용 시나리오</dt><dd>' + esc(b.use_case) + '</dd>' : '') +
                (b.result_form   ? '<dt>결과 형식</dt><dd>' + esc(b.result_form) + '</dd>' : '') +
                '</dl>' +
                '</div>'
            );
        }

        // 3. 채택 컨셉 (스토리)
        const finalConcepts = c.final_concept || [];
        if (finalConcepts.length) {
            const items = finalConcepts.map(function (k) {
                return '<div class="spec-list-item">' +
                    '<div class="item-title">' + esc(k.name || '이름 없음') + '</div>' +
                    (k.description ? '<div class="item-desc">' + esc(k.description) + '</div>' : '') +
                    (k.rationale ? '<div class="item-desc" style="margin-top:6px;"><strong>채택 이유:</strong> ' + esc(k.rationale) + '</div>' : '') +
                    (k.risk ? '<div class="item-meta">리스크: ' + esc(k.risk) + '</div>' : '') +
                    '</div>';
            }).join('');
            html.push('<div class="spec-section"><h4>3. 채택된 디자인 컨셉</h4><div class="spec-list">' + items + '</div></div>');
        }

        // 4. 생성 이미지
        const designs = c.generated_designs || [];
        if (designs.length) {
            const imgs = designs.map(function (d) {
                const label = d.output_kind === 'final' ? '최종안' : '초안';
                return '<div class="spec-list-item">' +
                    (d.image_url ? '<img src="' + esc(d.image_url) + '" alt="' + esc(label) + '" style="width:100%;max-height:260px;object-fit:contain;background:#f8fafc;border-radius:6px;margin-bottom:8px;">' : '') +
                    '<div class="item-title">' + esc(label) + '</div>' +
                    (d.prompt ? '<div class="item-desc">' + esc(d.prompt) + '</div>' : '') +
                    (d.provider ? '<div class="item-meta">' + esc(d.provider) + (d.model ? ' / ' + esc(d.model) : '') + '</div>' : '') +
                    '</div>';
            }).join('');
            html.push('<div class="spec-section"><h4>4. 생성 이미지 목록</h4><div class="spec-list">' + imgs + '</div></div>');
        }

        // 5. 디자인 제작 가이드 (추상화 규칙에서 형태/구조/소재 도출)
        const rules = c.abstraction_rules || [];
        if (rules.length) {
            const items = rules.map(function (r) {
                return '<div class="spec-list-item">' +
                    '<div class="item-title">재현 가능한 디자인 규칙</div>' +
                    (r.form ? '<div class="item-desc"><strong>형태:</strong> ' + esc(r.form) + '</div>' : '') +
                    (r.structure ? '<div class="item-desc" style="margin-top:6px;"><strong>구조:</strong> ' + esc(r.structure) + '</div>' : '') +
                    (r.surface ? '<div class="item-desc" style="margin-top:6px;"><strong>표면:</strong> ' + esc(r.surface) + '</div>' : '') +
                    (r.color_material ? '<div class="item-desc" style="margin-top:6px;"><strong>색상/소재:</strong> ' + esc(r.color_material) + '</div>' : '') +
                    (r.usability ? '<div class="item-desc" style="margin-top:6px;"><strong>사용성:</strong> ' + esc(r.usability) + '</div>' : '') +
                    (r.sketch_prompt ? '<div class="item-meta">스케치 프롬프트: ' + esc(r.sketch_prompt) + '</div>' : '') +
                    '</div>';
            }).join('');
            html.push('<div class="spec-section"><h4>5. 디자인 제작 가이드</h4><p class="muted">이미지를 보지 않아도 재현할 수 있도록 형태, 구조, 표면, 소재 기준을 정리합니다.</p><div class="spec-list">' + items + '</div></div>');
        }

        // 6. 트렌드 근거
        const trends = (c.trend_evidence || []).filter(function (t) {
            const text = (t.summary || t.title || '').trim();
            return text && text.indexOf('기사가 제공되지 않아') === -1;
        });
        if (trends.length) {
            const items = trends.slice(0, 10).map(function (t) {
                const sources = (t.source_urls || []).map(function (s) { return typeof s === 'string' ? s : s.url; }).filter(Boolean);
                return '<blockquote class="spec-quote">' +
                    esc(t.summary || t.title || '') +
                    (sources.length ? '<span class="src">출처: ' + sources.map(function (u) { return '<a href="' + esc(u) + '" target="_blank" rel="noopener">' + esc(u) + '</a>'; }).join(' · ') + '</span>' : '') +
                    '</blockquote>';
            }).join('');
            html.push('<div class="spec-section"><h4>6. 트렌드 근거</h4>' + items + '</div>');
        }

        // 7. 이미지 레퍼런스
        const refs = c.image_references || c.reference_board || [];
        if (refs.length) {
            const items = refs.slice(0, 12).map(function (r) {
                return '<div class="spec-list-item">' +
                    (r.thumbnail_url ? '<img src="' + esc(r.thumbnail_url) + '" alt="이미지 레퍼런스" style="width:100%;height:180px;object-fit:cover;border-radius:6px;margin-bottom:8px;">' : '') +
                    '<div class="item-title">' + esc(r.title || '레퍼런스') + '</div>' +
                    (r.url ? '<div class="item-meta"><a href="' + esc(r.url) + '" target="_blank" rel="noopener">' + esc(r.url) + '</a></div>' : '') +
                    (r.copyright_risk ? '<div class="item-meta">저작권 위험: ' + esc(r.copyright_risk) + '</div>' : '') +
                    '</div>';
            }).join('');
            html.push('<div class="spec-section"><h4>7. 이미지 레퍼런스</h4><div class="spec-list">' + items + '</div></div>');
        }

        // 8. 폐기된 대안
        const discarded = c.discarded_alternatives || [];
        if (discarded.length) {
            const items = discarded.map(function (d) {
                return '<div class="spec-list-item">' +
                    '<div class="item-title">' + esc(d.name || '이름 없음') + '</div>' +
                    (d.reason ? '<div class="item-desc">사유: ' + esc(d.reason) + '</div>' : '<div class="item-meta">사유 미기록</div>') +
                    '</div>';
            }).join('');
            html.push('<div class="spec-section"><h4>8. 폐기된 대안</h4><div class="spec-list">' + items + '</div></div>');
        }

        // 9. 결정 근거 요약
        const dr = c.decision_rationale;
        if (dr) {
            html.push(
                '<div class="spec-section">' +
                '<h4>9. 결정 근거 요약</h4>' +
                '<dl class="spec-meta-row">' +
                '<dt>채택 컨셉 수</dt><dd>' + esc(dr.adopted_count) + '</dd>' +
                '<dt>폐기 대안 수</dt><dd>' + esc(dr.discarded_count) + '</dd>' +
                '<dt>선택 기준</dt><dd>' + esc(dr.selection_criteria || '-') + '</dd>' +
                ((dr.adopted_concepts && dr.adopted_concepts.length) ? '<dt>채택 목록</dt><dd>' + dr.adopted_concepts.map(esc).join(', ') + '</dd>' : '') +
                '</dl>' +
                '</div>'
            );
        }

        // 10. 출처
        const sources = c.sources || [];
        if (sources.length) {
            const items = sources.slice(0, 30).map(function (u) {
                return '<li style="margin-bottom:4px;"><a href="' + esc(u) + '" target="_blank" rel="noopener" style="font-size:13px;">' + esc(u) + '</a></li>';
            }).join('');
            html.push('<div class="spec-section"><h4>10. 트렌드 출처</h4><ul style="padding-left:18px;margin:0;">' + items + '</ul></div>');
        }

        if (!html.length) {
            container.innerHTML = '<div style="color:var(--text-muted);font-size:14px;text-align:center;padding:2rem;">보고서 내용이 없습니다.</div>';
            return;
        }
        container.innerHTML = html.join('');
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
        sw.showTrendSources = showTrendSources;
        sw.closeTrendDetailModal = closeTrendDetailModal;
        sw.loadConcepts = loadConcepts;
        sw.generateConcepts = generateConcepts;
        sw.showConceptDetail = showConceptDetail;
        sw.closeConceptDetail = closeConceptDetail;
        sw.decideConcept = decideConcept;
        sw.loadReferences = loadReferences;
        sw.searchReferences = searchReferences;
        sw.searchDesignReferences = searchDesignReferences;
        sw.openDesignRef = openDesignRef;
        sw.analyzeReference = analyzeReference;
        sw.showRefDetail = showRefDetail;
        sw.closeRefDetailModal = closeRefDetailModal;
        sw.loadAbstraction = loadAbstraction;
        sw.generateAbstraction = generateAbstraction;
        sw.loadGenerations = loadGenerations;
        sw.showGenerationImage = showGenerationImage;
        sw.closeGenerationImage = closeGenerationImage;
        sw.retryGeneration = retryGeneration;
        sw.openGenerationDialog = openGenerationDialog;
        sw.closeGenerationDialog = closeGenerationDialog;
        sw.onOutputKindChange = onOutputKindChange;
        sw.selectGenerationConcept = selectGenerationConcept;
        sw.selectGenerationDraft = selectGenerationDraft;
        sw.submitGeneration = submitGeneration;
        sw.loadSpec = loadSpec;
        sw.generateSpec = generateSpec;
        sw.selectReportDesign = selectReportDesign;
        sw.selectReportVersion = selectReportVersion;
        sw.printSpec = printSpec;
    });
}());
