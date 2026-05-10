/**
 * Settings Page — AI Model Configuration
 */
(function () {
    'use strict';

    const state = {
        catalog: {},          // provider -> {label, configured, models[]}
        featureModels: {},    // feature_key -> FeatureModelResponse
        trendSettings: null,
        trendSources: [],
        enabledSourceIds: [],
    };

    // ─── Feature definitions ──────────────────────────────────────────────────

    const FEATURES = [
        {
            key: 'brief_structuring',
            label: '1. 브리프 구조화',
            desc: '사용자 입력을 구조화된 디자인 브리프로 변환합니다.',
            needs: [],
        },
        {
            key: 'trend_analysis',
            label: '2. 트렌드 분석',
            desc: '웹 크롤링 결과에서 트렌드 인사이트를 추출합니다.',
            needs: [],
        },
        {
            key: 'concept_generation',
            label: '3. 컨셉 후보 생성',
            desc: '트렌드 증거를 기반으로 디자인 컨셉 후보를 생성합니다.',
            needs: [],
        },
        {
            key: 'reference_analysis',
            label: '4. 레퍼런스 분석',
            desc: '수집된 레퍼런스 이미지의 시각 요소를 분석합니다.',
            needs: ['multimodal'],
        },
        {
            key: 'sketch_analysis',
            label: '4. 스케치 분석',
            desc: '업로드된 스케치 이미지를 분석하여 디자인 의도를 파악합니다.',
            needs: ['multimodal'],
        },
        {
            key: 'abstraction',
            label: '5. 추상화 규칙 생성',
            desc: '레퍼런스/스케치 분석에서 생성 근거가 되는 추상화 규칙을 도출합니다.',
            needs: [],
        },
        {
            key: 'sketch_prompt_generation',
            label: '6A. 스케치 프롬프트 작성',
            desc: '추상화 규칙을 스케치 생성 모델용 프롬프트로 변환합니다.',
            needs: [],
        },
        {
            key: 'sketch_generation',
            label: '6B. 스케치 생성',
            desc: '스케치 프롬프트를 사용해 탐색용 디자인 스케치를 생성합니다.',
            needs: ['image'],
        },
        {
            key: 'final_image_prompt_generation',
            label: '7A. 최종 이미지 프롬프트 작성',
            desc: '추상화 규칙을 최종 프레젠테이션 이미지용 프롬프트로 변환합니다.',
            needs: [],
        },
        {
            key: 'final_image_generation',
            label: '7B. 최종 이미지 생성',
            desc: '최종 이미지 프롬프트를 사용해 완성 디자인 이미지를 생성합니다.',
            needs: ['image'],
        },
        {
            key: 'spec_writing',
            label: '8. 스펙 문서 작성',
            desc: '최종 디자인 스펙 문서를 작성합니다.',
            needs: [],
        },
        {
            key: 'chat',
            label: '상시. 챗봇 협업',
            desc: '세션 내 디자이너와 AI 간 자유 대화를 지원합니다.',
            needs: [],
        },
    ];

    // ─── Helpers ──────────────────────────────────────────────────────────────

    function esc(t) {
        const d = document.createElement('div');
        d.textContent = String(t || '');
        return d.innerHTML;
    }

    function showToast(msg, type) {
        const el = document.getElementById('toast');
        if (!el) return;
        el.textContent = msg;
        el.style.display = 'block';
        el.style.background = type === 'error' ? '#fee2e2' : '#d1fae5';
        el.style.color    = type === 'error' ? '#b91c1c' : '#065f46';
        el.style.border   = type === 'error' ? '1px solid #fca5a5' : '1px solid #6ee7b7';
        clearTimeout(el._t);
        el._t = setTimeout(() => { el.style.display = 'none'; }, 3000);
    }

    // ─── Provider Status ──────────────────────────────────────────────────────

    function renderProviderStatus() {
        const container = document.getElementById('provider-status-list');
        if (!container) return;
        const LABELS = {
            openai: 'OpenAI', gemini: 'Google Gemini', anthropic: 'Anthropic',
            deepseek: 'DeepSeek', alibaba: 'Alibaba (Qwen)', xiaomi: 'Xiaomi Mimo',
            minimax: 'Minimax', kimi: 'Kimi', seedream: 'Seedream',
        };
        container.innerHTML = Object.entries(state.catalog).map(([p, info]) => {
            const ok = info.configured;
            return `<div class="provider-badge ${ok ? 'active' : 'inactive'}">
                <span class="provider-dot">${ok ? '✓' : '○'}</span>
                <span>${esc(info.label || LABELS[p] || p)}</span>
                <span class="provider-status-txt">${ok ? '활성' : '미설정'}</span>
            </div>`;
        }).join('');
    }

    // ─── Model dropdown builder ───────────────────────────────────────────────

    function buildModelOptions(featureNeeds, selectedProvider, selectedModel) {
        let html = '<option value="">— 모델 선택 —</option>';
        Object.entries(state.catalog).forEach(([provider, info]) => {
            if (!info.configured) return;
            const compatibleModels = (info.models || []).filter(m => {
                if (featureNeeds.includes('image')) return m.types.includes('image');
                if (featureNeeds.includes('multimodal')) return m.types.includes('multimodal') || m.types.includes('text');
                return m.types.includes('text') || m.types.includes('multimodal');
            });
            if (!compatibleModels.length) return;
            html += `<optgroup label="${esc(info.label || provider)}">`;
            compatibleModels.forEach(m => {
                const val = `${provider}::${m.id}`;
                const sel = (provider === selectedProvider && m.id === selectedModel) ? ' selected' : '';
                html += `<option value="${esc(val)}"${sel}>${esc(m.label)} · ${esc(provider)}</option>`;
            });
            html += '</optgroup>';
        });
        return html;
    }

    // ─── Capability badges ────────────────────────────────────────────────────

    function capabilityBadges(needs) {
        return needs.map(n => {
            if (n === 'image') return '<span class="cap-badge cap-image">이미지 생성 필요</span>';
            if (n === 'multimodal') return '<span class="cap-badge cap-multi">멀티모달 필요</span>';
            return '';
        }).join('');
    }

    // ─── Feature model rows ───────────────────────────────────────────────────

    function renderFeatureModels() {
        const container = document.getElementById('feature-models-container');
        if (!container) return;

        if (!Object.keys(state.catalog).length) {
            container.innerHTML = '<div class="empty-state">모델 카탈로그를 불러오는 중...</div>';
            return;
        }

        container.innerHTML = FEATURES.map(f => {
            const saved = state.featureModels[f.key] || {};
            const retryPrimary = saved.retry_count ?? 2;
            const retryFallback = saved.fallback_retry_count ?? 1;
            const hasConfig = saved.provider && saved.model;

            return `
            <div class="fm-row" data-key="${esc(f.key)}">
                <div class="fm-info">
                    <div class="fm-label-row">
                        <span class="fm-label">${esc(f.label)}</span>
                        <span class="fm-status ${hasConfig ? 'ok' : 'warn'}">${hasConfig ? '설정됨' : '미설정'}</span>
                        ${capabilityBadges(f.needs)}
                    </div>
                    <div class="fm-desc">${esc(f.desc)}</div>
                </div>
                <div class="fm-controls">
                    <div class="fm-group">
                        <label class="fm-group-label">기본 모델</label>
                        <div class="fm-row-controls">
                            <select class="fm-select" data-role="primary" data-key="${esc(f.key)}">
                                ${buildModelOptions(f.needs, saved.provider, saved.model)}
                            </select>
                            <div class="fm-retry-wrap">
                                <span class="fm-retry-label">재시도</span>
                                <input class="fm-retry" type="number" min="0" max="5" value="${retryPrimary}"
                                    data-role="retry_count" data-key="${esc(f.key)}">
                            </div>
                        </div>
                    </div>
                    <div class="fm-group">
                        <label class="fm-group-label">대체 모델</label>
                        <div class="fm-row-controls">
                            <select class="fm-select" data-role="fallback" data-key="${esc(f.key)}">
                                <option value="">— 없음 —</option>
                                ${buildModelOptions(f.needs, saved.fallback_provider, saved.fallback_model)}
                            </select>
                            <div class="fm-retry-wrap">
                                <span class="fm-retry-label">재시도</span>
                                <input class="fm-retry" type="number" min="0" max="5" value="${retryFallback}"
                                    data-role="fallback_retry_count" data-key="${esc(f.key)}">
                            </div>
                        </div>
                    </div>
                    <button class="btn btn-secondary btn-sm fm-save-btn" onclick="window._testFM('${esc(f.key)}', this)">연결 확인</button>
                    <button class="btn btn-primary btn-sm fm-save-btn" onclick="window._saveFM('${esc(f.key)}', this)">저장</button>
                </div>
            </div>`;
        }).join('');
    }

    // ─── Save single feature model ────────────────────────────────────────────

    window._saveFM = async function (featureKey, btn) {
        const row = document.querySelector(`.fm-row[data-key="${featureKey}"]`);
        if (!row) return;

        const primaryVal  = row.querySelector('[data-role="primary"]').value;
        const fallbackVal = row.querySelector('[data-role="fallback"]').value;
        const retryCount  = parseInt(row.querySelector('[data-role="retry_count"]').value, 10) || 2;
        const fbRetry     = parseInt(row.querySelector('[data-role="fallback_retry_count"]').value, 10) || 1;

        if (!primaryVal || !primaryVal.includes('::')) {
            showToast('기본 모델을 선택해 주세요.', 'error');
            return;
        }

        const [provider, model] = primaryVal.split('::');
        let fallback_provider = null;
        let fallback_model = null;
        if (fallbackVal && fallbackVal.includes('::') && fallbackVal !== '::') {
            [fallback_provider, fallback_model] = fallbackVal.split('::');
        }

        btn.disabled = true;
        btn.textContent = '저장 중...';

        try {
            const res = await fetch(`/api/workspace/feature-models/${encodeURIComponent(featureKey)}`, {
                method: 'PUT',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    provider, model,
                    retry_count: retryCount,
                    fallback_provider,
                    fallback_model,
                    fallback_retry_count: fbRetry,
                }),
            });
            if (!res.ok) throw new Error(await res.text());
            const updated = await res.json();
            state.featureModels[featureKey] = updated;

            // Update status badge in-place
            const statusEl = row.querySelector('.fm-status');
            if (statusEl) {
                statusEl.textContent = '설정됨';
                statusEl.className = 'fm-status ok';
            }
            showToast(`'${FEATURES.find(f => f.key === featureKey)?.label}' 저장 완료`, 'success');
        } catch (e) {
            showToast('저장 실패: ' + e.message, 'error');
        } finally {
            btn.disabled = false;
            btn.textContent = '저장';
        }
    };

    window._testFM = async function (featureKey, btn) {
        btn.disabled = true;
        btn.textContent = '확인 중...';
        try {
            const res = await fetch(`/api/workspace/feature-models/${encodeURIComponent(featureKey)}/connection-test`, {
                method: 'POST',
            });
            const data = await res.json().catch(() => ({}));
            if (!res.ok || !data.ok) throw new Error(data.detail || data.message || '연결 실패');
            showToast(data.message || '연결 확인 완료', 'success');
        } catch (e) {
            showToast('연결 확인 실패: ' + e.message, 'error');
        } finally {
            btn.disabled = false;
            btn.textContent = '연결 확인';
        }
    };

    // ─── Search Backend ────────────────────────────────────────────────────

    function loadSearchBackend() {
        try {
            const s = {
                backend: window.__searchBackend || 'none',
                externalUrl: window.__searchExternalUrl || '',
                externalToken: window.__searchExternalToken || '',
                searxngUrl: window.__searchSearxngUrl || '',
                crawl4aiUrl: window.__searchCrawl4aiUrl || '',
            };
            const sel = document.getElementById('search-backend-select');
            if (sel) sel.value = s.backend;
            const extUrl = document.getElementById('search-external-url');
            if (extUrl) extUrl.value = s.externalUrl;
            const extTok = document.getElementById('search-external-token');
            if (extTok) extTok.value = s.externalToken;
            const sxUrl = document.getElementById('search-searxng-url');
            if (sxUrl) sxUrl.value = s.searxngUrl;
            const c4Url = document.getElementById('search-crawl4ai-url');
            if (c4Url) c4Url.value = s.crawl4aiUrl;
            toggleSearchBackendFields(s.backend);
        } catch (e) {
            console.error('Search backend load error:', e);
        }
    }

    function toggleSearchBackendFields(backend) {
        ['external', 'searxng', 'crawl4ai'].forEach(id => {
            const el = document.getElementById('search-backend-' + id);
            if (el) el.style.display = (id === backend) ? 'block' : 'none';
        });
    }

    window._onSearchBackendChange = function () {
        const sel = document.getElementById('search-backend-select');
        toggleSearchBackendFields(sel ? sel.value : 'none');
    };

    window._saveSearchBackend = async function () {
        const sel = document.getElementById('search-backend-select');
        const backend = sel ? sel.value : 'none';
        const payload = { search_backend: backend };

        if (backend === 'external') {
            payload.web_search_crawler_api_base_url = document.getElementById('search-external-url')?.value.trim() || null;
            payload.web_search_crawler_api_token = document.getElementById('search-external-token')?.value.trim() || null;
        } else if (backend === 'searxng') {
            payload.searxng_api_url = document.getElementById('search-searxng-url')?.value.trim() || null;
        } else if (backend === 'crawl4ai') {
            payload.crawl4ai_api_url = document.getElementById('search-crawl4ai-url')?.value.trim() || null;
        }

        try {
            const res = await fetch('/api/workspace/search-backend', {
                method: 'PUT',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(payload),
            });
            if (!res.ok) throw new Error(await res.text());
            showToast('검색 백엔드 설정이 저장되었습니다.', 'success');
        } catch (e) {
            showToast('저장 실패: ' + e.message, 'error');
        }
    };

    window._testSearchBackend = async function () {
        const statusEl = document.getElementById('search-backend-status');
        if (statusEl) {
            statusEl.style.display = 'block';
            statusEl.style.background = '#fef3c7';
            statusEl.style.color = '#92400e';
            statusEl.textContent = '연결 확인 중...';
        }
        try {
            const res = await fetch('/api/workspace/search-backend/test', {method: 'POST'});
            const data = await res.json().catch(() => ({}));
            if (statusEl) {
                if (data.ok) {
                    statusEl.style.background = '#d1fae5';
                    statusEl.style.color = '#065f46';
                    statusEl.textContent = data.message || '연결 확인 완료';
                } else {
                    statusEl.style.background = '#fee2e2';
                    statusEl.style.color = '#b91c1c';
                    statusEl.textContent = data.detail || data.message || '연결 실패';
                }
            }
        } catch (e) {
            if (statusEl) {
                statusEl.style.background = '#fee2e2';
                statusEl.style.color = '#b91c1c';
                statusEl.textContent = '연결 확인 실패: ' + e.message;
            }
        }
    };

    // ─── Trend Settings ───────────────────────────────────────────────────────

    async function loadTrendSettings() {
        const container = document.getElementById('trend-settings-container');
        try {
            const res = await fetch('/api/workspace/trend-settings');
            if (!res.ok) throw new Error('로드 실패');
            state.trendSettings = await res.json();
            renderTrendSettings();
        } catch (e) {
            if (container) container.innerHTML = '<div style="color:var(--color-danger);font-size:var(--font-sm);">트렌드 설정 로드 실패</div>';
        }
    }

    function renderTrendSettings() {
        const container = document.getElementById('trend-settings-container');
        if (!container || !state.trendSettings) return;
        const s = state.trendSettings;
        container.innerHTML = `
            <div style="display:flex;align-items:flex-end;gap:1.5rem;flex-wrap:wrap;">
                <div style="display:flex;flex-direction:column;gap:3px;">
                    <label for="trend-domain" style="font-size:var(--font-xs);font-weight:600;color:var(--text-muted);white-space:nowrap;">기본 도메인</label>
                    <select id="trend-domain" style="width:160px;">
                        <option value="">전체</option>
                        <option value="industrial"     ${s.default_domain === 'industrial'     ? 'selected' : ''}>산업디자인</option>
                        <option value="product_service"${s.default_domain === 'product_service'? 'selected' : ''}>제품·서비스</option>
                        <option value="visual"         ${s.default_domain === 'visual'         ? 'selected' : ''}>시각디자인</option>
                        <option value="advertising"    ${s.default_domain === 'advertising'    ? 'selected' : ''}>광고·브랜딩</option>
                    </select>
                </div>
                <div style="display:flex;flex-direction:column;gap:3px;">
                    <label for="trend-days" style="font-size:var(--font-xs);font-weight:600;color:var(--text-muted);white-space:nowrap;">수집 기간 (일)</label>
                    <input type="number" id="trend-days" value="${s.recency_days || 365}" min="7" max="1095"
                           style="width:90px;" autocomplete="off">
                </div>
            </div>`;
    }

    window.saveTrendSettings = async function () {
        const domain = document.getElementById('trend-domain')?.value;
        const days   = parseInt(document.getElementById('trend-days')?.value || '365', 10);
        try {
            const res = await fetch('/api/workspace/trend-settings', {
                method: 'PUT',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({default_domain: domain || null, recency_days: days}),
            });
            if (!res.ok) throw new Error(await res.text());
            showToast('트렌드 설정 저장 완료', 'success');
        } catch (e) {
            showToast('저장 실패: ' + e.message, 'error');
        }
    };

    // ─── Trend Sources ────────────────────────────────────────────────────────

    async function loadTrendSources() {
        const container = document.getElementById('trend-sources-list');
        try {
            const res = await fetch('/api/trends/sources');
            if (!res.ok) throw new Error('로드 실패');
            state.trendSources = await res.json();
            renderTrendSources();
        } catch {
            if (container) container.innerHTML = '<div class="empty-state">소스 로드 실패</div>';
        }
    }

    function renderTrendSources() {
        const container = document.getElementById('trend-sources-list');
        if (!container) return;
        if (!state.trendSources.length) {
            container.innerHTML = '<div class="empty-state">등록된 트렌드 소스가 없습니다.</div>';
            return;
        }
        const domainLabels = {
            general: '일반',
            industrial: '산업디자인',
            product_service: '제품·서비스',
            visual: '시각디자인',
            advertising: '광고·브랜딩'
        };
        container.innerHTML = state.trendSources.map(src => `
            <div class="source-item">
                <div>
                    <div style="font-weight:600;font-size:var(--font-sm);">${esc(src.name)}</div>
                    <div style="font-size:var(--font-xs);color:var(--text-muted);">${esc(src.url)}</div>
                </div>
                <div style="display:flex;align-items:center;gap:0.5rem;">
                    <span class="domain-badge">${esc(domainLabels[src.domain] || src.domain || '일반')}</span>
                    <button class="btn btn-secondary btn-sm" onclick="window._deleteSource('${esc(src.id)}')">삭제</button>
                </div>
            </div>`).join('');
    }

    window.openAddSourceModal = function () {
        const m = document.getElementById('add-source-modal');
        if (m) m.style.display = 'flex';
    };
    window.closeAddSourceModal = function () {
        const m = document.getElementById('add-source-modal');
        if (m) m.style.display = 'none';
    };

    window.addTrendSource = async function () {
        const name   = document.getElementById('new-source-name')?.value.trim();
        const url    = document.getElementById('new-source-url')?.value.trim();
        const domain = document.getElementById('new-source-domain')?.value;
        if (!name || !url) { showToast('이름과 URL을 입력해 주세요.', 'error'); return; }
        try {
            const res = await fetch('/api/trends/sources', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({name, url, domain}),
            });
            if (!res.ok) throw new Error(await res.text());
            window.closeAddSourceModal();
            await loadTrendSources();
            showToast('소스가 추가되었습니다.', 'success');
        } catch (e) {
            showToast('추가 실패: ' + e.message, 'error');
        }
    };

    window._deleteSource = async function (id) {
        if (!confirm('이 소스를 삭제하시겠습니까?')) return;
        try {
            await fetch(`/api/trends/sources/${id}`, {method: 'DELETE'});
            await loadTrendSources();
            showToast('소스가 삭제되었습니다.', 'success');
        } catch (e) {
            showToast('삭제 실패: ' + e.message, 'error');
        }
    };

    // ─── Init ─────────────────────────────────────────────────────────────────

    window._settingsInit = async function () {
        try {
            const [catalogRes, modelsRes] = await Promise.all([
                fetch('/api/workspace/available-models'),
                fetch('/api/workspace/feature-models'),
            ]);
            state.catalog = catalogRes.ok ? await catalogRes.json() : {};
            const modelsList = modelsRes.ok ? await modelsRes.json() : [];
            modelsList.forEach(m => { state.featureModels[m.feature_key] = m; });

            renderProviderStatus();
            renderFeatureModels();

            // Load search backend config
            try {
                const sbRes = await fetch('/api/workspace/search-backend');
                if (sbRes.ok) {
                    const sb = await sbRes.json();
                    window.__searchBackend = sb.search_backend || 'none';
                    window.__searchExternalUrl = sb.web_search_crawler_api_base_url || '';
                    window.__searchExternalToken = sb.web_search_crawler_api_token || '';
                    window.__searchSearxngUrl = sb.searxng_api_url || '';
                    window.__searchCrawl4aiUrl = sb.crawl4ai_api_url || '';
                }
            } catch (_) { /* non-critical */ }
            loadSearchBackend();
        } catch (e) {
            showToast('설정 로드 실패: ' + e.message, 'error');
        }

        await Promise.all([loadTrendSettings(), loadTrendSources()]);
    };

    document.addEventListener('DOMContentLoaded', window._settingsInit);
})();
