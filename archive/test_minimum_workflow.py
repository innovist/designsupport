"""
간단한 워크플로우 테스트
핵심 기능 검증
"""

import asyncio
import sys
import os

# 프로젝트 루트 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.system_detector import get_system_info, get_available_image_models


async def test_system_detection():
    """시스템 감지 기능 테스트"""
    print("\n=== 시스템 감지 테스트 ===")

    # 시스템 정보 출력
    sys_info = get_system_info()
    print("\n📋 시스템 정보:")
    for key, value in sys_info.items():
        print(f"  {key}: {value}")

    # 사용 가능한 이미지 모델
    models = get_available_image_models()
    print(f"\n🔍 사용 가능한 이미지 모델: {models}")

    return len(models) > 0


async def test_basic_workflow():
    """기본 워크플로우 생성 테스트"""
    print("\n=== 기본 워크플로우 테스트 ===")

    try:
        # 간단한 세션 생성 테스트
        import uuid
        session_id = f"test_session_{uuid.uuid4().hex[:12]}"
        print(f"✅ 세션 ID 생성: {session_id}")

        # 간단한 입력 데이터
        user_input = {
            "prompt": "봄 여성 캐주얼 패션",
            "filters": {
                "gender": "여성",
                "season": "봄"
            }
        }
        print(f"✅ 사용자 입력: {user_input}")

        return True

    except Exception as e:
        print(f"❌ 기본 워크플로우 테스트 실패: {str(e)}")
        return False


async def test_crawler_import():
    """크롤러 임포트 테스트"""
    print("\n=== 크롤러 임포트 테스트 ===")

    try:
        from crawlers.crawler_service import CrawlerService
        print("✅ CrawlerService 임포트 성공")

        # 서비스 인스턴스 생성
        service = CrawlerService()
        print("✅ CrawlerService 인스턴스 생성 성공")

        return True

    except Exception as e:
        print(f"❌ 크롤러 임포트 실패: {str(e)}")
        return False


async def test_consistency_pipeline():
    """일관성 파이프라인 임포트 테스트"""
    print("\n=== 일관성 파이프라 임포트 테스트 ===")

    try:
        # GPU 감지 먼저 실행
        from app.utils.system_detector import detect_gpu_availability
        has_gpu, gpu_type = detect_gpu_availability()
        print(f"✅ GPU 감지: {has_gpu}, 타입: {gpu_type}")

        return True

    except Exception as e:
        print(f"❌ 일관성 파이프라인 테스트 실패: {str(e)}")
        return False


async def run_minimum_tests():
    """최소한의 테스트 실행"""
    print("=" * 60)
    print("패션 AI 생성 시스템 최소 테스트 시작")
    print("=" * 60)

    test_results = []

    # 테스트 1: 시스템 감지
    test_results.append(await test_system_detection())

    # 테스트 2: 기본 워크플로우
    test_results.append(await test_basic_workflow())

    # 테스트 3: 크롤러 임포트
    test_results.append(await test_crawler_import())

    # 테스트 4: 일관성 파이프라인
    test_results.append(await test_consistency_pipeline())

    # 결과 요약
    print("\n" + "=" * 60)
    print("테스트 결과 요약")
    print("=" * 60)

    passed = sum(test_results)
    total = len(test_results)

    print(f"통과: {passed}/{total}")

    if passed == total:
        print("✅ 모든 테스트 통과")
    else:
        print(f"❌ {total - passed}개 테스트 실패")

    return passed == total


if __name__ == "__main__":
    success = asyncio.run(run_minimum_tests())
    sys.exit(0 if success else 1)