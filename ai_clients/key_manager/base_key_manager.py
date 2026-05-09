"""
Base key manager for AI APIs
"""

import asyncio
import hashlib
import time
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

from app.core.logging import get_logger

logger = get_logger(__name__)


class KeyStatus(Enum):
    """키 상태"""
    ACTIVE = "active"
    RATE_LIMITED = "rate_limited"
    ERROR = "error"
    EXHAUSTED = "exhausted"


@dataclass
class ApiKeyInfo:
    """API 키 정보"""
    key_id: str
    api_key: str
    status: KeyStatus
    last_used: Optional[datetime] = None
    usage_count: int = 0
    error_count: int = 0
    rate_limit_reset_time: Optional[datetime] = None
    daily_limit: Optional[int] = None
    daily_usage: int = 0
    monthly_limit: Optional[int] = None
    monthly_usage: int = 0
    metadata: Optional[Dict[str, Any]] = None


class BaseKeyManager(ABC):
    """기본 키 관리자"""
    # @MX:ANCHOR: [AUTO] Abstract base class for API key management. All key managers inherit from this class.
    # @MX:REASON: High fan_in (5+ key manager implementations). Key rotation, rate limiting, and error tracking logic shared across all AI clients.

    def __init__(
        self,
        api_keys: List[str],
        rate_limit_window: int = 60,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ):
        """
        초기화

        Args:
            api_keys: API 키 목록
            rate_limit_window: Rate limit 창 (초)
            max_retries: 최대 재시도 횟수
            retry_delay: 재시도 지연 (초)
        """
        self.api_keys: Dict[str, ApiKeyInfo] = {}
        self.current_index = 0
        self.rate_limit_window = rate_limit_window
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._lock = asyncio.Lock()

        # API 키 초기화
        for i, key in enumerate(api_keys):
            key_id = self._generate_key_id(key)
            self.api_keys[key_id] = ApiKeyInfo(
                key_id=key_id,
                api_key=key,
                status=KeyStatus.ACTIVE
            )

    def _generate_key_id(self, api_key: str) -> str:
        """API 키로부터 고유 ID 생성"""
        return hashlib.sha256(api_key.encode()).hexdigest()[:16]

    async def get_next_key(self) -> Tuple[str, str]:
        """
        다음 사용 가능한 키 반환

        Returns:
            (key_id, api_key) 튜플
        """
        # @MX:WARN: [AUTO] Async lock protects key selection but auto-reset on exhaustion may hide persistent API issues.
        # @MX:REASON: Round-robin selection with automatic reset of rate-limited keys. If all keys are exhausted, raises exception after reset attempt.
        async with self._lock:
            # 활성 상태인 키 찾기
            active_keys = [
                k for k in self.api_keys.values()
                if k.status == KeyStatus.ACTIVE
            ]

            if not active_keys:
                # 모든 키가 비활성 상태면 재설정 시도
                await self._reset_rate_limited_keys()
                active_keys = [
                    k for k in self.api_keys.values()
                    if k.status == KeyStatus.ACTIVE
                ]

                if not active_keys:
                    raise Exception("No available API keys")

            # 라운드 로빈 방식으로 키 선택
            key_info = active_keys[self.current_index % len(active_keys)]
            self.current_index += 1

            # 사용 기록 업데이트
            key_info.last_used = datetime.utcnow()
            key_info.usage_count += 1

            logger.debug(f"Selected API key: {key_info.key_id}")

            return key_info.key_id, key_info.api_key

    async def mark_key_error(
        self,
        key_id: str,
        error_type: str,
        reset_time: Optional[datetime] = None
    ) -> None:
        """
        키 에러 표시

        Args:
            key_id: 키 ID
            error_type: 에러 타입
            reset_time: 리셋 시간
        """
        # @MX:WARN: [AUTO] Complex error classification with multiple error types. Error count threshold can permanently disable keys.
        # @MX:REASON: Handles rate_limit, invalid_key, quota_exceeded, and general errors. Keys marked ERROR after max_retries exceeded.
        async with self._lock:
            if key_id not in self.api_keys:
                return

            key_info = self.api_keys[key_id]
            key_info.error_count += 1

            if error_type == "rate_limit":
                key_info.status = KeyStatus.RATE_LIMITED
                key_info.rate_limit_reset_time = reset_time or (
                    datetime.utcnow() + timedelta(seconds=self.rate_limit_window)
                )
                logger.warning(f"Key {key_id} rate limited until {key_info.rate_limit_reset_time}")

            elif error_type in ["invalid_key", "authentication_failed"]:
                key_info.status = KeyStatus.ERROR
                logger.error(f"Key {key_id} marked as error: {error_type}")

            elif error_type == "quota_exceeded":
                key_info.status = KeyStatus.EXHAUSTED
                logger.warning(f"Key {key_id} quota exhausted")

            else:
                # 일반 에러
                if key_info.error_count >= self.max_retries:
                    key_info.status = KeyStatus.ERROR
                    logger.error(f"Key {key_id} marked as error after {key_info.error_count} errors")

    async def _reset_rate_limited_keys(self) -> None:
        """Rate limit된 키 리셋"""
        now = datetime.utcnow()
        for key_info in self.api_keys.values():
            if (
                key_info.status == KeyStatus.RATE_LIMITED
                and key_info.rate_limit_reset_time
                and key_info.rate_limit_reset_time <= now
            ):
                key_info.status = KeyStatus.ACTIVE
                key_info.rate_limit_reset_time = None
                logger.info(f"Reset rate limit for key: {key_info.key_id}")

    async def update_usage(
        self,
        key_id: str,
        daily_usage: Optional[int] = None,
        monthly_usage: Optional[int] = None
    ) -> None:
        """
        사용량 업데이트

        Args:
            key_id: 키 ID
            daily_usage: 일일 사용량
            monthly_usage: 월간 사용량
        """
        async with self._lock:
            if key_id not in self.api_keys:
                return

            key_info = self.api_keys[key_id]
            if daily_usage is not None:
                key_info.daily_usage = daily_usage
            if monthly_usage is not None:
                key_info.monthly_usage = monthly_usage

    def get_key_stats(self) -> Dict[str, Any]:
        """키 통계 정보 반환"""
        stats = {
            "total_keys": len(self.api_keys),
            "active_keys": 0,
            "rate_limited_keys": 0,
            "error_keys": 0,
            "exhausted_keys": 0,
            "total_usage": 0,
            "total_errors": 0,
            "keys": []
        }

        for key_info in self.api_keys.values():
            stats["total_usage"] += key_info.usage_count
            stats["total_errors"] += key_info.error_count

            if key_info.status == KeyStatus.ACTIVE:
                stats["active_keys"] += 1
            elif key_info.status == KeyStatus.RATE_LIMITED:
                stats["rate_limited_keys"] += 1
            elif key_info.status == KeyStatus.ERROR:
                stats["error_keys"] += 1
            elif key_info.status == KeyStatus.EXHAUSTED:
                stats["exhausted_keys"] += 1

            stats["keys"].append({
                "key_id": key_info.key_id[:8] + "...",
                "status": key_info.status.value,
                "usage_count": key_info.usage_count,
                "error_count": key_info.error_count,
                "last_used": key_info.last_used.isoformat() if key_info.last_used else None,
                "daily_usage": key_info.daily_usage,
                "monthly_usage": key_info.monthly_usage
            })

        return stats

    @abstractmethod
    async def test_key(self, api_key: str) -> bool:
        """
        API 키 유효성 테스트

        Args:
            api_key: 테스트할 API 키

        Returns:
            유효성 여부
        """
        pass

    async def validate_all_keys(self) -> Dict[str, bool]:
        """모든 키 유효성 검사"""
        results = {}
        for key_id, key_info in self.api_keys.items():
            try:
                is_valid = await self.test_key(key_info.api_key)
                results[key_id] = is_valid

                if not is_valid:
                    await self.mark_key_error(key_id, "invalid_key")
            except Exception as e:
                logger.error(f"Failed to validate key {key_id}: {e}")
                results[key_id] = False
                await self.mark_key_error(key_id, "validation_failed")

        return results

    def reset_daily_usage(self) -> None:
        """일일 사용량 리셋"""
        for key_info in self.api_keys.values():
            key_info.daily_usage = 0
        logger.info("Daily usage reset for all keys")

    def reset_monthly_usage(self) -> None:
        """월간 사용량 리셋"""
        for key_info in self.api_keys.values():
            key_info.monthly_usage = 0
        logger.info("Monthly usage reset for all keys")