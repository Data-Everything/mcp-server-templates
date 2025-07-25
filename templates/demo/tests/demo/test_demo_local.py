#!/usr/bin/env python3
"""
Simple test client for the demo server
"""

import asyncio
import json
import subprocess
import sys


async def test_demo_server():
    """Test the demo server by starting it as a subprocess and sending MCP messages."""

    # Start the server process
    process = subprocess.Popen(
        ["python", "main.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd="/home/sam/data-everything/mcp-platform/mcp-server-templates/templates/demo",
    )

    try:
        # Send initialization request
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"roots": {"listChanged": True}, "sampling": {}},
                "clientInfo": {"name": "test-client", "version": "1.0.0"},
            },
        }

        print("🧪 Testing demo server...")
        print("📤 Sending initialization request...")

        # Send the request
        process.stdin.write(json.dumps(init_request) + "\n")
        process.stdin.flush()

        # Read the response
        response_line = process.stdout.readline()
        if response_line:
            try:
                response = json.loads(response_line.strip())
                print("📥 Received response:")
                print(json.dumps(response, indent=2))

                if "result" in response:
                    print("✅ Server initialized successfully!")

                    # Send a tools list request
                    tools_request = {
                        "jsonrpc": "2.0",
                        "id": 2,
                        "method": "tools/list",
                        "params": {},
                    }

                    print("\n📤 Requesting tools list...")
                    process.stdin.write(json.dumps(tools_request) + "\n")
                    process.stdin.flush()

                    # Read tools response
                    tools_response_line = process.stdout.readline()
                    if tools_response_line:
                        tools_response = json.loads(tools_response_line.strip())
                        print("📥 Tools response:")
                        print(json.dumps(tools_response, indent=2))

                        if (
                            "result" in tools_response
                            and "tools" in tools_response["result"]
                        ):
                            tools = tools_response["result"]["tools"]
                            print(f"\n🔧 Found {len(tools)} tools:")
                            for tool in tools:
                                print(f"  • {tool['name']}: {tool['description']}")

                            # Test the say_hello tool
                            if any(tool["name"] == "say_hello" for tool in tools):
                                print("\n📤 Testing say_hello tool...")
                                tool_call = {
                                    "jsonrpc": "2.0",
                                    "id": 3,
                                    "method": "tools/call",
                                    "params": {
                                        "name": "say_hello",
                                        "arguments": {"name": "Test User"},
                                    },
                                }

                                process.stdin.write(json.dumps(tool_call) + "\n")
                                process.stdin.flush()

                                # Read tool response
                                tool_response_line = process.stdout.readline()
                                if tool_response_line:
                                    tool_response = json.loads(
                                        tool_response_line.strip()
                                    )
                                    print("📥 Tool response:")
                                    print(json.dumps(tool_response, indent=2))

                                    if "result" in tool_response:
                                        print("✅ Tool call successful!")
                                        print(
                                            f"🎉 Result: {tool_response['result']['content'][0]['text']}"
                                        )
                                    else:
                                        print("❌ Tool call failed")
                                else:
                                    print("❌ No tool response received")
                            else:
                                print("⚠️ say_hello tool not found")
                        else:
                            print("❌ No tools found in response")
                    else:
                        print("❌ No tools response received")
                else:
                    print("❌ Initialization failed")
                    print(f"Error: {response}")
            except json.JSONDecodeError as e:
                print(f"❌ Failed to parse JSON response: {e}")
                print(f"Raw response: {response_line}")
        else:
            print("❌ No response received from server")

    except Exception as e:
        print(f"❌ Test failed: {e}")
    finally:
        # Clean up
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()


if __name__ == "__main__":
    asyncio.run(test_demo_server())
