# Design Support System - 배포 매뉴얼
**Version:** 2.0.0
**Last Updated:** 2026-05-07

---

## 1. 배포 개요

본 문서는 Design Support System을 프로덕션 환경에 배포하기 위한 전체 과정을 설명합니다. 근거 기반 디자인 창작 지원 플랫폼으로, Django + PostgreSQL 기반 SaaS 서비스입니다.

### 1.1. 배포 대상
- 개발 환경 (Development)
- 스테이징 환경 (Staging)
- 프로덕션 환경 (Production)

### 1.2. 사전 요구사항
- Docker 및 Docker Compose 설치
- Git 설치 및 설정
- 도메인 및 SSL 인증서 준비
- AI Provider API 키 준비

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
- **Python**: 3.13 이상 (컨테이너 내부)

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
git clone https://github.com/your-org/design-support.git
cd design-support

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
# Django 설정
DJANGO_SETTINGS_MODULE=config.settings.production
SECRET_KEY=your_very_secure_secret_key_here
DEBUG=false
ALLOWED_HOSTS=design-support.com,www.design-support.com

# 데이터베이스 설정
DATABASE_URL=postgresql://postgres:your_password@db:5432/design_support
DB_HOST=db
DB_PORT=5432
DB_NAME=design_support
DB_USER=postgres
DB_PASSWORD=your_secure_password

# Redis 설정
REDIS_URL=redis://redis:6379/0

# AI Provider API Keys
GEMINI_API_KEY=your_gemini_api_key
GLM_API_KEY=your_glm_api_key
OPENAI_API_KEY=your_openai_api_key

# 파일 저장소
MEDIA_ROOT=/var/www/media
STATIC_ROOT=/var/www/static

# SSL 설정
SSL_CERT_PATH=/etc/nginx/ssl/cert.pem
SSL_KEY_PATH=/etc/nginx/ssl/key.pem
```

---

## 4. SSL 인증서 설정

### 4.1. Let's Encrypt 사용

```bash
# Certbot 설치
sudo apt update
sudo apt install certbot python3-certbot-nginx

# 도메인 인증서 발급
sudo certbot --nginx -d design-support.com -d www.design-support.com

# 자동 갱신 설정
sudo crontab -e
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

# Django 마이그레이션 실행
docker-compose exec web python manage.py migrate

# 관리자 계정 생성
docker-compose exec web python manage.py createsuperuser

# 기본 모델 카탈로그 로드 (필요 시)
docker-compose exec web python manage.py loaddata model_catalog.json
```

### 5.2. 데이터베이스 백업 설정

```bash
# 백업 스크립트 생성
sudo nano /usr/local/bin/backup_design_support.sh
```

```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup/postgresql"
CONTAINER_NAME="design_support_db"

# 백업 디렉토리 생성
mkdir -p $BACKUP_DIR

# 데이터베이스 백업
docker exec $CONTAINER_NAME pg_dump -U postgres design_support > $BACKUP_DIR/design_support_$DATE.sql

# 7일 이전 백업 삭제
find $BACKUP_DIR -name "design_support_*.sql" -mtime +7 -delete
```

```bash
# 실행 권한 부여 및 crontab 등록
sudo chmod +x /usr/local/bin/backup_design_support.sh
sudo crontab -e
# 매일 새벽 2시 백업
0 2 * * * /usr/local/bin/backup_design_support.sh
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
# Django 헬스 체크
curl http://localhost:8000/health/

# 데이터베이스 연결 확인
docker-compose exec web python manage.py check --database default

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

    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;
    error_log /var/log/nginx/error.log warn;

    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css application/json application/javascript;

    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;

    upstream design_support_backend {
        server web:8000;
        keepalive 32;
    }

    # HTTPS Server
    server {
        listen 443 ssl http2;
        server_name design-support.com www.design-support.com;

        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_prefer_server_ciphers off;

        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";

        # API 라우트
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://design_support_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # 정적 파일
        location /static/ {
            alias /var/www/static/;
            expires 1y;
            add_header Cache-Control "public, immutable";
        }

        # 미디어 파일
        location /media/ {
            alias /var/www/media/;
            expires 30d;
        }

        # 메인 애플리케이션
        location / {
            proxy_pass http://design_support_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        client_max_body_size 100M;
    }

    # HTTP to HTTPS 리다이렉트
    server {
        listen 80;
        server_name design-support.com www.design-support.com;
        return 301 https://$server_name$request_uri;
    }
}
```

---

## 8. 관리자 초기 설정

배포 후 관리자 콘솔에서 다음을 설정합니다.

### 8.1. 트렌드 지식 시스템
- Trend Source 등록 (Vogue Business, Core77, Dezeen 등)
- 도메인별 수집 주기 설정
- 트렌드 분류 관리

### 8.2. AI 모델 카탈로그
- Model Provider 등록 (Gemini, GLM, OpenAI 등)
- 기능별 모델 정책 설정
- Fallback 정책 구성

### 8.3. 테넌트 및 워크스페이스
- 초기 테넌트 생성
- 관리자 계정 설정
- 권한 정책 구성

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
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.13'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-django pytest-cov ruff
      - name: Lint
        run: ruff check .
      - name: Run tests
        run: pytest tests/ --cov=apps --cov-report=term-missing

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to server
        uses: appleboy/ssh-action@v1.0.3
        with:
          host: ${{ secrets.HOST }}
          username: ${{ secrets.USERNAME }}
          key: ${{ secrets.SSH_KEY }}
          script: |
            cd /opt/design-support
            git pull origin main
            docker-compose build
            docker-compose exec web python manage.py migrate --noinput
            docker-compose exec web python manage.py collectstatic --noinput
            docker-compose up -d
            docker system prune -f
```

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
docker-compose exec db psql -U postgres -d design_support < /backup/postgresql/design_support_backup.sql

# Django 마이그레이션 롤백
docker-compose exec web python manage.py migrate <app_name> <migration_number>
```

---

## 11. 배포 체크리스트

### 11.1. 사전 점검
- [ ] 서버 사양 충족 여부 확인
- [ ] Docker 및 Docker Compose 설치 확인
- [ ] 도메인 및 SSL 인증서 준비
- [ ] AI Provider API 키 준비
- [ ] 방화벽 설정 완료
- [ ] 백업 전략 수립

### 11.2. 배포 후 점검
- [ ] 모든 서비스 정상 시작 확인
- [ ] 헬스 체크 통과 확인
- [ ] SSL 인증서 정상 적용 확인
- [ ] 관리자 콘솔 접속 확인
- [ ] 모델 카탈로그 설정 확인
- [ ] 트렌드 출처 등록 확인
- [ ] 백업 스크립트 실행 테스트

---

*본 매뉴얼은 시스템 변경사항에 따라 지속적으로 업데이트됩니다.*
