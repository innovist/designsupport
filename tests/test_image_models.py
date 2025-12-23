"""
이미지 생성 모델 테스트 스크립트
macOS 환경에서 z-image는 제외하고 Seedream, Nano Banana 테스트
"""

import asyncio
import sys
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.config import get_settings
from app.core.settings_storage import (
    get_seedream_model, get_seedream_model_id,
    get_nano_banana_model, get_nano_banana_base_model, get_nano_banana_pro_model,
    get_nano_banana_model_id, AVAILABLE_MODELS
)


async def test_seedream():
    """Seedream 이미지 생성 테스트"""
    print("\n" + "=" * 60)
    print("Seedream 이미지 생성 테스트")
    print("=" * 60)

    from ai_clients.seedream_client import get_seedream_client, SeedreamGenerationConfig

    settings = get_settings()

    # API 키 확인
    if not settings.seedream_api_key:
        print("❌ Seedream API 키가 설정되지 않음")
        return False

    print(f"✓ API 키 설정됨: {settings.seedream_api_key[:10]}...")
    print(f"✓ API URL: {settings.seedream_api_url or 'https://ark.ap-southeast.bytepluses.com/api/v3'}")

    # 모델 설정 확인
    model = get_seedream_model()
    model_id = get_seedream_model_id(model)
    print(f"✓ 모델: {model}")
    print(f"✓ 모델 ID: {model_id}")

    client = get_seedream_client()

    # 간단한 테스트 프롬프트
    prompt = "Simple fashion jacket, flat lay, white background, professional product photography"

    config = SeedreamGenerationConfig(
        width=512,  # 테스트용 작은 사이즈
        height=512,
        steps=20,
        model=model
    )

    try:
        print(f"\n프롬프트: {prompt}")
        print("이미지 생성 중...")

        response = await client.generate_image(prompt=prompt, config=config)

        if response.images:
            print(f"✅ Seedream 이미지 생성 성공!")
            print(f"   - 생성 시간: {response.generation_time:.2f}초")
            print(f"   - 이미지 수: {len(response.images)}")
            print(f"   - 이미지 크기: {len(response.images[0])} bytes")
            return True
        else:
            print("❌ 이미지 생성 실패: 응답에 이미지 없음")
            return False

    except Exception as e:
        print(f"❌ Seedream 테스트 실패: {e}")
        return False


async def test_nano_banana():
    """Nano Banana 이미지 생성 테스트"""
    print("\n" + "=" * 60)
    print("Nano Banana 이미지 생성 테스트")
    print("=" * 60)

    from ai_clients.nano_banana_client import get_nano_banana_client, NanoBananaGenerationConfig

    settings = get_settings()

    # API 키 확인
    if not settings.nano_banana_api_key:
        print("❌ Nano Banana API 키가 설정되지 않음")
        return False

    api_key = settings.nano_banana_api_key
    is_google = api_key.startswith("AIza")

    print(f"✓ API 키 설정됨: {api_key[:10]}...")
    print(f"✓ Google GenAI 키: {is_google}")

    # 모델 설정 확인
    model = get_nano_banana_model()
    base_model = get_nano_banana_base_model()
    pro_model = get_nano_banana_pro_model()

    print(f"✓ 기본 모델: {model}")
    print(f"✓ Base 모델: {base_model}")
    print(f"✓ Pro 모델: {pro_model}")

    if is_google:
        base_id = get_nano_banana_model_id(base_model, "google")
        pro_id = get_nano_banana_model_id(pro_model, "google")
        print(f"✓ Base Google ID: {base_id}")
        print(f"✓ Pro Google ID: {pro_id}")

    client = get_nano_banana_client()

    # 테스트 1: Base 모델 (스케치 목적)
    print("\n--- Base 모델 테스트 (스케치) ---")
    config_base = NanoBananaGenerationConfig(
        width=512,
        height=512,
        steps=20,
        model=base_model,
        purpose="sketch"
    )

    prompt_sketch = "Fashion design sketch of a modern dress, black and white line drawing, technical illustration"

    try:
        print(f"프롬프트: {prompt_sketch[:50]}...")
        print("이미지 생성 중...")

        response_base = await client.generate_image(prompt=prompt_sketch, config=config_base)

        if response_base.images:
            print(f"✅ Base 모델 이미지 생성 성공!")
            print(f"   - 모델: {response_base.model}")
            print(f"   - 생성 시간: {response_base.generation_time:.2f}초")
            print(f"   - 이미지 크기: {len(response_base.images[0])} bytes")
        else:
            print("❌ Base 모델 이미지 생성 실패")

    except Exception as e:
        print(f"❌ Base 모델 테스트 실패: {e}")

    # 테스트 2: Pro 모델 (고품질)
    print("\n--- Pro 모델 테스트 (고품질) ---")
    config_pro = NanoBananaGenerationConfig(
        width=512,
        height=512,
        steps=40,  # 높은 스텝 = Pro 선택
        model=pro_model,
        purpose="general"
    )

    prompt_pro = "Luxury fashion coat, professional product photography, studio lighting, high quality"

    try:
        print(f"프롬프트: {prompt_pro[:50]}...")
        print("이미지 생성 중...")

        response_pro = await client.generate_image(prompt=prompt_pro, config=config_pro)

        if response_pro.images:
            print(f"✅ Pro 모델 이미지 생성 성공!")
            print(f"   - 모델: {response_pro.model}")
            print(f"   - 생성 시간: {response_pro.generation_time:.2f}초")
            print(f"   - 이미지 크기: {len(response_pro.images[0])} bytes")
            return True
        else:
            print("❌ Pro 모델 이미지 생성 실패")
            return False

    except Exception as e:
        print(f"❌ Pro 모델 테스트 실패: {e}")
        return False


async def test_model_settings():
    """모델 설정 확인"""
    print("\n" + "=" * 60)
    print("모델 설정 확인")
    print("=" * 60)

    print("\n사용 가능한 모델:")
    for category, models in AVAILABLE_MODELS.items():
        print(f"\n{category}:")
        if isinstance(models, dict):
            for subcat, model_list in models.items():
                if isinstance(model_list, list):
                    print(f"  {subcat}: {', '.join(model_list)}")
                else:
                    print(f"  {subcat}: {model_list}")

    print("\n현재 설정:")
    print(f"  Gemini: {__import__('app.core.settings_storage', fromlist=['get_gemini_model']).get_gemini_model()}")
    print(f"  GLM: {__import__('app.core.settings_storage', fromlist=['get_glm_model']).get_glm_model()}")
    print(f"  Seedream: {get_seedream_model()}")
    print(f"  Nano Banana: {get_nano_banana_model()}")


async def main():
    """메인 테스트 함수"""
    print("=" * 60)
    print("이미지 생성 모델 테스트 시작")
    print("macOS 환경 - z-image 제외")
    print("=" * 60)

    # 모델 설정 확인
    await test_model_settings()

    results = {}

    # Seedream 테스트
    results["seedream"] = await test_seedream()

    # Nano Banana 테스트
    results["nano_banana"] = await test_nano_banana()

    # 결과 요약
    print("\n" + "=" * 60)
    print("테스트 결과 요약")
    print("=" * 60)

    for model, success in results.items():
        status = "✅ 성공" if success else "❌ 실패"
        print(f"  {model}: {status}")

    all_success = all(results.values())
    print(f"\n전체 결과: {'✅ 모든 테스트 통과' if all_success else '❌ 일부 테스트 실패'}")

    return all_success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
