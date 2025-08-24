"""
Test Visual Formatting Utilities.

This module tests the visual formatting functions used for displaying
multi-backend information in CLI output.
"""

import datetime

import pytest

from mcp_template.core.response_formatter import (
    format_deployment_summary,
    format_timestamp,
    get_backend_color,
    get_backend_icon,
    get_backend_indicator,
    get_status_color,
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

    def test_backend_indicators_case_sensitivity(self):
        """Test that backend indicators work with different cases."""
        # Test uppercase
        assert get_backend_color("DOCKER") == "dim"  # Should default to dim for unknown
        assert get_backend_color("docker") == "blue"

        # Test mixed case
        assert get_backend_color("Docker") == "dim"
        assert get_backend_color("docker") == "blue"
