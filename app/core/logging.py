import logging
import logging.handlers
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
# structlog is optional - only used in production
try:
    import structlog
    from structlog.stdlib import LoggerFactory
    STRUCTLOG_AVAILABLE = True
except ImportError:
    STRUCTLOG_AVAILABLE = False
    structlog = None
    LoggerFactory = None


class SensitiveDataFilter(logging.Filter):
    """민감정보 마스킹 필터"""

    SENSITIVE_KEYS = [
        'api_key', 'password', 'secret', 'token', 'key',
        'authorization', 'cookie', 'session', 'credential'
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        """로그 레코드의 민감정보 마스킹"""
        if hasattr(record, 'msg'):
            record.msg = self._mask_sensitive_data(str(record.msg))
        return True

    def _mask_sensitive_data(self, message: str) -> str:
        """메시지 내의 민감정보 마스킹"""
        import re

        for key in self.SENSITIVE_KEYS:
            # key=value 형태 마스킹
            pattern = rf'({key}[=\s]+)[\w\-\.+/=]+'
            message = re.sub(pattern, r'\1***MASKED***', message, flags=re.IGNORECASE)

            # Bearer token 마스킹
            pattern = r'(bearer\s+)[\w\-\.+/=]+'
            message = re.sub(pattern, r'\1***MASKED***', message, flags=re.IGNORECASE)

        return message


class JSONFormatter(logging.Formatter):
    """JSON 형식 로그 포매터"""

    def format(self, record: logging.LogRecord) -> str:
        """로그 레코드를 JSON 형식으로 포맷팅"""
        import json

        log_data = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }

        # 예외 정보 추가
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)

        # 추가 필드 추가
        for key, value in record.__dict__.items():
            if key not in {
                'name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                'filename', 'module', 'lineno', 'funcName', 'created',
                'msecs', 'relativeCreated', 'thread', 'threadName',
                'processName', 'process', 'getMessage', 'exc_info',
                'exc_text', 'stack_info'
            }:
                log_data[key] = value

        return json.dumps(log_data, ensure_ascii=False)


class ColoredFormatter(logging.Formatter):
    """콘솔 출력용 컬러 포매터"""

    # ANSI 컬러 코드
    COLORS = {
        'DEBUG': '\033[36m',      # 청록색
        'INFO': '\033[32m',       # 녹색
        'WARNING': '\033[33m',    # 노란색
        'ERROR': '\033[31m',      # 빨간색
        'CRITICAL': '\033[35m',   # 보라색
        'RESET': '\033[0m'        # 리셋
    }

    def format(self, record: logging.LogRecord) -> str:
        """로그 레코드에 컬러 적용"""
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']

        # 시간 포맷팅
        timestamp = datetime.fromtimestamp(record.created).strftime('%H:%M:%S')

        # 레벨에 컬러 적용
        record.levelname = f"{color}{record.levelname}{reset}"

        # 포맷팅
        formatted = super().format(record)

        # 타임스탬프 추가
        return f"{timestamp} - {formatted}"


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    log_rotation: str = "daily",
    log_retention_days: int = 30,
    json_logs: bool = False,
    enable_console: bool = True
) -> None:
    """로깅 시스템 설정"""

    # 로그 레벨 설정
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    # 루트 로거 설정
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # 기존 핸들러 제거
    root_logger.handlers.clear()

    # 포매터 생성
    if json_logs:
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

    # 콘솔 핸들러
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)

        if json_logs:
            console_handler.setFormatter(formatter)
        else:
            console_handler.setFormatter(ColoredFormatter())

        console_handler.addFilter(SensitiveDataFilter())
        root_logger.addHandler(console_handler)

    # 파일 핸들러
    if log_file:
        # 로그 디렉토리 생성
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        if log_rotation == "daily":
            file_handler = logging.handlers.TimedRotatingFileHandler(
                filename=log_file,
                when='midnight',
                interval=1,
                backupCount=log_retention_days,
                encoding='utf-8'
            )
        else:
            file_handler = logging.handlers.RotatingFileHandler(
                filename=log_file,
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=5,
                encoding='utf-8'
            )

        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        file_handler.addFilter(SensitiveDataFilter())
        root_logger.addHandler(file_handler)


def setup_structlog() -> None:
    """structlog 설정"""
    if not STRUCTLOG_AVAILABLE or structlog is None:
        return
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> logging.Logger:
    """로거 인스턴스 반환"""
    return logging.getLogger(name)


def log_performance(func_name: str, duration: float, details: Optional[Dict[str, Any]] = None) -> None:
    """성능 로그 기록"""
    logger = get_logger("performance")

    log_data = {
        "function": func_name,
        "duration_ms": round(duration * 1000, 2),
    }

    if details:
        log_data.update(details)

    logger.info(f"Performance: {func_name} completed", extra=log_data)


def log_api_request(
    method: str,
    endpoint: str,
    user_id: Optional[str] = None,
    duration: Optional[float] = None,
    status_code: Optional[int] = None
) -> None:
    """API 요청 로그 기록"""
    logger = get_logger("api")

    log_data = {
        "method": method,
        "endpoint": endpoint,
        "user_id": user_id,
    }

    if duration:
        log_data["duration_ms"] = round(duration * 1000, 2)

    if status_code:
        log_data["status_code"] = status_code

    logger.info(f"API Request: {method} {endpoint}", extra=log_data)


def log_error(
    error: Exception,
    context: Optional[Dict[str, Any]] = None,
    user_id: Optional[str] = None
) -> None:
    """에러 로그 기록"""
    logger = get_logger("error")

    log_data = {
        "error_type": type(error).__name__,
        "error_message": str(error),
        "user_id": user_id,
    }

    if context:
        log_data.update(context)

    logger.error(
        f"Error occurred: {type(error).__name__}",
        exc_info=True,
        extra=log_data
    )


def log_crawl_progress(
    job_id: str,
    total: int,
    completed: int,
    failed: int = 0,
    source: Optional[str] = None
) -> None:
    """크롤링 진행률 로그 기록"""
    logger = get_logger("crawler")

    progress = round((completed / total) * 100, 2) if total > 0 else 0

    log_data = {
        "job_id": job_id,
        "total": total,
        "completed": completed,
        "failed": failed,
        "progress_percent": progress,
        "source": source,
    }

    logger.info(f"Crawl Progress: {progress}%", extra=log_data)


def log_generation_progress(
    job_id: str,
    stage: str,
    total_steps: int,
    current_step: int,
    model: Optional[str] = None
) -> None:
    """생성 진행률 로그 기록"""
    logger = get_logger("generation")

    progress = round((current_step / total_steps) * 100, 2) if total_steps > 0 else 0

    log_data = {
        "job_id": job_id,
        "stage": stage,
        "total_steps": total_steps,
        "current_step": current_step,
        "progress_percent": progress,
        "model": model,
    }

    logger.info(f"Generation Progress: {stage} - {progress}%", extra=log_data)


# 환경 변수에서 로깅 설정 로드
def load_logging_config() -> None:
    """환경 변수에서 로깅 설정 로드 및 적용"""
    from dotenv import load_dotenv

    load_dotenv()

    setup_logging(
        level=os.getenv("LOG_LEVEL", "INFO"),
        log_file=os.getenv("LOG_FILE"),
        log_rotation=os.getenv("LOG_ROTATION", "daily"),
        log_retention_days=int(os.getenv("LOG_RETENTION_DAYS", "30")),
        json_logs=os.getenv("ENVIRONMENT") == "production",
        enable_console=True
    )

    if os.getenv("ENVIRONMENT") == "production":
        setup_structlog()