"""
Test Visual Formatting Utilities.

This module tests the visual formatting functions used for displaying
multi-backend information in CLI output.
"""

import datetime
from unittest.mock import patch

import pytest

from mcp_template.core.response_formatter import (
    MultiBackendProgressTracker,
    format_deployment_summary,
    format_timestamp,
    get_backend_color,
    get_backend_icon,
    get_backend_indicator,
    get_status_color,
    render_backend_health_status,
    render_deployments_grouped_by_backend,
    render_deployments_unified_table,
    render_tools_with_sources,
)

pytestmark = pytest.mark.unit


class TestBackendIndicators:
    """Test backend visual indicator functions."""

    def test_get_backend_color(self):
        """Test backend color mapping."""
        assert get_backend_color("docker") == "blue"
        assert get_backend_color("kubernetes") == "green"
        assert get_backend_color("mock") == "yellow"
        assert get_backend_color("unknown") == "dim"
        assert get_backend_color("invalid") == "dim"

    def test_get_backend_icon(self):
        """Test backend icon mapping."""
        assert get_backend_icon("docker") == "🐳"
        assert get_backend_icon("kubernetes") == "☸️"
        assert get_backend_icon("mock") == "🔧"
        assert get_backend_icon("unknown") == "❓"
        assert get_backend_icon("invalid") == "❓"

    def test_get_status_color(self):
        """Test status color mapping."""
        assert get_status_color("running") == "green"
        assert get_status_color("stopped") == "red"
        assert get_status_color("starting") == "yellow"
        assert get_status_color("error") == "bright_red"
        assert get_status_color("unknown") == "dim"
        assert get_status_color("RUNNING") == "green"  # Case insensitive
        assert get_status_color(None) == "dim"

    def test_get_backend_indicator(self):
        """Test backend indicator formatting."""
        indicator = get_backend_indicator("docker")
        assert "🐳" in indicator
        assert "DOCKER" in indicator
        assert "[blue]" in indicator

        indicator_no_icon = get_backend_indicator("kubernetes", include_icon=False)
        assert "☸️" not in indicator_no_icon
        assert "KUBERNETES" in indicator_no_icon
        assert "[green]" in indicator_no_icon


class TestTimestampFormatting:
    """Test timestamp formatting functionality."""

    def test_format_timestamp_none(self):
        """Test formatting None timestamp."""
        assert format_timestamp(None) == "N/A"

    def test_format_timestamp_string_iso(self):
        """Test formatting ISO string timestamp."""
        timestamp = "2024-01-01T10:00:00Z"
        result = format_timestamp(timestamp)
        # Should return a relative time or absolute date
        assert result != "N/A"
        assert len(result) > 0

    def test_format_timestamp_string_invalid(self):
        """Test formatting invalid string timestamp."""
        timestamp = "invalid-timestamp"
        result = format_timestamp(timestamp)
        assert result == "invalid-timestamp"

    def test_format_timestamp_datetime_recent(self):
        """Test formatting recent datetime object."""
        now = datetime.datetime.now()
        recent = now - datetime.timedelta(minutes=5)
        result = format_timestamp(recent)
        assert "m ago" in result or "just now" in result

    def test_format_timestamp_datetime_hours_ago(self):
        """Test formatting datetime from hours ago."""
        now = datetime.datetime.now()
        hours_ago = now - datetime.timedelta(hours=3)
        result = format_timestamp(hours_ago)
        assert "h ago" in result

    def test_format_timestamp_datetime_days_ago(self):
        """Test formatting datetime from days ago."""
        now = datetime.datetime.now()
        days_ago = now - datetime.timedelta(days=2)
        result = format_timestamp(days_ago)
        assert "d ago" in result

    def test_format_timestamp_datetime_old(self):
        """Test formatting old datetime."""
        old_date = datetime.datetime(2023, 1, 1, 10, 0, 0)
        result = format_timestamp(old_date)
        assert "2023-01-01" in result


class TestDeploymentSummary:
    """Test deployment summary formatting."""

    def test_format_deployment_summary_empty(self):
        """Test summary with no deployments."""
        result = format_deployment_summary([])
        assert result == "No deployments"

    def test_format_deployment_summary_single_backend(self):
        """Test summary with deployments from single backend."""
        deployments = [
            {"id": "test-1", "status": "running", "backend_type": "docker"},
            {"id": "test-2", "status": "running", "backend_type": "docker"},
        ]
        result = format_deployment_summary(deployments)
        assert "2 total" in result
        # No status breakdown for single status, no backend breakdown for single backend
        assert result == "2 total"

    def test_format_deployment_summary_multiple_backends(self):
        """Test summary with deployments from multiple backends."""
        deployments = [
            {"id": "test-1", "status": "running", "backend_type": "docker"},
            {"id": "test-2", "status": "stopped", "backend_type": "docker"},
            {"id": "test-3", "status": "running", "backend_type": "kubernetes"},
        ]
        result = format_deployment_summary(deployments)
        assert "3 total" in result
        assert "2 running" in result
        assert "2 docker" in result
        assert "1 kubernetes" in result

    def test_format_deployment_summary_mixed_statuses(self):
        """Test summary with mixed deployment statuses."""
        deployments = [
            {"id": "test-1", "status": "running", "backend_type": "docker"},
            {"id": "test-2", "status": "stopped", "backend_type": "docker"},
            {"id": "test-3", "status": "error", "backend_type": "docker"},
        ]
        result = format_deployment_summary(deployments)
        assert "3 total" in result
        assert "1 running" in result


class TestRenderFunctions:
    """Test rendering functions (mocked console output)."""

    @patch("mcp_template.core.response_formatter.console")
    def test_render_deployments_grouped_by_backend(self, mock_console):
        """Test grouped deployments rendering."""
        deployments = {
            "docker": [
                {
                    "id": "docker-123",
                    "template": "demo",
                    "status": "running",
                    "created_at": "2024-01-01T10:00:00Z",
                    "transport": "http",
                }
            ],
            "kubernetes": [
                {
                    "id": "k8s-456",
                    "template": "github",
                    "status": "stopped",
                    "created_at": "2024-01-01T11:00:00Z",
                    "transport": "stdio",
                }
            ],
        }

        render_deployments_grouped_by_backend(deployments)

        # Verify console.print was called (indicating rendering occurred)
        assert mock_console.print.call_count > 0

        # Check that backend indicators were printed
        print_calls = [
            call[0][0] for call in mock_console.print.call_args_list if call[0]
        ]
        backend_indicators = [
            call
            for call in print_calls
            if "DOCKER" in str(call) or "KUBERNETES" in str(call)
        ]
        assert len(backend_indicators) > 0

    @patch("mcp_template.core.response_formatter.console")
    def test_render_deployments_grouped_empty(self, mock_console):
        """Test grouped rendering with no deployments."""
        render_deployments_grouped_by_backend({})

        # Should print "No deployments found"
        print_calls = [str(call) for call in mock_console.print.call_args_list]
        no_deployments_calls = [
            call for call in print_calls if "No deployments found" in call
        ]
        assert len(no_deployments_calls) > 0

    @patch("mcp_template.core.response_formatter.console")
    def test_render_deployments_grouped_show_empty(self, mock_console):
        """Test grouped rendering with show_empty=True."""
        deployments = {"docker": []}

        render_deployments_grouped_by_backend(deployments, show_empty=True)

        # Should show docker backend with no deployments
        print_calls = [str(call) for call in mock_console.print.call_args_list]
        docker_calls = [call for call in print_calls if "DOCKER" in call]
        assert len(docker_calls) > 0

    @patch("mcp_template.core.response_formatter.console")
    def test_render_deployments_unified_table(self, mock_console):
        """Test unified table rendering."""
        deployments = [
            {
                "id": "docker-123",
                "template": "demo",
                "status": "running",
                "created_at": "2024-01-01T10:00:00Z",
                "transport": "http",
                "backend_type": "docker",
            },
            {
                "id": "k8s-456",
                "template": "github",
                "status": "stopped",
                "created_at": "2024-01-01T11:00:00Z",
                "transport": "stdio",
                "backend_type": "kubernetes",
            },
        ]

        render_deployments_unified_table(deployments)

        # Verify console.print was called with table
        assert mock_console.print.call_count > 0

    @patch("mcp_template.core.response_formatter.console")
    def test_render_deployments_unified_empty(self, mock_console):
        """Test unified table rendering with no deployments."""
        render_deployments_unified_table([])

        # Should print "No deployments found"
        print_calls = [str(call) for call in mock_console.print.call_args_list]
        no_deployments_calls = [
            call for call in print_calls if "No deployments found" in call
        ]
        assert len(no_deployments_calls) > 0

    @patch("mcp_template.core.response_formatter.console")
    def test_render_tools_with_sources(self, mock_console):
        """Test tools rendering with multiple sources."""
        tools_data = {
            "static_tools": {
                "demo": {
                    "tools": [
                        {"name": "echo", "description": "Echo a message"},
                        {"name": "greet", "description": "Greet someone"},
                    ],
                    "source": "template_definition",
                }
            },
            "dynamic_tools": {
                "docker": [
                    {
                        "name": "echo",
                        "description": "Echo a message",
                        "deployment_id": "docker-123",
                        "template": "demo",
                        "backend": "docker",
                    }
                ]
            },
            "backend_summary": {"docker": {"tool_count": 1, "deployment_count": 1}},
        }

        render_tools_with_sources(tools_data)

        # Verify console.print was called multiple times (summary, static, dynamic sections)
        assert mock_console.print.call_count > 5

        # Check for key sections in output
        print_calls = [str(call) for call in mock_console.print.call_args_list]
        summary_calls = [
            call for call in print_calls if "Tool Discovery Summary" in call
        ]
        static_calls = [call for call in print_calls if "Static Tools" in call]
        dynamic_calls = [call for call in print_calls if "Dynamic Tools" in call]

        assert len(summary_calls) > 0
        assert len(static_calls) > 0
        assert len(dynamic_calls) > 0

    @patch("mcp_template.core.response_formatter.console")
    def test_render_tools_with_sources_empty(self, mock_console):
        """Test tools rendering with no tools."""
        tools_data = {"static_tools": {}, "dynamic_tools": {}, "backend_summary": {}}

        render_tools_with_sources(tools_data)

        # Should show summary and "No tools found"
        print_calls = [str(call) for call in mock_console.print.call_args_list]
        no_tools_calls = [call for call in print_calls if "No tools found" in call]
        assert len(no_tools_calls) > 0

    @patch("mcp_template.core.response_formatter.console")
    def test_render_backend_health_status(self, mock_console):
        """Test backend health status rendering."""
        health_data = {
            "docker": {"status": "healthy", "deployment_count": 2, "error": None},
            "kubernetes": {"status": "healthy", "deployment_count": 1, "error": None},
            "mock": {
                "status": "unhealthy",
                "deployment_count": 0,
                "error": "Connection failed",
            },
        }

        render_backend_health_status(health_data)

        # Verify console.print was called
        assert mock_console.print.call_count > 0

        # Check for health status header
        print_calls = [str(call) for call in mock_console.print.call_args_list]
        header_calls = [call for call in print_calls if "Backend Health Status" in call]
        assert len(header_calls) > 0

    @patch("mcp_template.core.response_formatter.console")
    def test_render_backend_health_status_empty(self, mock_console):
        """Test backend health status rendering with no data."""
        render_backend_health_status({})

        # Should show "No backend health data available"
        print_calls = [str(call) for call in mock_console.print.call_args_list]
        no_data_calls = [
            call for call in print_calls if "No backend health data available" in call
        ]
        assert len(no_data_calls) > 0


class TestMultiBackendProgressTracker:
    """Test multi-backend progress tracking."""

    @patch("mcp_template.core.response_formatter.console")
    def test_progress_tracker_basic_flow(self, mock_console):
        """Test basic progress tracking flow."""
        tracker = MultiBackendProgressTracker(["docker", "kubernetes"])

        # Start first backend
        tracker.start_backend("docker")

        # Finish first backend successfully
        tracker.finish_backend("docker", success=True, message="Completed successfully")

        # Start second backend
        tracker.start_backend("kubernetes")

        # Finish second backend with failure
        tracker.finish_backend("kubernetes", success=False, message="Connection failed")

        # Get summary
        summary = tracker.get_summary()

        # Verify progress messages were printed
        assert (
            mock_console.print.call_count >= 4
        )  # At least start/finish for each backend

        # Check summary content
        assert "1/2 backends successful" in summary
        assert "1 failed" in summary

    @patch("mcp_template.core.response_formatter.console")
    def test_progress_tracker_all_success(self, mock_console):
        """Test progress tracking with all successes."""
        tracker = MultiBackendProgressTracker(["docker", "kubernetes", "mock"])

        for backend in ["docker", "kubernetes", "mock"]:
            tracker.start_backend(backend)
            tracker.finish_backend(backend, success=True, message="Success")

        summary = tracker.get_summary()
        assert "All 3 backends completed successfully" in summary

    @patch("mcp_template.core.response_formatter.console")
    def test_progress_tracker_all_failure(self, mock_console):
        """Test progress tracking with all failures."""
        tracker = MultiBackendProgressTracker(["docker", "kubernetes"])

        for backend in ["docker", "kubernetes"]:
            tracker.start_backend(backend)
            tracker.finish_backend(backend, success=False, message="Failed")

        summary = tracker.get_summary()
        assert "All 2 backends failed" in summary

    def test_progress_tracker_results_storage(self):
        """Test that progress tracker stores results correctly."""
        tracker = MultiBackendProgressTracker(["docker"])

        tracker.start_backend("docker")
        tracker.finish_backend("docker", success=True, message="Test message")

        assert "docker" in tracker.results
        assert tracker.results["docker"]["success"] is True
        assert tracker.results["docker"]["message"] == "Test message"


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_format_timestamp_string_truncation(self):
        """Test timestamp string truncation for long strings."""
        long_timestamp = "2024-01-01T10:00:00.123456789Z-very-long-suffix"
        result = format_timestamp(long_timestamp)
        # Should be truncated to 19 characters
        assert len(result) <= 19

    def test_get_backend_indicator_empty_string(self):
        """Test backend indicator with empty string."""
        indicator = get_backend_indicator("")
        assert "UNKNOWN" in indicator or "❓" in indicator

    def test_format_deployment_summary_missing_fields(self):
        """Test deployment summary with missing fields."""
        deployments = [
            {"id": "test-1"},  # Missing status and backend_type
            {"status": "running"},  # Missing backend_type
            {"backend_type": "docker"},  # Missing status
        ]
        result = format_deployment_summary(deployments)
        assert "3 total" in result
        # Should handle missing fields gracefully

    @patch("mcp_template.core.response_formatter.console")
    def test_render_tools_long_descriptions(self, mock_console):
        """Test tools rendering with very long descriptions."""
        tools_data = {
            "static_tools": {
                "demo": {
                    "tools": [
                        {
                            "name": "test_tool",
                            "description": "This is a very long description that should be truncated because it exceeds the reasonable length limit for display in the table",
                        }
                    ],
                    "source": "template_definition",
                }
            },
            "dynamic_tools": {},
            "backend_summary": {},
        }

        render_tools_with_sources(tools_data)

        # Should not raise any errors and should call console.print
        assert mock_console.print.call_count > 0

    def test_backend_indicators_case_sensitivity(self):
        """Test that backend indicators work with different cases."""
        # Test uppercase
        assert get_backend_color("DOCKER") == "dim"  # Should default to dim for unknown
        assert get_backend_color("docker") == "blue"

        # Test mixed case
        assert get_backend_color("Docker") == "dim"
        assert get_backend_color("docker") == "blue"
