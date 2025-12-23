#!/usr/bin/env python3
"""
Test script for GLM client fix
"""

import sys
import os

# Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_glm_client_import():
    """Test if GLM client can be imported without errors"""
    try:
        from ai_clients.glm_client import GLMClient, ZhipuAI
        print("✓ GLM client imports successfully")
        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False

def test_glm_client_initialization():
    """Test if GLM client can be initialized"""
    try:
        from ai_clients.glm_client import GLMClient
        client = GLMClient()
        print("✓ GLM client initializes successfully")
        return True
    except Exception as e:
        print(f"✗ Initialization error: {e}")
        return False

def test_zhipuai_wrapper():
    """Test if ZhipuAI wrapper works"""
    try:
        from ai_clients.glm_client import ZhipuAI

        # Test initialization
        client = ZhipuAI(api_key="test_key")
        print("✓ ZhipuAI wrapper initializes successfully")

        # Test properties
        assert hasattr(client, 'chat')
        assert hasattr(client, 'completions')
        assert hasattr(client, 'embeddings')
        print("✓ ZhipuAI wrapper has required properties")

        return True
    except Exception as e:
        print(f"✗ ZhipuAI wrapper error: {e}")
        return False

def main():
    """Run all tests"""
    print("Testing GLM client fix...")
    print("=" * 50)

    tests = [
        ("Import Test", test_glm_client_import),
        ("Initialization Test", test_glm_client_initialization),
        ("ZhipuAI Wrapper Test", test_zhipuai_wrapper),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        if test_func():
            passed += 1
        else:
            print(f"  Failed!")

    print("\n" + "=" * 50)
    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print("✓ All tests passed! The GLM client fix is working correctly.")
        return 0
    else:
        print("✗ Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())