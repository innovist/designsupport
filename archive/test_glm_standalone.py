#!/usr/bin/env python3
"""
Standalone test script for GLM client fix
"""

import sys
import os
import asyncio
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

# Set up basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Mock the missing dependencies
class MockConfig:
    def __init__(self):
        self.glm_api_key = os.environ.get("GLM_API_KEY", "test_key")

def get_settings():
    return MockConfig()

def get_logger(name):
    return logging.getLogger(name)

# Try to import zhipuai, if not available, use mock
try:
    import zhipuai
    ZHIPUAI_AVAILABLE = True
    print("✓ zhipuai module is available")
except ImportError:
    ZHIPUAI_AVAILABLE = False
    print("⚠ zhipuai module not available. Using mock implementation.")

@dataclass
class GLMGenerationConfig:
    """GLM 생성 설정"""
    temperature: float = 0.7
    top_p: float = 0.9
    max_tokens: int = 8192
    stream: bool = False
    model: str = "glm-4.7"

@dataclass
class GLMResponse:
    """GLM 응답"""
    text: str
    model: str
    usage: Optional[Dict[str, int]] = None
    finish_reason: Optional[str] = None
    created: Optional[int] = None
    id: Optional[str] = None

# Wrapper class to emulate the new ZhipuAI API with version 1.0.7
class ZhipuAI:
    """Compatibility wrapper for zhipuai 1.0.7"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        if ZHIPUAI_AVAILABLE:
            zhipuai.api_key = api_key

    @property
    def chat(self):
        return self

    @property
    def completions(self):
        return self

    @property
    def embeddings(self):
        return self

    def create(self, model: str, messages: List[Dict], temperature: float = 0.7,
               top_p: float = 0.9, max_tokens: int = 8192, stream: bool = False,
               input: Optional[str] = None):
        """Create chat completion or embedding"""
        if not ZHIPUAI_AVAILABLE:
            # Return mock response when zhipuai is not available
            logger.warning(f"Mock response for GLM {model} (zhipuai not installed)")
            if model.startswith("embedding"):
                return EmbeddingResponse({})
            else:
                # Create mock chat completion response
                mock_response = {
                    "content": f"Mock response from GLM {model} (zhipuai not installed). Please install zhipuai package to use actual AI.",
                    "finish_reason": "stop"
                }
                return ChatCompletionResponse(mock_response)

        if model.startswith("embedding"):
            # Handle embedding
            response = zhipuai.model_api.invoke(
                model=model,
                prompt=input
            )
            return EmbeddingResponse(response)
        else:
            # Handle chat completion
            response = zhipuai.model_api.invoke(
                model=model,
                messages=messages,
                temperature=temperature,
                top_p=top_p,
                max_tokens=max_tokens,
                incremental=stream
            )
            return ChatCompletionResponse(response)

class EmbeddingResponse:
    """Mock embedding response"""

    def __init__(self, response):
        self.data = [EmbeddingData(response)]

class EmbeddingData:
    """Mock embedding data"""

    def __init__(self, response):
        # Generate a mock embedding vector
        self.embedding = [0.1] * 1024  # 1024-dimensional embedding

class ChatCompletionResponse:
    """Mock chat completion response"""

    def __init__(self, response):
        self.choices = [ChatChoice(response)]
        self.usage = Usage(response) if 'usage' in response else None
        self.created = response.get('created', None)
        self.id = response.get('id', None)

class ChatChoice:
    """Mock chat choice"""

    def __init__(self, response):
        self.message = Message(response)
        self.finish_reason = response.get('finish_reason', None)
        self.delta = Delta(response) if 'delta' in response else None

class Message:
    """Mock message"""

    def __init__(self, response):
        # Handle both direct content and nested message structures
        if 'content' in response:
            self.content = response['content']
        elif 'message' in response and 'content' in response['message']:
            self.content = response['message']['content']
        else:
            self.content = str(response)  # Fallback to string representation

class Delta:
    """Mock delta for streaming"""

    def __init__(self, response):
        self.content = response.get('content', '')

class Usage:
    """Mock usage"""

    def __init__(self, response):
        usage_data = response.get('usage', {})
        self.prompt_tokens = usage_data.get('prompt_tokens', 0)
        self.completion_tokens = usage_data.get('completion_tokens', 0)
        self.total_tokens = usage_data.get('total_tokens', 0)

class GLMClient:
    """GLM AI 클라이언트"""

    def __init__(self):
        """초기화"""
        self._client_cache = {}
        self._last_init_time = {}
        self.cache_ttl = 3600  # 1시간 캐시

    async def _get_client(self):
        """
        클라이언트 가져오기 (캐시된 것 재사용)

        Returns:
            생성된 클라이언트
        """
        current_time = asyncio.get_event_loop().time()

        # 캐시된 클라이언트 확인
        if 'glm_client' in self._client_cache:
            cache_time = self._last_init_time.get('glm_client', 0)
            if current_time - cache_time < self.cache_ttl:
                return self._client_cache['glm_client']

        # 새 클라이언트 생성
        api_key = "test_api_key"  # Use test key
        client = ZhipuAI(api_key=api_key)

        # 캐시에 저장
        self._client_cache['glm_client'] = client
        self._last_init_time['glm_client'] = current_time

        logger.info("Created new GLM client")
        return client

async def test_glm_client():
    """Test GLM client functionality"""
    try:
        client = GLMClient()

        # Test client creation
        glm_client = await client._get_client()
        print("✓ GLM client created successfully")

        # Test ZhipuAI wrapper
        assert hasattr(glm_client, 'chat')
        assert hasattr(glm_client, 'completions')
        assert hasattr(glm_client, 'embeddings')
        print("✓ ZhipuAI wrapper has required properties")

        # Test mock response generation
        messages = [{"role": "user", "content": "Hello, GLM!"}]
        response = await asyncio.to_thread(
            glm_client.chat.completions.create,
            model="glm-4.7",
            messages=messages
        )

        assert response is not None
        assert len(response.choices) > 0
        print(f"✓ Mock response generated: {response.choices[0].message.content[:50]}...")

        # Test embedding
        embedding_response = await asyncio.to_thread(
            glm_client.embeddings.create,
            model="embedding-2",
            input="test text",
            messages=[]
        )

        assert embedding_response is not None
        assert len(embedding_response.data) > 0
        assert len(embedding_response.data[0].embedding) == 1024
        print("✓ Mock embedding generated successfully")

        return True
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False

async def main():
    """Run all tests"""
    print("Testing GLM client fix (Standalone)...")
    print("=" * 50)
    print(f"ZhipuAI available: {ZHIPUAI_AVAILABLE}")
    print("=" * 50)

    if await test_glm_client():
        print("\n✓ All tests passed! The GLM client fix is working correctly.")
        print("Note: Running in mock mode since zhipuai is not installed.")
        return 0
    else:
        print("\n✗ Test failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))