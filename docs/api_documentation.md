# Fashion AI Generator - API Documentation
**Version:** 1.0.0
**Base URL:** `https://api.fashion-ai.com`
**Documentation:** `https://api.fashion-ai.com/docs`

---

## 1. 개요

Fashion AI Generator는 AI 기반 패션 트렌드 분석 및 이미지 생성을 위한 RESTful API를 제공합니다. 모든 API 요청은 JSON 형식으로 처리되며, OAuth 2.0 기반 인증을 지원합니다.

### 1.1. 주요 기능
- **트렌드 분석**: 패션 트렌드 데이터 수집 및 AI 기반 분석
- **이미지 생성**: 텍스트/이미지 기반 패션 디자인 생성
- **패턴 생성**: 디자인을 실제 제작용 패턴 도면으로 변환
- **데이터 수집**: 다양한 패션 소스에서 데이터 크롤링

### 1.2. 인증
```http
Authorization: Bearer {access_token}
```

### 1.3. API 버전
- 현재 버전: v1
- URL 형식: `/api/v1/{resource}`

---

## 2. 공통 응답 형식

### 2.1. 성공 응답
```json
{
  "success": true,
  "data": {
    // 실제 데이터
  },
  "metadata": {
    "timestamp": "2025-12-21T12:00:00Z",
    "request_id": "req_123456789",
    "version": "1.0.0"
  }
}
```

### 2.2. 에러 응답
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input parameters",
    "details": {
      "field": "prompt",
      "reason": "Must be at least 10 characters"
    }
  },
  "metadata": {
    "timestamp": "2025-12-21T12:00:00Z",
    "request_id": "req_123456789"
  }
}
```

### 2.3. HTTP 상태 코드
| 코드 | 의미 | 설명 |
|------|------|------|
| 200 | OK | 요청 성공 |
| 201 | Created | 리소스 생성 성공 |
| 400 | Bad Request | 잘못된 요청 |
| 401 | Unauthorized | 인증 실패 |
| 403 | Forbidden | 권한 없음 |
| 404 | Not Found | 리소스 없음 |
| 429 | Too Many Requests | 요청 초과 |
| 500 | Internal Server Error | 서버 오류 |

---

## 3. 트렌드 분석 API

### 3.1. 트렌드 분석 시작
**POST** `/api/v1/analysis/analyze-trends`

패션 트렌드를 분석합니다.

#### 요청
```json
{
  "keywords": ["오버사이즈", "미니멀리즘"],
  "time_range": "7d",
  "sources": ["fashion_news", "instagram", "musinsa"],
  "options": {
    "include_sentiment": true,
    "include_visuals": true,
    "depth": "deep"
  }
}
```

#### 파라미터
| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| keywords | array[string] | O | 분석할 키워드 목록 (최대 10개) |
| time_range | string | X | 분석 기간 (1d, 7d, 30d) 기본값: 7d |
| sources | array[string] | X | 데이터 소스 (기본값: 모든 소스) |
| options | object | X | 추가 옵션 |

#### 응답
```json
{
  "success": true,
  "data": {
    "trend_id": "trend_123456",
    "keywords": ["오버사이즈", "미니멀리즘"],
    "analysis_period": {
      "start": "2025-12-14T00:00:00Z",
      "end": "2025-12-21T00:00:00Z"
    },
    "trend_score": 87.5,
    "growth_rate": 12.3,
    "sentiment": {
      "positive": 65,
      "neutral": 25,
      "negative": 10
    },
    "related_keywords": [
      {"keyword": "루즈핏", "score": 0.85},
      {"keyword": "편안한패션", "score": 0.72}
    ],
    "visual_trends": {
      "colors": ["black", "beige", "white"],
      "patterns": ["solid", "minimal"],
      "silhouettes": ["oversized", "relaxed"]
    },
    "insights": [
      "최근 7일간 오버사이즈 스타일 관련 게시물 23% 증가",
      "20-30대 여성층에서 가장 높은 반응률 기록"
    ]
  }
}
```

### 3.2. 이미지 분석
**POST** `/api/v1/analysis/analyze-image`

패션 이미지를 분석하여 스타일 정보를 추출합니다.

#### 요청 (multipart/form-data)
```
image: [파일]
options: {
  "extract_colors": true,
  "identify_garments": true,
  "style_classification": true
}
```

#### 응답
```json
{
  "success": true,
  "data": {
    "style_category": "casual",
    "color_palette": [
      {"color": "#000000", "name": "black", "ratio": 0.45},
      {"color": "#FFFFFF", "name": "white", "ratio": 0.30}
    ],
    "garments": [
      {"type": "t-shirt", "color": "black", "material": "cotton"},
      {"type": "jeans", "color": "blue", "material": "denim"}
    ],
    "overall_aesthetic": "minimalist casual",
    "similar_styles": ["streetwear", "athleisure"]
  }
}
```

---

## 4. 이미지 생성 API

### 4.1. 패션 디자인 생성
**POST** `/api/v1/generation/fashion-design`

텍스트 설명을 기반으로 패션 디자인 이미지를 생성합니다.

#### 요청
```json
{
  "prompt": "미니멀한 A라인 원피스, 흰색, 린넨 소재",
  "style": "modern",
  "garment_type": "dress",
  "color_scheme": ["white"],
  "fabric_type": "linen",
  "num_variations": 3,
  "width": 1024,
  "height": 1024,
  "quality": "high",
  "model_preference": "zimage",
  "reference_image_url": "https://example.com/ref.jpg"
}
```

#### 파라미터
| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| prompt | string | O | 디자인 설명 (최소 10자, 최대 500자) |
| style | string | X | 스타일 (modern, classic, avantgarde) |
| garment_type | string | X | 의류 타입 |
| num_variations | integer | X | 생성할 변형 수 (1-5) |
| quality | string | X | 품질 (standard, high, ultra) |

#### 응답
```json
{
  "success": true,
  "data": {
    "generation_id": "gen_123456",
    "images": [
      {
        "url": "https://cdn.fashion-ai.com/gen/123456_1.jpg",
        "base64": "data:image/jpeg;base64,...",
        "metadata": {
          "width": 1024,
          "height": 1024,
          "file_size": 245760
        }
      }
    ],
    "variations": [
      // 추가 변형 이미지들
    ],
    "model_used": "zimage",
    "generation_time": 45.2,
    "parameters_used": {
      "prompt_hash": "abc123",
      "seed": 456789
    }
  }
}
```

### 4.2. 컬렉션 생성
**POST** `/api/v1/generation/collection`

통합된 테마로 패션 컬렉션을 생성합니다.

#### 요청
```json
{
  "theme": "서머 비치웨어 2025",
  "garments": ["dress", "top", "bottom", "swimwear"],
  "style": "resort",
  "color_palette": ["aqua", "coral", "sand"],
  "num_sets": 5
}
```

#### 응답
```json
{
  "success": true,
  "data": {
    "collection_id": "col_123456",
    "theme": "서머 비치웨어 2025",
    "sets": [
      {
        "set_id": "set_001",
        "garments": [
          {
            "type": "dress",
            "images": ["url1", "url2"],
            "description": "플로럴 맥시 드레스"
          }
        ]
      }
    ]
  }
}
```

### 4.3. 기술적 스케치 생성
**POST** `/api/v1/generation/technical-sketch`

디자인을 기술적 도면으로 변환합니다.

#### 요청
```json
{
  "design_description": "심플한 셔츠 블라우스",
  "garment_type": "blouse",
  "include_measurements": true,
  "output_format": "line_drawing"
}
```

---

## 5. 패턴 생성 API

### 5.1. 패턴 블루프린트 생성
**POST** `/api/v1/blueprint/generate`

디자인을 실제 제작용 패턴으로 변환합니다.

#### 요청
```json
{
  "garment_type": "blouse",
  "design_description": "기본 셔츠 블라우스",
  "size_system": "KS",
  "size": "M",
  "measurements": {
    "bust": 84,
    "waist": 68,
    "hip": 92
  },
  "include_instructions": true,
  "include_seam_allowance": true,
  "seam_allowance_width": 1.5,
  "output_format": "image"
}
```

#### 응답
```json
{
  "success": true,
  "data": {
    "blueprint_id": "bp_123456",
    "pattern_pieces": [
      {
        "name": "Front_Bodice",
        "image": "data:image/png;base64,...",
        "width": 500,
        "height": 600,
        "piece_count": 1,
        "instructions": [
          "시접 1.5cm 추가",
          "다트 7cm 깊이로 마킹"
        ]
      },
      {
        "name": "Back_Bodice",
        "image": "data:image/png;base64,...",
        "width": 500,
        "height": 650,
        "piece_count": 1
      }
    ],
    "layout_diagram": "data:image/png;base64,...",
    "instructions": {
      "cutting": "1. 시접 포함하여 재단...",
      "sewing": "1. 어깨솔기缝合...",
      "finishing": "1. 가단자 처리..."
    },
    "material_requirements": {
      "fabric": "1.5m x 1.4m",
      "thread": "200m",
      "buttons": "7개 (直径 1.5cm)",
      "interfacing": "0.5m"
    }
  }
}
```

### 5.2. PDF 내보내기
**GET** `/api/v1/blueprint/export/{blueprint_id}`

생성된 패턴을 PDF로 다운로드합니다.

#### 응답
```json
{
  "success": true,
  "data": {
    "download_url": "https://cdn.fashion-ai.com/patterns/bp_123456.pdf",
    "expires_at": "2025-12-28T12:00:00Z"
  }
}
```

---

## 6. 데이터 수집 API

### 6.1. 크롤링 시작
**POST** `/api/v1/crawler/start`

패션 데이터 수집을 시작합니다.

#### 요청
```json
{
  "sources": ["fashion_news", "instagram", "musinsa"],
  "keywords": ["2025 S/S", "패션 트렌드"],
  "max_items": 500,
  "filters": {
    "date_range": {
      "start": "2025-12-01",
      "end": "2025-12-21"
    },
    "language": ["ko", "en"],
    "min_engagement": 100
  }
}
```

#### 응답
```json
{
  "success": true,
  "data": {
    "job_id": "job_123456",
    "status": "started",
    "estimated_duration": 1800,
    "sources_count": 3,
    "keywords_count": 2
  }
}
```

### 6.2. 크롤링 상태 조회
**GET** `/api/v1/crawler/status/{job_id}`

크롤링 작업 상태를 조회합니다.

#### 응답
```json
{
  "success": true,
  "data": {
    "job_id": "job_123456",
    "status": "running",
    "progress": {
      "total": 1000,
      "completed": 456,
      "percentage": 45.6
    },
    "sources": {
      "fashion_news": {"status": "completed", "items": 250},
      "instagram": {"status": "running", "items": 180},
      "musinsa": {"status": "pending", "items": 0}
    },
    "start_time": "2025-12-21T10:00:00Z",
    "estimated_completion": "2025-12-21T10:30:00Z"
  }
}
```

### 6.3. 크롤링 결과 조회
**GET** `/api/v1/crawler/results/{job_id}`

크롤링 결과 데이터를 조회합니다.

#### 쿼리 파라미터
- `page`: 페이지 번호 (기본값: 1)
- `limit`: 페이지 당 항목 수 (기본값: 50)
- `format`: 응답 형식 (json, csv)

#### 응답
```json
{
  "success": true,
  "data": {
    "job_id": "job_123456",
    "total_items": 892,
    "page": 1,
    "total_pages": 18,
    "items": [
      {
        "id": "item_001",
        "source": "instagram",
        "url": "https://instagram.com/p/123",
        "content": {
          "text": "2025년 봄 패션 트렌드...",
          "images": ["url1", "url2"],
          "hashtags": ["fashion", "trend2025"],
          "engagement": {
            "likes": 1523,
            "comments": 89,
            "shares": 45
          }
        },
        "metadata": {
          "author": "fashion_influencer",
          "publish_date": "2025-12-20T15:30:00Z",
          "language": "ko"
        }
      }
    ]
  }
}
```

---

## 7. 모델 정보 API

### 7.1. 이미지 생성 모델 목록
**GET** `/api/v1/models/image-generation`

사용 가능한 이미지 생성 모델 목록을 조회합니다.

#### 응답
```json
{
  "success": true,
  "data": {
    "models": [
      {
        "name": "zimage",
        "display_name": "Z-Image",
        "provider": "Z-AI Lab",
        "capabilities": [
          "fashion_design",
          "model_fitting",
          "upscale",
          "style_transfer"
        ],
        "supported_formats": ["jpeg", "png"],
        "max_resolution": "2048x2048",
        "pricing": {
          "standard": 0.01,
          "high": 0.02,
          "ultra": 0.05
        },
        "status": "available",
        "version": "2.1.0"
      }
    ]
  }
}
```

### 7.2. 텍스트 생성 모델 목록
**GET** `/api/v1/models/text-generation`

사용 가능한 텍스트 생성 모델 목록을 조회합니다.

#### 응답
```json
{
  "success": true,
  "data": {
    "models": [
      {
        "name": "gemini-2.5-flash",
        "display_name": "Gemini 2.5 Flash",
        "provider": "Google",
        "capabilities": [
          "text",
          "multimodal",
          "analysis",
          "translation"
        ],
        "max_tokens": 8192,
        "languages": ["ko", "en", "zh-CN", "zh-TW", "ja"],
        "pricing": {
          "input": 0.0001,
          "output": 0.0004
        }
      }
    ]
  }
}
```

---

## 8. WebSocket API (실시간 통신)

### 8.1. 생성 진행률 구독
**WS** `/ws/progress/{generation_id}`

이미지/패턴 생성 진행률을 실시간으로 수신합니다.

#### 메시지 형식
```json
{
  "type": "progress_update",
  "data": {
    "generation_id": "gen_123456",
    "status": "processing",
    "progress": 65,
    "stage": "optimizing_prompt",
    "estimated_remaining": 45,
    "preview_url": "https://cdn.fashion-ai.com/previews/123.jpg"
  }
}
```

---

## 9. 제한 사항

### 9.1. 요청 제한
- **분당 요청**: 100회
- **일일 요청**: 10,000회
- **동시 요청**: 10개
- **파일 업로드**: 최대 100MB

### 9.2. 생성 제한
- **일일 이미지 생성**: 1,000개
- **동시 생성**: 5개
- **최대 해상도**: 2048x2048
- **최대 비디오 길이**: 60초

### 9.3. 데이터 보관
- **생성 결과**: 30일
- **크롤링 데이터**: 90일
- **사용자 데이터**: 365일

---

## 10. 에러 코드

| 코드 | 의미 | 해결 방법 |
|------|------|----------|
| AUTH_001 | 잘못된 API 키 | 유효한 API 키 사용 |
| AUTH_002 | 만료된 토큰 | 토큰 갱신 |
| RATE_001 | 요청 초과 | 요청 간격 조정 |
| GEN_001 | 생성 실패 | 파라미터 확인 후 재시도 |
| GEN_002 | 모델 사용 불가 | 다른 모델 선택 |
| VAL_001 | 유효하지 않은 입력 | 입력값 검증 |
| SYS_001 | 시스템 오류 | 잠시 후 재시도 |

---

## 11. SDK 및 라이브러리

### 11.1. Python SDK
```python
pip install fashion-ai-sdk

from fashion_ai import FashionAIClient

client = FashionAIClient(api_key="your_key")

# 트렌드 분석
trends = client.analyze_trends(
    keywords=["오버사이즈"],
    time_range="7d"
)

# 이미지 생성
images = client.generate_design(
    prompt="미니멀 원피스",
    num_variations=3
)
```

### 11.2. JavaScript SDK
```javascript
npm install fashion-ai-js

import { FashionAI } from 'fashion-ai-js';

const client = new FashionAI('your_api_key');

// 패턴 생성
const pattern = await client.generatePattern({
  garment_type: 'dress',
  size: 'M'
});
```

### 11.3. cURL 예제
```bash
# 이미지 생성
curl -X POST https://api.fashion-ai.com/api/v1/generation/fashion-design \
  -H "Authorization: Bearer YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "미니멀한 블랙 드레스",
    "num_variations": 2
  }'
```

---

## 12. 지원 및 문의

- **기술 문서**: https://docs.fashion-ai.com
- **API 참조**: https://api.fashion-ai.com/docs
- **지원 이메일**: api-support@fashion-ai.com
- **상태 페이지**: https://status.fashion-ai.com
- **GitHub**: https://github.com/fashion-ai/api-sdk

---

## 13. 변경 로그

### v1.0.0 (2025-12-21)
- 초기 API 릴리스
- 트렌드 분석 API 추가
- 이미지 생성 API 추가
- 패턴 생성 API 추가
- 다국어 지원 (한국어, 영어, 중국어 간체/번체)
- WebSocket 실시간 통신 지원