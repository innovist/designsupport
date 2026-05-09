# Fashion AI Generator - 배포 매뉴얼
**Version:** 1.0.0
**Last Updated:** 2025-12-21

---

## 1. 배포 개요

본 문서는 Fashion AI Generator 시스템을 프로덕션 환경에 배포하기 위한 전체 과정을 상세히 설명합니다.

### 1.1. 배포 대상
- 개발 환경 (Development)
- 스테이징 환경 (Staging)
- 프로덕션 환경 (Production)

### 1.2. 사전 요구사항
- Docker 및 Docker Compose 설치
- Git 설치 및 설정
- 도메인 및 SSL 인증서 준비
- API 키 및 환경 변수 준비

---

## 2. 인프라 준비

### 2.1. 서버 사양

#### 최소 사양
| 컴포넌트 | CPU | 메모리 | 스토리지 | 네트워크 |
|---------|-----|--------|----------|----------|
| Application Server | 4코어 | 8GB | 100GB SSD | 100Mbps |
| Database Server | 4코어 | 16GB | 500GB SSD | 100Mbps |
| Load Balancer | 2코어 | 4GB | 50GB SSD | 1Gbps |

#### 권장 사양
| 컴포넌트 | CPU | 메모리 | 스토리지 | 네트워크 |
|---------|-----|--------|----------|----------|
| Application Server | 8코어 | 16GB | 200GB SSD | 1Gbps |
| Database Server | 8코어 | 32GB | 1TB SSD | 1Gbps |
| Load Balancer | 4코어 | 8GB | 100GB SSD | 10Gbps |

### 2.2. 운영체제 요구사항
- **OS**: Ubuntu 22.04 LTS 또는 CentOS 8 이상
- **Docker**: 20.10 이상
- **Docker Compose**: 2.0 이상
- **Python**: 3.10 이상 (컨테이너 내부)

### 2.3. 네트워크 설정
- **외부 포트**: 80 (HTTP), 443 (HTTPS)
- **내부 포트**: 8000 (Application), 5432 (DB), 6379 (Redis)
- **방화벽**: 필요한 포트만 개방

---

## 3. 설치 절차

### 3.1. Docker 설치

#### Ubuntu 22.04
```bash
# Docker 설치
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Docker 그룹에 사용자 추가
sudo usermod -aG docker $USER

# Docker Compose 설치
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 서비스 시작 및 자동 실행 설정
sudo systemctl start docker
sudo systemctl enable docker
```

### 3.2. 소스 코드 배포

```bash
# Git 클론
git clone https://github.com/your-org/fashion-ai-generator.git
cd fashion-ai-generator

# 프로덕션 브랜치로 전환
git checkout main
git pull origin main
```

### 3.3. 환경 설정

```bash
# .env 파일 생성
cp .env.example .env

# .env 파일 편집
nano .env
```

#### .env 설정 예시
```env
# 데이터베이스 설정
DATABASE_URL=postgresql://postgres:your_password@db:5432/fashion_ai
DB_HOST=db
DB_PORT=5432
DB_NAME=fashion_ai
DB_USER=postgres
DB_PASSWORD=your_secure_password

# Redis 설정
REDIS_URL=redis://redis:6379/0
REDIS_HOST=redis
REDIS_PORT=6379

# API Keys
GEMINI_API_KEY=your_gemini_api_key
GLM_API_KEY=your_glm_api_key
Z_IMAGE_API_KEY=your_zimage_api_key
SEEDREAM_API_KEY=your_seedream_api_key
NANO_BANANA_API_KEY=your_nano_banana_api_key

# 애플리케이션 설정
SECRET_KEY=your_very_secure_secret_key_here
ENVIRONMENT=production
DEBUG=false
HOST=0.0.0.0
PORT=8000

# SSL 설정
SSL_CERT_PATH=/etc/nginx/ssl/cert.pem
SSL_KEY_PATH=/etc/nginx/ssl/key.pem

# 기타 설정
DEFAULT_LANGUAGE=ko
DEFAULT_SIZE_STANDARD=KS
MAX_CRAWL_PAGES=100
ALLOWED_HOSTS=fashion-ai.com,www.fashion-ai.com
```

---

## 4. SSL 인증서 설정

### 4.1. Let's Encrypt 사용

```bash
# Certbot 설치
sudo apt update
sudo apt install certbot python3-certbot-nginx

# 도메인 인증서 발급
sudo certbot --nginx -d fashion-ai.com -d www.fashion-ai.com

# 자동 갱신 설정
sudo crontab -e
# 다음 라인 추가
0 12 * * * /usr/bin/certbot renew --quiet
```

### 4.2. 기존 인증서 사용

```bash
# SSL 디렉토리 생성
mkdir -p nginx/ssl

# 인증서 복사
cp /path/to/cert.pem nginx/ssl/
cp /path/to/key.pem nginx/ssl/

# 권한 설정
chmod 600 nginx/ssl/key.pem
chmod 644 nginx/ssl/cert.pem
```

---

## 5. 데이터베이스 설정

### 5.1. PostgreSQL 초기화

```bash
# Docker Compose로 데이터베이스 시작
docker-compose up -d db redis

# 데이터베이스 초기화 스크립트 실행
docker-compose exec db psql -U postgres -d fashion_ai -f /docker-entrypoint-initdb.d/init.sql

# 마이그레이션 실행
docker-compose exec web alembic upgrade head
```

### 5.2. 데이터베이스 백업 설정

```bash
# 백업 스크립트 생성
sudo nano /usr/local/bin/backup_fashion_ai.sh
```

```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup/postgresql"
CONTAINER_NAME="fashion_ai_db"

# 백업 디렉토리 생성
mkdir -p $BACKUP_DIR

# 데이터베이스 백업
docker exec $CONTAINER_NAME pg_dump -U postgres fashion_ai > $BACKUP_DIR/fashion_ai_$DATE.sql

# 7일 이전 백업 삭제
find $BACKUP_DIR -name "fashion_ai_*.sql" -mtime +7 -delete
```

```bash
# 실행 권한 부여 및 crontab 등록
sudo chmod +x /usr/local/bin/backup_fashion_ai.sh
sudo crontab -e
# 매일 새벽 2시 백업
0 2 * * * /usr/local/bin/backup_fashion_ai.sh
```

---

## 6. 애플리케이션 배포

### 6.1. 빌드 및 시작

```bash
# 이미지 빌드
docker-compose build --no-cache

# 서비스 시작
docker-compose up -d

# 상태 확인
docker-compose ps
```

### 6.2. 로그 확인

```bash
# 모든 서비스 로그 확인
docker-compose logs -f

# 특정 서비스 로그 확인
docker-compose logs -f web
docker-compose logs -f db
```

### 6.3. 헬스 체크

```bash
# API 헬스 체크
curl http://localhost:8000/health

# 데이터베이스 연결 확인
docker-compose exec web python -c "from app.core.database import engine; print(engine.execute('SELECT 1').scalar())"

# Redis 연결 확인
docker-compose exec redis redis-cli ping
```

---

## 7. Nginx 설정

### 7.1. 프로덕션 Nginx 설정

```nginx
# /nginx/nginx.prod.conf
events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # 로그 형식
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;
    error_log /var/log/nginx/error.log warn;

    # Gzip 압축
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css application/json application/javascript;

    # Rate Limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;

    # Upstream
    upstream fashion_ai_backend {
        server web:8000;
        keepalive 32;
    }

    # HTTPS Server
    server {
        listen 443 ssl http2;
        server_name fashion-ai.com www.fashion-ai.com;

        # SSL 설정
        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES256-GCM-SHA384;
        ssl_prefer_server_ciphers off;

        # 보안 헤더
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";

        # API 라우트
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://fashion_ai_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_connect_timeout 30s;
            proxy_send_timeout 30s;
            proxy_read_timeout 30s;
        }

        # 정적 파일
        location /static/ {
            alias /var/www/static/;
            expires 1y;
            add_header Cache-Control "public, immutable";
        }

        # 메인 애플리케이션
        location / {
            proxy_pass http://fashion_ai_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # 파일 업로드 제한
        client_max_body_size 100M;
    }

    # HTTP to HTTPS 리다이렉트
    server {
        listen 80;
        server_name fashion-ai.com www.fashion-ai.com;
        return 301 https://$server_name$request_uri;
    }
}
```

### 7.2. Nginx 재시작

```bash
# 설정 테스트
docker-compose exec nginx nginx -t

# 재시작
docker-compose restart nginx
```

---

## 8. 모니터링 설정

### 8.1. Prometheus & Grafana

```bash
# 모니터링 스택 시작
docker-compose -f docker-compose.monitoring.yml up -d

# Grafana 접속
# URL: http://your-server:3000
# ID: admin
# PW: admin (최초 로그인 후 변경)
```

### 8.2. ELK Stack

```bash
# 로그 수집 스택 시작
docker-compose -f docker-compose.logging.yml up -d

# Kibana 접속
# URL: http://your-server:5601
```

---

## 9. CI/CD 설정

### 9.1. GitHub Actions 워크플로우

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov
      - name: Run tests
        run: pytest tests/ --cov=app

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to server
        uses: appleboy/ssh-action@v0.1.5
        with:
          host: ${{ secrets.HOST }}
          username: ${{ secrets.USERNAME }}
          key: ${{ secrets.SSH_KEY }}
          script: |
            cd /opt/fashion-ai-generator
            git pull origin main
            docker-compose build
            docker-compose up -d
            docker system prune -f
```

### 9.2. Secrets 설정

GitHub 리포지토리 Settings > Secrets and variables > Actions에 다음 항목 추가:

- `HOST`: 배포 서버 IP 또는 도메인
- `USERNAME`: 서버 접속 사용자명
- `SSH_KEY`: 서버 접속용 SSH 개인키

---

## 10. 롤백 절차

### 10.1. 빠른 롤백

```bash
# 이전 버전으로 되돌리기
git checkout <previous_tag>
docker-compose build
docker-compose up -d
```

### 10.2. 데이터베이스 롤백

```bash
# 백업에서 복원
docker-compose exec db psql -U postgres -d fashion_ai < /backup/postgresql/fashion_ai_backup.sql

# 마이그레이션 롤백
docker-compose exec web alembic downgrade -1
```

---

## 11. 성능 튜닝

### 11.1. 데이터베이스 튜닝

```sql
-- postgresql.conf 설정 예시
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
```

### 11.2. Nginx 튜닝

```nginx
# nginx.conf 튜닝
worker_processes auto;
worker_connections 2048;

# keepalive 활성화
keepalive_timeout 65;
keepalive_requests 100;

# 버퍼 크기 조정
client_body_buffer_size 128k;
client_max_body_size 100m;
client_header_buffer_size 1k;
large_client_header_buffers 4 4k;
```

---

## 12. 보안 강화

### 12.1. 방화벽 설정

```bash
# UFW 설정
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw deny 5432  # DB 외부 접속 차단
sudo ufw deny 6379  # Redis 외부 접속 차단
```

### 12.2. Fail2ban 설정

```bash
# Fail2ban 설치
sudo apt install fail2ban

# Nginx 보안 규칙 추가
sudo nano /etc/fail2ban/jail.local
```

```ini
[nginx-http-auth]
enabled = true
filter = nginx-http-auth
port = http,https
logpath = /var/log/nginx/error.log

[nginx-limit-req]
enabled = true
filter = nginx-limit-req
port = http,https
logpath = /var/log/nginx/error.log
maxretry = 10
findtime = 600
bantime = 7200
```

---

## 13. 문제 해결

### 13.1. 일반적인 문제

#### 문제: 컨테이너가 시작되지 않음
```bash
# 로그 확인
docker-compose logs <service_name>

# 컨테이너 상세 정보 확인
docker inspect <container_name>
```

#### 문제: 데이터베이스 연결 오류
```bash
# DB 상태 확인
docker-compose exec db pg_isready

# 연결 테스트
docker-compose exec web python -c "
import psycopg2
try:
    conn = psycopg2.connect('postgresql://postgres:password@db:5432/fashion_ai')
    print('Connection successful')
except Exception as e:
    print(f'Error: {e}')
"
```

#### 문제: 502 Bad Gateway
```bash
# Nginx 재시작
docker-compose restart nginx

# 웹 서비스 상태 확인
docker-compose ps web
```

### 13.2. 성능 문제

#### 문제: 응답 시간이 느림
```bash
# 리소스 사용량 확인
docker stats

# DB 쿼리 모니터링
docker-compose exec db psql -U postgres -d fashion_ai -c "
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
ORDER BY total_time DESC
LIMIT 10;"
```

---

## 14. 배포 체크리스트

### 14.1. 사전 점검
- [ ] 서버 사양 충족 여부 확인
- [ ] Docker 및 Docker Compose 설치 확인
- [ ] 도메인 및 SSL 인증서 준비
- [ ] API 키 및 환경 변수 준비
- [ ] 방화벽 설정 완료
- [ ] 백업 전략 수립

### 14.2. 배포 후 점검
- [ ] 모든 서비스 정상 시작 확인
- [ ] 헬스 체크 통과 확인
- [ ] SSL 인증서 정상 적용 확인
- [ ] API 기능 테스트 완료
- [ ] 모니터링 대시보드 설정 확인
- [ ] 로그 수집 정상 확인
- [ ] 백업 스크립트 실행 테스트

### 14.3. 운영 준비
- [ ] 문서 업데이트 완료
- [ ] 팀원 교육 완료
- [ ] 알림 설정 완료
- [ ] 장애 대응 절차 확립
- [ ] 사용자 안내 공지 준비

---

## 15. 연락처

- **개발팀**: dev-team@fashion-ai.com
- **운영팀**: ops-team@fashion-ai.com
- **긴급 연락**: +82-10-XXXX-XXXX (24/7)

---

*본 매뉴얼은 시스템 변경사항에 따라 지속적으로 업데이트됩니다.*