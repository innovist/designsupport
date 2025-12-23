"""
Full Workflow Integration Test
패션 AI 생성 시스템 전체 워크플로우 테스트
"""

import asyncio
import logging
import sys
import os

# 프로젝트 루트 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.full_workflow_service import FullWorkflowService
from app.utils.system_detector import get_system_info, get_available_image_models

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_case_1_spring_womens_casual():
    """테스트 케이스 1: 봄 여성 캐주얼 패션"""
    print("\n=== 테스트 케이스 1: 봄 여성 캐주얼 패션 ===")

    service = FullWorkflowService()

    # 세션 생성
    user_input = {
        "prompt": "내년 봄 20대 여성을 위한 편안한 캐주얼 패션 트렌드",
        "filters": {
            "gender": "여성",
            "age_group": "20대",
            "season": "봄",
            "region": "서울"
        }
    }

    session_id = await service.create_session("project_001", user_input)
    print(f"✅ 세션 생성: {session_id}")

    # 워크플로우 실행
    result = await service.start_workflow(session_id)
    print(f"✅ 워크플로우 결과: {result['status']}")

    # 상태 확인
    status = await service.get_session_status(session_id)
    print(f"✅ 최종 상태: {status['status']}, 진행률: {status['progress']}%")


async def test_case_2_business_casual():
    """테스트 케이스 2: 비즈니스 캐주얼"""
    print("\n=== 테스트 케이스 2: 비즈니스 캐주얼 ===")

    service = FullWorkflowService()

    user_input = {
        "prompt": "프레젠테이블을 위한 전문적인 비즈니스 캐주얼 디자인",
        "filters": {
            "gender": "남성",
            "age_group": "30대",
            "season": "상시",
            "region": "강남",
            "style": "비즈니스"
        }
    }

    session_id = await service.create_session("project_002", user_input)
    print(f"✅ 세션 생성: {session_id}")

    result = await service.start_workflow(session_id)
    print(f"✅ 워크플로우 결과: {result['status']}")


async def test_case_3_streetwear_collection():
    """테스트 케이스 3: 스트릿웨어 컬렉션"""
    print("\n=== 테스트 케이스 3: 스트릿웨어 컬렉션 ===")

    service = FullWorkflowService()

    user_input = {
        "prompt": "젊은 세대들이 선호하는 스트릿웨어 스타일 컬렉션 제안",
        "filters": {
            "target": "Z세대",
            "season": "가을",
            "style": "스트릿웨어",
            "keywords": ["oversized", "urban", "street fashion"]
        }
    }

    session_id = await service.create_session("project_003", user_input)
    print(f"✅ 세션 생성: {session_id}")

    result = await service.start_workflow(session_id)
    print(f"✅ 워크플로우 결과: {result['status']}")


async def test_case_4_sports_wear():
    """테스트 케이스 4: 스포츠웨어"""
    print("\n=== 테스트 케이스 4: 스포츠웨어 ===")

    service = FullWorkflowService()

    user_input = {
        "prompt": "편안하고 자유로운 스포츠웨어 디자인",
        "filters": {
            "activity": "everyday",
            "style": "sporty",
            "keywords": ["athleisure", "comfort", "functional"]
        }
    }

    session_id = await service.create_session("project_004", user_input)
    print(f"✅ 세션 생성: {session_id}")

    result = await service.start_workflow(session_id)
    print(f"✅ 워크플로우 결과: {result['status']}")


async def test_case_5_ethnic_fusion():
    """테스트 케이스 5: 민속 퓨전 패션"""
    print("\n=== 테스트 케이스 5: 민족 퓨전 패션 ===")

    service = FullWorkflowService()

    user_input = {
        "prompt": "한국과 서양 전통 패션 요소를 융합한 독특한 디자인",
        "filters": {
            "elements": ["한복", "양단", "인디안"],
            "keywords": ["fusion", "cultural", "traditional"]
        }
    }

    session_id = await service.create_session("project_005", user_input)
    print(f"✅ 세션 생성: {session_id}")

    result = await service.start_workflow(session_id)
    print(f"✅ 워크플로우 결과: {result['status']}")


async def run_all_tests():
    """모든 테스트 실행"""
    print("=" * 60)
    print("패션 AI 생성 시스템 전체 워크플로우 테스트 시작")
    print("=" * 60)

    # 시스템 정보 출력
    sys_info = get_system_info()
    print("\n📋 시스템 정보:")
    for key, value in sys_info.items():
        print(f"  {key}: {value}")

    print("\n🔍 사용 가능한 이미지 모델:")
    models = get_available_image_models()
    print(f"  {models}")

    try:
        await test_case_1_spring_womens_casual()
        await test_case_2_business_casual()
        await test_case_3_streetwear_collection()
        await test_case_4_sports_wear()
        await test_case_5_ethnic_fusion()

        print("\n" + "=" * 60)
        print("✅ 모든 테스트 완료")
        print("=" * 60)

    except Exception as e:
        logger.error(f"테스트 실패: {str(e)}")
        print(f"\n❌ 테스트 오류: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(run_all_tests())