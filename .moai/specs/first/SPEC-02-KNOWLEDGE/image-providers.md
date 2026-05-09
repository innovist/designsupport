# SPEC-02 Appendix: 이미지 검색 제공자 카탈로그 (Image Provider Catalog)

이 부록은 SPEC-02-KNOWLEDGE §3.5.1(이미지 검색 제공자 카탈로그)의 본문이며, 레퍼런스를 “대략적 시각 자극”으로만 사용한다는 사용자 의도를 정책으로 구현한다. 본 부록의 모든 표/절차는 SPEC-02 정식 일부이며 REQ-02-REF-009 ~ REQ-02-REF-017 / INV-02-05 / INV-02-06 / NFR-02-LIC-002 / NFR-02-PRIVACY-001 / NFR-02-PERF-003 / NFR-02-COMP-002의 본문 근거다.

핵심 원칙(요약):
- 레퍼런스는 “편집/복제 대상이 아니다”. 추상화 규칙 도출의 시각 자극일 뿐이며 고해상도가 필요 없다.
- 내부에 저장하는 이미지는 긴변 ≤ 1024px 썸네일·중간 해상도(WebP, 품질 80%)로만.
- 라이선스 메타가 없는 자료는 기본적으로 보수적 처리(`tier=3`, `license_risk=high`, `abstraction_only=true`).
- 제공자별 처리는 코드 if 분기가 아니라 어댑터 레지스트리 패턴(데이터 주도)으로.

---

## 1. Tier 분류 정책

| Tier | 정의 | license_risk | direct_style_apply | 내부 저장 | 비고 |
|---|---|---|---|---|---|
| 1 | 상업 무료/공개도메인이 명확하고 출처 attribution이 합법적인 제공자 | low | 가능(원본 보존형 생성에는 추상화 규칙 거쳐 사용) | 썸네일/중간해상도(≤1024px) WebP | UI에 attribution 표기 의무 |
| 2 | 라이선스 메타가 “건별로” 명시되며, CC 필터로 안전 자료를 추릴 수 있는 제공자 | medium | 추상화 우선(직접 스타일 적용은 제한) | 썸네일/중간해상도(≤1024px) | 라이선스 누락 항목은 자동으로 Tier 3으로 강등 |
| 3 | 라이선스 미상이거나 약관상 내부 캐싱이 위험한 자료 | high | **불변(false)** — INV-02-06 | **원본/리사이즈 미저장**, 외부 URL + 자체 생성 썸네일(저작권법상 인용 범위)만 보관 | 추상화 규칙 도출용 시각 자극으로만 사용 |

상태 전이:
- Tier 2의 항목 중 라이선스 메타 부재가 확인되면 자동으로 Tier 3으로 강등(REQ-02-REF-013).
- Tier 3에서 출처 사이트의 명시적 라이선스 변경이 확인되더라도 자동 승격은 없음. 관리자 검토(SPEC-04 콘솔)로만 승격 가능.

---

## 2. Tier 1 — 직접 사용 가능 제공자(11종)

| # | 제공자 | API 엔드포인트(베이스) | 라이선스(SPDX/명) | 도메인 적합도 | `.env` 키 | 어댑터 파일 |
|---|---|---|---|---|---|---|
| 1 | Unsplash | https://api.unsplash.com | Unsplash-License (상업 무료, 무재배포 의무는 없음 / attribution 권장) | 사진 일반(자연·제품·라이프스타일) | UNSPLASH_ACCESS_KEY (보조: UNSPLASH_ApplicationID, UNSPLASH_SECRET_KEY) | apps/references/infrastructure/image_search/unsplash.py |
| 2 | Pexels | https://api.pexels.com/v1 | Pexels-License (상업 무료) | 사진/비디오 일반 | PEXELS_API_KEY | apps/references/infrastructure/image_search/pexels.py |
| 3 | Pixabay | https://pixabay.com/api | Pixabay-Content-License | 사진/일러스트/벡터 | PIXABAY_API_KEY | apps/references/infrastructure/image_search/pixabay.py |
| 4 | Wikimedia Commons | https://commons.wikimedia.org/w/api.php | 항목별 CC0 / CC-BY / CC-BY-SA / Public-Domain (응답에서 추출) | 자연/건축/문화/역사/공예 | (불필요, User-Agent 식별 필요) | apps/references/infrastructure/image_search/wikimedia.py |
| 5 | Openverse | https://api.openverse.org/v1 | 항목별 CC 라이선스(메타 명시, 8억+ 통합) | 범용 | (불필요) | apps/references/infrastructure/image_search/openverse.py |
| 6 | Met Museum Open Access | https://collectionapi.metmuseum.org/public/collection/v1 | CC0-1.0 (오픈 액세스 항목) | 미술/공예/패션 아카이브 (Costume Institute) | (불필요) | apps/references/infrastructure/image_search/met.py |
| 7 | Smithsonian Open Access | https://api.si.edu/openaccess/api/v1.0 | CC0-1.0 (450만+ Open Access) | 자연사/예술/디자인 | (등록 후 발급, 환경변수 SMITHSONIAN_API_KEY로 신규 추가 권장) | apps/references/infrastructure/image_search/smithsonian.py |
| 8 | Europeana | https://api.europeana.eu/record/v2 | 항목별 라이선스 메타(주로 CC계열, public domain 다수) | 유럽 문화유산/디자인/패션 | (별도 발급, EUROPEANA_API_KEY로 추가 권장) | apps/references/infrastructure/image_search/europeana.py |
| 9 | Rijksmuseum | https://www.rijksmuseum.nl/api/en | CC0-1.0 (대부분 컬렉션) | 미술/장식예술/시각디자인 | (별도 발급, RIJKS_API_KEY로 추가 권장) | apps/references/infrastructure/image_search/rijks.py |
| 10 | NASA Images | https://images-api.nasa.gov | Public-Domain (NASA 정책) | 자연/우주/항공 | (불필요) | apps/references/infrastructure/image_search/nasa.py |
| 11 | KIPRIS (한국 특허/디자인) | http://plus.kipris.or.kr / OPI 서비스 | 정부공개(저작재산권 준수, 디자인등록 메타) | 산업디자인(국내 디자인등록·상표) | KIPRIS_API_KEY | apps/references/infrastructure/image_search/kipris.py |

추가 옵션(보조 — 동영상 썸네일):
- YouTube Data API v3: https://www.googleapis.com/youtube/v3 / `YOUTUBE_API_KEYS` 사용. 영상 “썸네일 URL 메타”만 수집(영상 본체 다운로드 금지). 패션 위크 리뷰·광고 캠페인 비주얼·트렌드 영상 시각 자극용. 어댑터 위치: `apps/references/infrastructure/image_search/youtube_thumbnail.py`. 라이선스는 영상별 상이하므로 기본 `tier=3`으로 분류한다(섬네일은 인용 범위에서만 표시).

---

## 3. Tier 2 — 라이선스 메타 검증 후 사용

| 제공자 | API/엔드포인트 | 처리 정책 | 어댑터 비고 |
|---|---|---|---|
| Flickr (CC search only) | https://www.flickr.com/services/api | 호출 시 `license` 파라미터를 “CC BY / CC BY-SA / CC0 / Public Domain”에 해당하는 ID 셋으로 강제. 그 외 결과는 응답에서 폐기. 메타에 라이선스명·작가·URL 포함 필수. | apps/references/infrastructure/image_search/flickr.py |
| Internet Archive | https://archive.org/advancedsearch.php | `licenseurl` 또는 컬렉션 메타로 PD/CC 필터. 라이선스 누락 결과는 폐기. | apps/references/infrastructure/image_search/internet_archive.py |
| 일반 웹 검색(SerpAPI / Bing Image Search / DuckDuckGo) | 외부 검색 API | 호출 파라미터에 `usage_rights=cc_publicdomain,cc_attribute,cc_sharealike,cc_noncommercial` 또는 동등 옵션을 강제. 라이선스 메타 없는 결과는 응답에서 폐기. NFR-02-COMP-002에 의해 정적분석 대상. | apps/references/infrastructure/image_search/web_search.py |

규칙:
- Tier 2 어댑터는 응답 단계에서 `license_id`가 비어 있으면 자동으로 결과를 버린다(거짓 라이선스 추정 금지).
- 결과로 살아남은 항목은 `tier=2`, `license_risk=medium`. 추상화 우선 정책 적용.

---

## 4. Tier 3 — 링크 전용, 추상화 강제

| 제공자 | 처리 방식 |
|---|---|
| Pinterest, Behance, Dribbble, ArtStation | 외부 검색이나 사용자 붙여넣기 URL을 통해 들어오는 카드. **썸네일 외부 URL 링크만 보관**, 내부 다운로드/캐시 금지. 자체 생성 미니썸네일(서버 측 ≤ 256px)은 “저작권법상 인용 범위” 한도에서만 허용. `tier=3`, `license_risk=high`, `abstraction_only=true` 자동 표시. UI에서 `direct_style_apply` 비활성. |
| 일반 웹 이미지(라이선스 미상) | `provider="web"`, `license_id=unknown`, NFR-02-LIC-001에 의해 보수적 처리. Tier 3과 동일 정책. |
| YouTube 썸네일(기본) | 위 표 1.11 “보조” 참조. 기본 tier 3로 두고, 도메인팩 정책으로 명시적 허용 시 Tier 2로 승격 검토. |

INV-02-06에 의해 Tier 3 항목은 어떤 단계(UI/API/생성)에서도 `direct_style_apply=true`가 될 수 없다. 추상화 규칙 도출 입력으로만 사용하며 SPEC-03 REQ-03-ABSTRACT-006이 직접 스타일 적용을 거부한다.

---

## 5. 어댑터 레지스트리 / 호출 모델 (NFR-02-LIC-002 데이터 주도)

코드에 제공자명을 if/else 분기로 두지 않는다. 대신 어댑터 레지스트리 패턴.

```text
apps/references/infrastructure/image_search/
├── __init__.py          # registry: provider_id -> Adapter class
├── base.py              # ImageSearchAdapter 추상 클래스 (Port 구현)
├── unsplash.py
├── pexels.py
├── pixabay.py
├── wikimedia.py
├── openverse.py
├── met.py
├── smithsonian.py
├── europeana.py
├── rijks.py
├── nasa.py
├── kipris.py
├── flickr.py            # Tier 2
├── internet_archive.py  # Tier 2
├── web_search.py        # Tier 2 (SerpAPI/Bing/DDG, usage_rights 강제)
└── youtube_thumbnail.py # 보조
```

레지스트리 구조(개념):

```
Registry = {
  "unsplash": {adapter_class, tier: 1, env_keys: ["UNSPLASH_ACCESS_KEY"], default_license: "Unsplash-License"},
  "pexels":   {adapter_class, tier: 1, env_keys: ["PEXELS_API_KEY"],     default_license: "Pexels-License"},
  "pixabay":  {adapter_class, tier: 1, env_keys: ["PIXABAY_API_KEY"],    default_license: "Pixabay-Content-License"},
  "wikimedia":{adapter_class, tier: 1, env_keys: [],                     default_license: "(per-item)"},
  "openverse":{adapter_class, tier: 1, env_keys: [],                     default_license: "(per-item CC)"},
  "met":      {adapter_class, tier: 1, env_keys: [],                     default_license: "CC0-1.0"},
  "smithsonian":{adapter_class, tier: 1, env_keys: ["SMITHSONIAN_API_KEY"], default_license: "CC0-1.0"},
  "europeana":  {adapter_class, tier: 1, env_keys: ["EUROPEANA_API_KEY"],   default_license: "(per-item)"},
  "rijks":      {adapter_class, tier: 1, env_keys: ["RIJKS_API_KEY"],       default_license: "CC0-1.0"},
  "nasa":       {adapter_class, tier: 1, env_keys: [],                       default_license: "Public-Domain"},
  "kipris":     {adapter_class, tier: 1, env_keys: ["KIPRIS_API_KEY"],       default_license: "KR-Government-Open"},
  "flickr":     {adapter_class, tier: 2, env_keys: ["FLICKR_API_KEY"],       default_license: "(CC-filtered)"},
  "internet_archive":{adapter_class, tier: 2, env_keys: [],                  default_license: "(per-item PD/CC)"},
  "web_search":     {adapter_class, tier: 2, env_keys: ["SERPAPI_KEY|BING_SEARCH_KEY"], default_license: "(usage_rights filter)"},
  "youtube_thumbnail":{adapter_class, tier: 3 (기본), env_keys: ["YOUTUBE_API_KEYS"], default_license: "(video-specific)"}
}
```

도메인팩이 “시드 제공자”를 지정하면 본 레지스트리의 `provider_id`로만 참조한다(REQ-02-REF-014).

---

## 6. 도메인별 시드 제공자 (REQ-02-REF-014)

| 도메인 | 우선 제공자(시드) | 보조 제공자 |
|---|---|---|
| industrial | kipris, smithsonian, met, wikimedia, unsplash, pexels | europeana, openverse |
| fashion | met (Costume Institute), europeana, rijks, unsplash, pexels | youtube_thumbnail (Tier 3, 패션 위크 리뷰 시각 자극용) |
| visual | rijks, met, openverse, unsplash, pexels, pixabay | wikimedia, internet_archive |
| advertising | unsplash, pexels, pixabay, openverse | youtube_thumbnail (Tier 3, 광고 캠페인 비주얼 시각 자극용) |

이 매핑은 코드가 아니라 `domain_packs/<domain>/manifest.yaml`의 `image_search.seed_providers` 항목으로 표현된다. 추가/변경은 도메인팩 데이터 수정만으로 반영된다.

---

## 7. 응답 정규화 스키마 (모든 어댑터 공통 출력)

각 어댑터는 다음 스키마로 정규화된 결과 리스트를 반환한다. 정규화는 어댑터의 책임이며, application 레이어는 “정규화된 카드”만 본다.

```text
NormalizedReferenceCard {
  provider: str,                  # registry key
  tier: int,                      # 1 | 2 | 3
  external_url: str,              # 원본 페이지 URL (attribution 표기용)
  source_url: str,                # 이미지 직접 URL (Tier 1/2: 다운로드 대상, Tier 3: 표시 전용)
  thumbnail_url: str,             # 제공자 썸네일 URL
  title: str | None,
  author: str | None,
  license_id: str | "unknown",    # SPDX 또는 제공자 라이선스명. 미상이면 "unknown"
  attribution_text: str,          # "Photo by {author} on {provider}" 등 표준 문구
  license_url: str | None,
  domain_tags: [str],
  published_at: ISO-8601 | None,
  collected_at: ISO-8601,         # 본 시스템 수집 시각
  raw_meta: object                # 어댑터별 원형 메타 (디버깅·재처리용)
}
```

application 레이어는 정규화된 카드를 받아서 다음을 수행:
1. `license_id == "unknown"` → `tier=3`, `license_risk=high`, `abstraction_only=true` 강제(REQ-02-REF-013).
2. tier에 따라 내부 저장 정책 적용(§8).
3. attribution 메타를 `ReferenceAsset`에 저장(REQ-02-REF-012, REQ-02-REF-017).

---

## 8. 내부 저장·썸네일 정책 (REQ-02-REF-010, REQ-02-REF-011, INV-02-05)

| Tier | 다운로드 대상 | 변환 | 저장 형식 | 보존 기간 |
|---|---|---|---|---|
| 1 | `thumbnail_url` 또는 `source_url` 중 ≤ 1024px 변형 우선 | 긴변 1024px 리사이즈 + WebP 80% 압축 + EXIF 제거(NFR-02-PRIVACY-001) | `assets/refs/<sha256>.webp` (객체 스토리지 14030) | 운영 정책에 따름 |
| 2 | 동일(라이선스 검증 통과 항목만) | 동일 | 동일 | 동일 |
| 3 | **다운로드 금지**. 자체 생성 미니썸네일(서버 측 ≤ 256px, 인용 범위) 또는 외부 URL만 | 미니썸네일은 ≤ 256px WebP 70% | 미니썸네일이 있을 경우만 `assets/refs/_mini/<sha256>.webp` | 짧게(예: 30일) 갱신 |

원본 고해상도 다운로드는 모든 Tier에서 금지(INV-02-05). “원본 보존형 생성(SPEC-03 refinement)”은 사용자 스케치(`UserSketchAsset`)에만 적용되며 외부 레퍼런스에는 적용되지 않는다.

---

## 9. Rate Limit / Quota 관리 (REQ-02-REF-016)

`ImageProviderQuota(provider, daily_limit, used_today, reset_at, active, last_error_at)` 테이블로 관리한다. 정책:

- 호출 전 `provider`의 `used_today < daily_limit` 확인. 초과 시 같은 Tier의 다른 제공자로 라운드로빈(예: unsplash 한도 도달 → pexels → pixabay → openverse 순).
- 일일 리셋은 제공자 약관에 맞춰 UTC 또는 KST 기준으로 `reset_at` 갱신.
- HTTP 429 응답 시 `last_error_at` 기록 + 백오프(지수 백오프, 최대 3회) 후 다음 후보로 전환.
- 모든 제공자 한도 도달 → `insufficient_evidence`(REQ-02-INDEX-004) 동급의 “검색 한도 초과” 응답을 반환하고 거짓 결과로 메우지 않는다.

기본 일일 한도(보수적 기본값 — 실제 약관 변경 시 관리자 콘솔에서 갱신):

| 제공자 | 기본 daily_limit |
|---|---|
| unsplash | 5,000 (Production 키 기준; Demo는 50) |
| pexels | 20,000 (시간당 200 → 일 환산 보수치) |
| pixabay | 5,000 |
| wikimedia / openverse / nasa / met / smithsonian / europeana / rijks | 사실상 무제한이지만 1,000 (예의 한도) |
| kipris | 10,000 (한국 OPI 정책 기준 보수) |
| flickr | 3,600 (시간당 기본 한도 환산) |
| internet_archive | 1,000 |
| web_search (SerpAPI/Bing/DDG) | 키별 약관에 따라 운영 |
| youtube_thumbnail | 10,000 단위 quota 단위(YouTube Data API 일일 quota) |

값은 모두 `ImageProviderQuota`에 저장되어 코드 변경 없이 조정 가능.

---

## 10. UI Attribution 노출 (REQ-02-REF-017, SPEC-05 연계)

UI(SPEC-05) `ReferenceCard` 렌더링 시 다음 attribution을 항상 표기:
- 작가(author)
- 제공자(provider)
- 라이선스명(license_id)
- 출처 페이지 링크(external_url, 새 창)

문구 표준(예시):
- Unsplash: "Photo by {author} on Unsplash" + license link
- Pexels: "Photo by {author} on Pexels"
- Pixabay: "Image from Pixabay (Pixabay Content License)"
- Wikimedia: "{file_title} — {author or institution}, via Wikimedia Commons (CC BY-SA 4.0)" 등 항목별 라이선스명에 따라 자동
- Met / Smithsonian / Rijks / NASA: "{title}, {institution}, CC0/Public Domain"
- KIPRIS: "{디자인등록번호}, KIPRIS"
- YouTube 썸네일: "Thumbnail © {channel}, YouTube" + Tier 3 워터마크

---

## 11. 보안·법적 가드 (NFR-02-PRIVACY-001 / NFR-02-COMP-002)

- 외부 이미지 다운로드 시 EXIF의 GPS/카메라ID/저자메타를 저장 전 제거(NFR-02-PRIVACY-001). 원본 EXIF가 필요한 분석은 일시 메모리 처리만, 파일에 남기지 않는다.
- SerpAPI/Bing/Google CSE/DuckDuckGo 호출은 어댑터에서 `usage_rights=cc_*` 옵션 강제. 어댑터 외 경로로 이 API들을 호출하는 코드(파일 grep 정적 분석)는 CI에서 거부(NFR-02-COMP-002).
- 모든 외부 호출은 SPEC-01 SSRF allowlist를 통과(NFR-02-SEC-001).
- robots.txt/사이트별 약관 확인(REQ-02-CRAWL-005)은 본 부록의 어댑터에도 적용된다.

---

## 12. CI 정적 분석 룰 (요약)

- 금지: 어댑터 디렉토리 외부에서 `pixabay.com`, `api.pexels.com`, `api.unsplash.com`, `serpapi.com`, `api.bing.microsoft.com` 등 외부 도메인 직접 호출.
- 금지: 어댑터 외 코드에 `provider == "unsplash"`처럼 제공자명을 if/else로 분기.
- 금지: `usage_rights` 옵션 없이 외부 검색 API 호출.
- 금지: 외부 이미지 PIL/Image.open 결과를 1024px 초과 해상도로 영속 저장(`save()`)하는 코드 경로.
- 위반 시 빌드 실패. 룰은 `tools/ci_checks/`에 위치(SPEC-01 §6.5/structure.md §1).

---

부록 종료. spec.md의 §3.5(REQ-02-REF-009 ~ 017), §5.1(엔티티), §6.1(라이브러리), §7(NFR), §8(INV), §10(.env 매핑) 절은 본 부록을 명시 참조한다.
