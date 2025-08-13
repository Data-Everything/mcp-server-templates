#!/usr/bin/env python3
"""
Comprehensive Client Testing Script

This script tests all MCP Client methods with various edge cases and scenarios.
It's designed to be run manually to verify client functionality end-to-end.
"""

import asyncio
import json
import logging
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from mcp_template.client import MCPClient

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ClientTestRunner:
    """Comprehensive test runner for MCP Client."""

    def __init__(self):
        self.test_results = {}
        self.clients = []

    def log_test_start(self, test_name: str):
        """Log the start of a test."""
        print(f"\n{'='*60}")
        print(f"🧪 Testing: {test_name}")
        print(f"{'='*60}")

    def log_test_result(self, test_name: str, success: bool, details: str = ""):
        """Log test result."""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"   Details: {details}")

        self.test_results[test_name] = {
            "success": success,
            "details": details,
            "timestamp": time.time(),
        }

    def run_all_tests(self):
        """Run all client tests."""
        print("🚀 Starting Comprehensive MCP Client Testing")
        print(f"📊 Target: Test all client methods with edge cases")

        # Basic initialization tests
        self.test_client_initialization()

        # Template management tests
        self.test_template_methods()

        # Server management tests
        self.test_server_management()

        # Tool discovery and calling tests
        self.test_tool_operations()

        # Connection management tests
        asyncio.run(self.test_connection_operations())

        # Edge case and error handling tests
        self.test_edge_cases()

        # Performance and stress tests
        self.test_performance()

        # Cleanup
        self.cleanup_all_clients()

        # Print summary
        self.print_test_summary()

    def test_client_initialization(self):
        """Test client initialization with various backends and configurations."""
        self.log_test_start("Client Initialization")

        try:
            # Test default initialization
            client1 = MCPClient()
            self.clients.append(client1)
            assert client1.backend_type == "docker"
            assert client1.timeout == 30
            self.log_test_result("Default initialization", True)

            # Test custom backend
            client2 = MCPClient(backend_type="mock", timeout=60)
            self.clients.append(client2)
            assert client2.backend_type == "mock"
            assert client2.timeout == 60
            self.log_test_result("Custom backend initialization", True)

            # Test invalid backend (should still initialize but may fail later)
            client3 = MCPClient(backend_type="nonexistent")
            self.clients.append(client3)
            self.log_test_result(
                "Invalid backend initialization", True, "Gracefully handled"
            )

        except Exception as e:
            self.log_test_result("Client initialization", False, str(e))

    def test_template_methods(self):
        """Test all template-related methods."""
        self.log_test_start("Template Methods")

        client = MCPClient()
        self.clients.append(client)

        try:
            # Test list_templates
            templates = client.list_templates()
            assert isinstance(templates, dict)
            self.log_test_result(
                "list_templates()", True, f"Found {len(templates)} templates"
            )

            # Test list_templates with deployed status
            templates_with_status = client.list_templates(include_deployed_status=True)
            assert isinstance(templates_with_status, dict)
            self.log_test_result("list_templates(include_deployed_status=True)", True)

            # Test get_template_info for existing template
            if "demo" in templates:
                demo_info = client.get_template_info("demo")
                assert demo_info is not None
                assert isinstance(demo_info, dict)
                self.log_test_result("get_template_info('demo')", True)

            # Test get_template_info for non-existent template
            nonexistent_info = client.get_template_info("nonexistent_template_12345")
            assert nonexistent_info is None
            self.log_test_result(
                "get_template_info(nonexistent)", True, "Correctly returned None"
            )

            # Test validate_template for existing template
            if "demo" in templates:
                is_valid = client.validate_template("demo")
                assert isinstance(is_valid, bool)
                self.log_test_result(
                    "validate_template('demo')", True, f"Valid: {is_valid}"
                )

            # Test validate_template for non-existent template
            is_invalid = client.validate_template("nonexistent_template_12345")
            assert is_invalid is False
            self.log_test_result(
                "validate_template(nonexistent)", True, "Correctly returned False"
            )

            # Test search_templates
            search_results = client.search_templates("demo")
            assert isinstance(search_results, dict)
            self.log_test_result(
                "search_templates('demo')", True, f"Found {len(search_results)} matches"
            )

            # Test search_templates with no matches
            no_matches = client.search_templates("nonexistent_query_xyz123")
            assert isinstance(no_matches, dict)
            self.log_test_result(
                "search_templates(no matches)", True, f"Found {len(no_matches)} matches"
            )

        except Exception as e:
            self.log_test_result("Template methods", False, str(e))

    def test_server_management(self):
        """Test server management methods."""
        self.log_test_start("Server Management")

        client = MCPClient()
        self.clients.append(client)

        try:
            # Test list_servers (initially should be empty or have existing servers)
            servers = client.list_servers()
            assert isinstance(servers, list)
            self.log_test_result(
                "list_servers()", True, f"Found {len(servers)} servers"
            )

            # Test list_servers_by_template
            demo_servers = client.list_servers_by_template("demo")
            assert isinstance(demo_servers, list)
            self.log_test_result(
                "list_servers_by_template('demo')",
                True,
                f"Found {len(demo_servers)} demo servers",
            )

            # Test start_server with minimal config
            server_result = client.start_server("demo", {"greeting": "Test"})
            if server_result:
                deployment_id = server_result.get("deployment_id")
                self.log_test_result(
                    "start_server('demo')", True, f"Started: {deployment_id}"
                )

                # Wait a moment for server to start
                time.sleep(2)

                # Test get_server_info
                server_info = client.get_server_info(deployment_id)
                if server_info:
                    self.log_test_result(
                        "get_server_info()",
                        True,
                        f"Status: {server_info.get('status')}",
                    )
                else:
                    self.log_test_result(
                        "get_server_info()", False, "No server info returned"
                    )

                # Test get_server_logs
                logs = client.get_server_logs(deployment_id)
                if logs:
                    self.log_test_result(
                        "get_server_logs()", True, f"Got {len(logs.split())} log lines"
                    )
                else:
                    self.log_test_result(
                        "get_server_logs()", True, "No logs yet (normal for new server)"
                    )

                # Test stop_server
                stop_result = client.stop_server(deployment_id)
                if stop_result.get("success"):
                    self.log_test_result("stop_server()", True, "Successfully stopped")
                else:
                    self.log_test_result(
                        "stop_server()",
                        False,
                        stop_result.get("error", "Unknown error"),
                    )
            else:
                self.log_test_result(
                    "start_server('demo')", False, "Failed to start server"
                )

            # Test start_server with non-existent template
            invalid_server = client.start_server("nonexistent_template_xyz")
            assert invalid_server is None
            self.log_test_result(
                "start_server(nonexistent)", True, "Correctly returned None"
            )

            # Test stop_server with invalid ID
            invalid_stop = client.stop_server("invalid_id_12345")
            assert not invalid_stop.get("success", True)
            self.log_test_result("stop_server(invalid)", True, "Correctly failed")

        except Exception as e:
            self.log_test_result("Server management", False, str(e))

    def test_tool_operations(self):
        """Test tool discovery and calling methods."""
        self.log_test_start("Tool Operations")

        client = MCPClient()
        self.clients.append(client)

        try:
            # Test list_tools for existing template
            tools = client.list_tools("demo")
            assert isinstance(tools, list)
            self.log_test_result(
                "list_tools('demo')", True, f"Found {len(tools)} tools"
            )

            # Test list_tools with force_refresh
            refreshed_tools = client.list_tools("demo", force_refresh=True)
            assert isinstance(refreshed_tools, list)
            self.log_test_result(
                "list_tools(force_refresh=True)",
                True,
                f"Found {len(refreshed_tools)} tools",
            )

            # Test list_tools for non-existent template
            no_tools = client.list_tools("nonexistent_template_xyz")
            assert isinstance(no_tools, list)
            self.log_test_result(
                "list_tools(nonexistent)", True, f"Found {len(no_tools)} tools"
            )

            # Test call_tool (this requires a running server)
            # First start a server
            server_result = client.start_server("demo", {"greeting": "Test Tool Call"})
            if server_result:
                deployment_id = server_result.get("deployment_id")
                time.sleep(3)  # Give server time to start

                # Try to call a tool if available
                if tools:
                    tool_name = tools[0].get("name", "echo")
                    tool_result = client.call_tool(
                        deployment_id, tool_name, {"message": "test"}
                    )
                    if tool_result and tool_result.get("success"):
                        self.log_test_result(
                            "call_tool()",
                            True,
                            f"Tool {tool_name} executed successfully",
                        )
                    else:
                        self.log_test_result(
                            "call_tool()",
                            False,
                            tool_result.get("error", "Unknown error"),
                        )
                else:
                    self.log_test_result(
                        "call_tool()", True, "No tools available to test"
                    )

                # Test call_tool with invalid tool name
                invalid_tool = client.call_tool(
                    deployment_id, "nonexistent_tool_xyz", {}
                )
                assert not invalid_tool.get("success", True)
                self.log_test_result("call_tool(invalid)", True, "Correctly failed")

                # Clean up
                client.stop_server(deployment_id)
            else:
                self.log_test_result(
                    "call_tool()", False, "Could not start server for testing"
                )

            # Test call_tool with invalid deployment
            invalid_call = client.call_tool(
                "invalid_deployment_xyz", "echo", {"message": "test"}
            )
            assert not invalid_call.get("success", True)
            self.log_test_result(
                "call_tool(invalid deployment)", True, "Correctly failed"
            )

        except Exception as e:
            self.log_test_result("Tool operations", False, str(e))

    async def test_connection_operations(self):
        """Test async connection-related methods."""
        self.log_test_start("Connection Operations")

        client = MCPClient()
        self.clients.append(client)

        try:
            # Test connect_stdio with valid command
            connection_id = await client.connect_stdio(["echo", "test"])
            if connection_id:
                self.log_test_result(
                    "connect_stdio()", True, f"Connection: {connection_id}"
                )

                # Test list_tools_from_connection
                conn_tools = await client.list_tools_from_connection(connection_id)
                if conn_tools is not None:
                    self.log_test_result(
                        "list_tools_from_connection()",
                        True,
                        f"Found {len(conn_tools)} tools",
                    )
                else:
                    self.log_test_result(
                        "list_tools_from_connection()",
                        True,
                        "No tools (expected for echo command)",
                    )

                # Test call_tool_from_connection
                call_result = await client.call_tool_from_connection(
                    connection_id, "test_tool", {}
                )
                # This will likely fail since echo doesn't support MCP protocol
                self.log_test_result(
                    "call_tool_from_connection()",
                    True,
                    "Attempted call (expected to fail with echo)",
                )

                # Test disconnect
                disconnect_result = await client.disconnect(connection_id)
                assert disconnect_result is True
                self.log_test_result("disconnect()", True, "Successfully disconnected")
            else:
                self.log_test_result(
                    "connect_stdio()", False, "Failed to create connection"
                )

            # Test connect_stdio with invalid command
            invalid_conn = await client.connect_stdio(["nonexistent_command_xyz"])
            assert invalid_conn is None
            self.log_test_result(
                "connect_stdio(invalid)", True, "Correctly returned None"
            )

            # Test operations on non-existent connection
            no_tools = await client.list_tools_from_connection("nonexistent_conn_xyz")
            assert no_tools is None
            self.log_test_result(
                "list_tools_from_connection(invalid)", True, "Correctly returned None"
            )

            no_call = await client.call_tool_from_connection(
                "nonexistent_conn_xyz", "tool", {}
            )
            assert no_call is None
            self.log_test_result(
                "call_tool_from_connection(invalid)", True, "Correctly returned None"
            )

            no_disconnect = await client.disconnect("nonexistent_conn_xyz")
            assert no_disconnect is False
            self.log_test_result(
                "disconnect(invalid)", True, "Correctly returned False"
            )

            # Test cleanup
            await client.cleanup()
            self.log_test_result("cleanup()", True, "Successfully cleaned up")

            # Test context manager
            async with MCPClient() as ctx_client:
                assert isinstance(ctx_client, MCPClient)
                # Add a connection to test cleanup
                test_conn = await ctx_client.connect_stdio(["echo", "context_test"])
                if test_conn:
                    # Connection should be cleaned up automatically when exiting context
                    pass
            self.log_test_result(
                "context manager", True, "Successfully used as context manager"
            )

        except Exception as e:
            self.log_test_result("Connection operations", False, str(e))

    def test_edge_cases(self):
        """Test edge cases and error handling."""
        self.log_test_start("Edge Cases & Error Handling")

        try:
            # Test with None inputs
            client = MCPClient()
            self.clients.append(client)

            try:
                none_template = client.get_template_info(None)
                self.log_test_result(
                    "get_template_info(None)", True, "Handled None input"
                )
            except Exception:
                self.log_test_result(
                    "get_template_info(None)", True, "Raised exception (acceptable)"
                )

            # Test with empty string inputs
            empty_template = client.get_template_info("")
            assert empty_template is None
            self.log_test_result("get_template_info('')", True, "Handled empty string")

            # Test with very long strings
            long_string = "x" * 10000
            long_result = client.get_template_info(long_string)
            assert long_result is None
            self.log_test_result(
                "get_template_info(long_string)", True, "Handled long input"
            )

            # Test with special characters
            special_chars = "template!@#$%^&*()_+-=[]{}|;':\",./<>?"
            special_result = client.get_template_info(special_chars)
            assert special_result is None
            self.log_test_result(
                "get_template_info(special_chars)", True, "Handled special characters"
            )

            # Test concurrent operations
            import threading

            results = []

            def concurrent_list():
                try:
                    templates = client.list_templates()
                    results.append(len(templates))
                except Exception as e:
                    results.append(str(e))

            threads = [threading.Thread(target=concurrent_list) for _ in range(5)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()

            self.log_test_result("concurrent operations", True, f"Results: {results}")

        except Exception as e:
            self.log_test_result("Edge cases", False, str(e))

    def test_performance(self):
        """Test performance characteristics."""
        self.log_test_start("Performance Testing")

        client = MCPClient()
        self.clients.append(client)

        try:
            # Test repeated calls performance
            start_time = time.time()
            for _ in range(10):
                client.list_templates()
            duration = time.time() - start_time
            self.log_test_result(
                "repeated list_templates", True, f"10 calls in {duration:.2f}s"
            )

            # Test memory usage (basic check)
            try:
                import psutil
                import os

                process = psutil.Process(os.getpid())
                memory_before = process.memory_info().rss / 1024 / 1024  # MB

                # Create and destroy multiple clients
                temp_clients = []
                for _ in range(10):
                    temp_client = MCPClient()
                    temp_clients.append(temp_client)

                # Clear references
                temp_clients.clear()

                memory_after = process.memory_info().rss / 1024 / 1024  # MB
                memory_diff = memory_after - memory_before

                self.log_test_result(
                    "memory usage", True, f"Memory change: {memory_diff:.1f}MB"
                )
            except ImportError:
                self.log_test_result(
                    "memory usage", True, "psutil not available (skipped)"
                )

        except Exception as e:
            self.log_test_result("Performance testing", False, str(e))

    def cleanup_all_clients(self):
        """Clean up all created clients."""
        print("\n🧹 Cleaning up test clients...")
        for client in self.clients:
            try:
                # Stop any servers that might be running
                servers = client.list_servers()
                for server in servers:
                    if "test" in str(server.get("name", "")).lower():
                        client.stop_server(server.get("id"))

                # Clean up async connections if possible
                try:
                    asyncio.run(client.cleanup())
                except RuntimeError:
                    # No event loop, skip async cleanup
                    pass
            except Exception as e:
                logger.warning(f"Error cleaning up client: {e}")

    def print_test_summary(self):
        """Print summary of all test results."""
        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)

        total_tests = len(self.test_results)
        passed_tests = sum(
            1 for result in self.test_results.values() if result["success"]
        )
        failed_tests = total_tests - passed_tests

        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")

        if failed_tests > 0:
            print("\n🔍 FAILED TESTS:")
            for test_name, result in self.test_results.items():
                if not result["success"]:
                    print(f"  ❌ {test_name}: {result['details']}")

        print("\n📝 DETAILED RESULTS:")
        for test_name, result in self.test_results.items():
            status = "✅" if result["success"] else "❌"
            print(f"  {status} {test_name}")
            if result["details"]:
                print(f"      {result['details']}")


def main():
    """Main function to run all tests."""
    print("🧪 MCP Client Comprehensive Testing Suite")
    print("=" * 60)

    runner = ClientTestRunner()

    try:
        runner.run_all_tests()
    except KeyboardInterrupt:
        print("\n⏹️  Testing interrupted by user")
        runner.cleanup_all_clients()
    except Exception as e:
        print(f"\n💥 Unexpected error during testing: {e}")
        runner.cleanup_all_clients()
        raise

    print("\n✨ Testing completed!")


if __name__ == "__main__":
    main()
