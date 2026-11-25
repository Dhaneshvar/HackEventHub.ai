#!/usr/bin/env python3
"""Athena contract test -- exercises: simple chat, tool call, JSON output.

TODO: This is a skeleton. Update once the Athena API documentation is provided.
Currently it assumes an OpenAI-compatible chat/completions endpoint.
"""

import asyncio
import json
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.providers.athena import AthenaProvider
from app.providers.base import ChatMessage


async def test_simple_chat(provider: AthenaProvider) -> bool:
    """Test 1: Simple chat completion."""
    print("\n--- Test 1: Simple Chat ---")
    try:
        result = await provider.chat(
            [ChatMessage(role="user", content="Say 'hello world'")],
            max_tokens=50,
        )
        print(f"  Response: {result.content}")
        print(f"  Finish reason: {result.finish_reason}")
        print(f"  Usage: {result.usage}")
        print("  PASS")
        return True
    except Exception as e:
        print(f"  FAIL: {e}")
        return False


async def test_json_output(provider: AthenaProvider) -> bool:
    """Test 2: JSON-formatted output."""
    print("\n--- Test 2: JSON Output ---")
    try:
        result = await provider.chat(
            [
                ChatMessage(
                    role="user",
                    content='Return a JSON object with keys "name" and "type". '
                    'Example: {"name": "test", "type": "demo"}',
                )
            ],
            response_format={"type": "json_object"},
            max_tokens=100,
        )
        print(f"  Response: {result.content}")
        # Try to parse as JSON
        parsed = json.loads(result.content)
        print(f"  Parsed JSON: {parsed}")
        print("  PASS")
        return True
    except json.JSONDecodeError:
        print(f"  FAIL: Response is not valid JSON: {result.content}")
        return False
    except Exception as e:
        print(f"  FAIL: {e}")
        return False


async def test_tool_calling(provider: AthenaProvider) -> bool:
    """Test 3: Tool/function calling (may not be supported)."""
    print("\n--- Test 3: Tool Calling ---")
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get weather for a city",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "city": {"type": "string", "description": "City name"},
                    },
                    "required": ["city"],
                },
            },
        }
    ]
    try:
        result = await provider.chat(
            [ChatMessage(role="user", content="What is the weather in Tokyo?")],
            tools=tools,
            max_tokens=100,
        )
        if result.tool_calls:
            print(f"  Tool calls: {result.tool_calls}")
            print("  PASS (tool calling supported)")
        else:
            print(f"  Response (no tool call): {result.content}")
            print("  PARTIAL: Tool calling may not be supported")
        return True
    except Exception as e:
        print(f"  FAIL: {e}")
        return False


async def main():
    print("=" * 60)
    print("Athena EA Contract Test")
    print("=" * 60)

    base_url = os.environ.get("ATHENA_BASE_URL", "")
    api_key = os.environ.get("ATHENA_API_KEY", "")
    model = os.environ.get("ATHENA_MODEL", "default")

    if not base_url:
        print("\nATHENA_BASE_URL is not set. Set it in .env or as an env var.")
        print("Skipping tests.")
        sys.exit(0)

    print(f"\nBase URL: {base_url}")
    print(f"Model: {model}")
    print(f"API Key: {'configured' if api_key else 'NOT SET'}")

    provider = AthenaProvider(base_url=base_url, api_key=api_key, model=model)

    # Connection test
    print("\n--- Connection Test ---")
    conn_result = await provider.test_connection()
    print(f"  Result: {conn_result}")

    if not conn_result.get("ok"):
        print("\nConnection failed. Stopping.")
        sys.exit(1)

    # Run contract tests
    results = {
        "simple_chat": await test_simple_chat(provider),
        "json_output": await test_json_output(provider),
        "tool_calling": await test_tool_calling(provider),
    }

    print("\n" + "=" * 60)
    print("Summary:")
    for test_name, passed in results.items():
        status = "PASS" if passed else "FAIL"
        print(f"  {test_name}: {status}")

    all_passed = all(results.values())
    print(f"\nOverall: {'ALL PASSED' if all_passed else 'SOME FAILED'}")
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    asyncio.run(main())
