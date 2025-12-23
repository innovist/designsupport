"""
System Detection Utilities
플랫폼 및 하드웨어 감지 유틸리티
"""

import platform
import subprocess
from typing import Tuple, List

def detect_gpu_availability() -> Tuple[bool, str]:
    """
    NVIDIA GPU 가용성 확인

    Returns:
        Tuple[bool, str]: (GPU_가용여부, GPU_정보)
    """
    system = platform.system()

    try:
        # NVIDIA GPU 확인 (PyTorch CUDA)
        try:
            import torch
            if torch.cuda.is_available():
                gpu_name = torch.cuda.get_device_name(0)
                return True, f"CUDA: {gpu_name}"
        except ImportError:
            pass

        # Linux NVIDIA 확인 (nvidia-smi)
        if system == "Linux":
            try:
                result = subprocess.run(
                    ['nvidia-smi'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    return True, "NVIDIA GPU (nvidia-smi)"
            except (FileNotFoundError, subprocess.TimeoutExpired):
                pass

        return False, "No GPU detected"

    except Exception as e:
        return False, f"GPU detection failed: {str(e)}"

def get_available_image_models() -> List[str]:
    """
    GPU 환경에 따른 사용 가능한 이미지 생성 모델 목록

    Returns:
        List[str]: 사용 가능한 모델 리스트
    """
    has_gpu, gpu_info = detect_gpu_availability()

    if has_gpu:
        # GPU가 있는 경우 모든 모델 사용 가능
        return ["zimage", "seedream", "nano_banana"]
    else:
        # GPU가 없는 경우 Z-Image 제외
        print(f"GPU 미감지: {gpu_info}")
        print("CPU-only 모드로 실행됩니다. Z-Image-turbo가 비활성화됩니다.")
        return ["seedream", "nano_banana"]

def get_system_info() -> dict:
    """
    시스템 정보 반환

    Returns:
        dict: 시스템 정보
    """
    has_gpu, gpu_info = detect_gpu_availability()

    return {
        "platform": platform.system(),
        "platform_release": platform.release(),
        "platform_version": platform.version(),
        "architecture": platform.machine(),
        "processor": platform.processor(),
        "gpu_available": has_gpu,
        "gpu_info": gpu_info,
        "available_models": get_available_image_models()
    }
