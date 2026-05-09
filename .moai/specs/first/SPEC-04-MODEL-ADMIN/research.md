# Research: SPEC-04-MODEL-ADMIN

Codebase analysis for AI model catalog, ModelRouter, admin console, policy management, and provider integration.

## API Keys Status (CORRECTED - All Configured)

Previous analysis incorrectly stated keys were empty. ALL provider API keys are configured:

| Provider | Key Variable | Value Status | Endpoint |
|----------|-------------|-------------|----------|
| Google Gemini | `GEMINI_API_KEYS` | Configured | `https://generativelanguage.googleapis.com/v1beta` |
| DeepSeek | `DEEPSEEK_API_KEY` | Configured | `https://api.deepseek.com` |
| ByteDance Seedream | `BYTEDANCE_SEEDREAM_API_KEY` | **Configured** (`a79b284f-...`) | `https://ark.ap-southeast.bytepluses.com/api/v3` |
| OpenAI | `OPENAI_API_KEY` | **Configured** (`sk-proj-...`) | `https://api.openai.com/v1` |
| Alibaba/Qwen | `ALIBABA_API_KEY` | **Configured** (`sk-e1f87...`) | `https://dashscope-intl.aliyuncs.com/compatible-mode/v1` |
| Xiaomi MiMo | `XIAOMI_MIMO_API_KEY` | Configured | `https://api.xiaomimimo.com/v1` |
| MiniMax | `MINIMAX_API_KEY` | Configured | `https://api.minimax.io/v1` |
| Kimi/Moonshot | `KIMI_API_KEY` | Configured | `https://api.moonshot.ai/v1` |

## Available Model Catalog (from .env Comparison Tables)

### Text/Multimodal Models (30+ models across 8 providers)

**High Performance (종합 ≥ 78):**

| Model | API model_id | 종합 | 가격점수 | SPD | MM | Provider |
|-------|-------------|------|---------|-----|-----|----------|
| gemini-3.1-pro | gemini-3.1-pro-preview | 85 | 36 | 45 | Y | Google |
| gpt-5.4 | gpt-5.4 | 85 | 20 | 77 | Y | OpenAI |
| qwen3.6-Max | qwen3.6-max-preview | 84 | 69 | 20 | Y* | Alibaba |
| mimo-v2.5-pro | mimo-v2.5-pro | 83 | 84 | 65 | N | Xiaomi |
| kimi-k2.6 | kimi-k2.6 | 82 | 79 | 47 | Y | Moonshot |
| qwen3.6-plus | qwen3.6-plus | 81 | 85 | 20 | Y | Alibaba |
| deepseek-v4-pro | deepseek-v4-pro | 80 | 80 | 26 | N | DeepSeek |
| MiniMax-M2.7 | MiniMax-M2.7 | 79 | 95 | 26 | N | MiniMax |
| mimo-v2.5 | mimo-v2.5 | 78 | 91 | 70 | Y | Xiaomi |
| mimo-v2-pro | mimo-v2-pro | 78 | 84 | 79 | N | Xiaomi |
| kimi-k2.5 | kimi-k2.5 | 78 | 85 | 39 | Y | Moonshot |

**Best Value (통합지수):**

| Model | 통합 | 가성비 | 가격 | Use Case |
|-------|------|--------|------|----------|
| deepseek-v4-flash | 76 | 100 | 100 | 성능+가격 최강 |
| mimo-v2.5 | 73 | 70 | 91 | 멀티모달 균형 |
| mimo-v2-omni | 70 | 60 | 91 | 멀티모달+빠른 응답 |
| qwen3.6-Flash-non | 74 | 70 | 94 | 가장 빠른 Qwen |

### Image Generation Models

| Model | Provider | API Endpoint | Price | Auth |
|-------|----------|-------------|-------|------|
| seedream-4-5-251128 | ByteDance | `ark.ap-southeast.bytepluses.com/api/v3/images/generations` | from $0.04/img | Bearer |
| z-image-turbo | Alibaba | `dashscope-intl.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation` | $0.015-0.03/img | Bearer |
| gemini-2.5-flash-image | Google | (via SDK) | included in Gemini API | API key |
| gpt-image-2 | OpenAI | `api.openai.com/v1/images/generations` | standard pricing | Bearer |

### Thinking Mode Control

Several providers support thinking on/off toggle:

| Model (thinking on) | Model (thinking off) | API model_id | Toggle parameter |
|---------------------|---------------------|-------------|-----------------|
| qwen3.6-Flash | qwen3.6-Flash-non | qwen3.6-flash | `extra_body={"enable_thinking": false}` |
| qwen3.6-Max | qwen3.6-Max-non | qwen3.6-max-preview | `extra_body={"enable_thinking": false}` |
| mimo-v2.5-pro | mimo-v2.5-pro-non | mimo-v2.5-pro | `extra_body={"thinking":{"type":"disabled"}}` |
| kimi-k2.6 | kimi-k2.6-non | kimi-k2.6 | `extra_body={"thinking":{"type":"disabled"}}` |
| kimi-k2.5 | kimi-k2.5-non | kimi-k2.5 | `extra_body={"thinking":{"type":"disabled"}}` |

## ModelRouter Architecture (Updated)

### 9 Feature Keys → Recommended Model Mapping

| Feature Key | Recommended Primary | Fallback | Rationale |
|-------------|-------------------|----------|-----------|
| TrendResearch | deepseek-v4-flash | qwen3.6-Flash-non | 최저가+고성능, 텍스트 전용 |
| ConceptChat | mimo-v2.5 | qwen3.6-Flash-non | 멀티모달, 빠른 응답, 1M ctx |
| UserSketchAnalysis | mimo-v2.5 | gemini-3-flash | 멀티모달 필수, 균형 가격 |
| ReferenceAnalysis | mimo-v2.5 | gemini-3-flash | 멀티모달 이미지 분석 |
| Abstraction | qwen3.6-Flash-non | deepseek-v4-flash | 빠른 분류, 저비용 |
| SketchPrompt | qwen3.6-Plus-Non | mimo-v2.5 | 프롬프트 품질 중시 |
| ImageGeneration | seedream-4-5-251128 | z-image-turbo → gemini → gpt-image-2 | SPEC-04 fallback chain |
| SpecWriting | kimi-k2.6 | qwen3.6-plus | 장문 생성, 추론 능력 |
| Verification | deepseek-v4-flash | qwen3.6-Flash-non | 빠른 평가, 저비용 |

### ModelRouter Dispatch Pattern

```python
class ModelRouter:
    async def dispatch(
        self,
        feature: FeatureKey,
        prompt: str | list[dict],
        context: dict | None = None,
        thinking: bool = True,
    ) -> ModelResult:
        policy = await self.get_active_policy(feature)
        model = policy.primary_model
        provider = self.providers[model.provider]

        try:
            result = await provider.call(model, prompt, context, thinking=thinking)
            await self.record_success(feature, model, result)
            return result
        except ProviderError:
            # Fallback chain
            for fallback in policy.fallback_models:
                result = await self.providers[fallback.provider].call(fallback, prompt, context)
                await self.record_fallback(feature, fallback, result)
                return result
            raise AllProvidersFailedError(feature)
```

## Current Config Pattern (Scattered)

```python
# app/core/config.py - direct env-based
IMAGE_GEN_PROVIDER=nano_banana
IMAGE_GENERATION_MODEL=gemini-2.5-flash-image
```

Each service reads settings directly → no central routing, no fallback, no cost tracking.

## Endpoints Summary (from .env)

| Provider | Base URL | Auth Method |
|----------|---------|-------------|
| Gemini | `generativelanguage.googleapis.com/v1beta` | `?key={API_KEY}` |
| DeepSeek | `api.deepseek.com` | `Authorization: Bearer {KEY}` |
| Alibaba (text) | `dashscope-intl.aliyuncs.com/compatible-mode/v1` | `Authorization: Bearer {KEY}` |
| Alibaba (image) | `dashscope-intl.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation` | `Authorization: Bearer {KEY}` |
| ByteDance | `ark.ap-southeast.bytepluses.com/api/v3` | `Authorization: Bearer {KEY}` |
| OpenAI | `api.openai.com/v1` | `Authorization: Bearer {KEY}` |
| Xiaomi MiMo | `api.xiaomimimo.com/v1` | `api-key: {KEY}` or `Bearer` |
| MiniMax | `api.minimax.io/v1` | `Authorization: Bearer {KEY}` |
| Kimi | `api.moonshot.ai/v1` | `Authorization: Bearer {KEY}` |

**Note:** Alibaba, Xiaomi, MiniMax, Kimi all use OpenAI-compatible API format. Can use `openai.OpenAI(base_url=..., api_key=...)` SDK directly.

## Key Gaps

| Gap | Severity | Description |
|-----|----------|-------------|
| No ModelRouter | CRITICAL | All services use direct model config |
| No model catalog | HIGH | No ModelProvider/ModelCatalog entities |
| No policy management | HIGH | No FeatureModelPolicy/PromptPolicy |
| No admin console | HIGH | Entirely new on port 14001 |
| No cost tracking | MEDIUM | No token/cost/failure metrics |
| No policy versioning | MEDIUM | No rollback capability |
| ~~Empty API keys~~ | ~~MEDIUM~~ | **CORRECTED: All keys configured** |

## Dependencies to Add

```
# All providers use OpenAI-compatible SDK except Gemini and ByteDance
# openai package already in requirements.txt - covers Alibaba, Xiaomi, MiniMax, Kimi, DeepSeek
# google-generativeai already in requirements.txt - covers Gemini
# ByteDance: use HTTP requests (requests/httpx) to Ark API
```
