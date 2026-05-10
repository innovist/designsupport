# API / Webhook Docs

인증: 모든 API 요청은 Django admin에서 미리 생성한 사용자 토큰을 `Authorization: Token <token>` 헤더로 전달해야 합니다.

# 서버 정보 및 인증
host: http://119.207.232.98:9123

auth token: f68bae5a893dab656229f290c700bcde82b3963f

## 1. 특정 여러 개 크롤러 시작
설명: 여러 source를 한 번에 받아 Celery 작업으로 크롤링을 시작합니다.

요청 구조
```json
POST /api/crawlers/start/
{
  "source": ["google", "duckduckgo"],
  "start_time": "2026-03-20T10:00:00+09:00",
  "end_time": "2026-03-20T11:00:00+09:00",
  "keyword": ["python", "django"],
  "limit": 10
}
```

응답 구조
```json
{
  "status": "success",
  "task_id": "1234567890"
}
```

## 2. 지원하는 source 목록 조회
설명: 현재 API에서 시작 가능한 `source` 목록을 조회합니다.

요청 구조
```json
GET /api/crawlers/sources/
```

응답 구조
```json
{
  "status": "success",
  "result": ["bing", "duckduckgo", "google", "yahoo"]
}
```

## 3. task_id로 크롤러 상태 조회
설명: Celery task 상태를 조회합니다.

요청 구조
```json
GET /api/crawlers/status/?task_id=1234567890
```

응답 구조
```json
{
  "status": "success",
  "task_id": "1234567890",
  "result": "started|success|failure|revoked" 
}
```

## 4. task_id로 크롤러 중지
설명: Celery task revoke를 호출해 작업 중지를 요청합니다.

요청 구조
```json
POST /api/crawlers/stop/
{
  "task_id": "1234567890"
}
```

응답 구조
```json
{
  "status": "success",
  "task_id": "1234567890",
  "result": "success"
}
```

## 5. 크롤링한 데이터 조회
설명: `task_id`가 있으면 해당 작업 데이터만, 없으면 인증 사용자 전체 데이터를 조회합니다.

요청 구조
```json
GET /api/crawlers/data/?task_id=1234567890&page=1&page_size=10
```

응답 구조
```json
{
  "status": "success",
  "task_id": "1234567890",
  "total_count": 100,
  "total_pages": 10,
  "result": [
    {
      "id": 1,
      "source": "google",
      "task_id": "1234567890",
      "title": "title",
      "url": "https://example.com",
      "description": "description",
      "created_at": "2026-03-20T10:00:00+09:00"
    }
  ]
}
```

## 6. Webhook
설명: Django Channels websocket endpoint입니다. 특정 `task_id`를 구독하면 크롤링 완료 데이터, 오류 메시지, task 종료 이벤트를 실시간 수신합니다.

요청 구조
```text
WS /webhook/<task_id>/
```

usage example:
```python
try:
      import websocket
  except ImportError as exc:
      raise ImportError(
          "webhook 연결을 보려면 `pip install websocket-client`가 필요합니다."
      ) from exc

  webhook_url = f"{WS_BASE_URL}/webhook/{task_id}/"
  ws = websocket.create_connection(
      webhook_url,
      header=[f"Authorization: Token {AUTH_TOKEN.strip()}"],
      timeout=30,
  )
  print(f"webhook connected: {webhook_url}")

  try:
      while True:
          message = ws.recv()
          try:
              payload = json.loads(message)
          except json.JSONDecodeError:
              print(message)
              continue

          print(json.dumps(payload, ensure_ascii=False, indent=2))
          result = payload.get("result")
          if isinstance(result, dict) and result.get("event") == "task_finished":
              print("task finished event received; waiting for socket close.")
              continue
  except Exception as exc:
      print(f"websocket closed or recv failed: {exc}")
  finally:
      done_event.set()
      try:
          ws.close()
      except Exception:
          pass

```

응답 구조: 크롤링 완료 데이터
```json
{
  "status": "success",
  "task_id": "1234567890",
  "result": {
    "id": 1,
    "source": "google",
    "task_id": "1234567890",
    "title": "title",
    "url": "https://example.com",
    "description": "description",
    "created_at": "2026-03-20T10:00:00+09:00"
  }
}
```

응답 구조: 오류 메시지
```json
{
  "status": "error",
  "task_id": "1234567890",
  "result": "error message"
}
```

응답 구조: task 종료 이벤트
```json
{
  "status": "success",
  "task_id": "1234567890",
  "result": {
    "event": "task_finished",
    "task_status": "success",
    "saved_count": 12
  }
}
```

`task_status` 값은 정상 종료 시 `success`, 중지 요청으로 종료된 경우 `revoked` 입니다.
