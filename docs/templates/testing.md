# Testing Templates

**Comprehensive testing strategies for MCP server templates including unit testing, integration testing, and deployment validation with professional CI/CD practices.**

## Testing Philosophy

Professional MCP template testing follows a multi-layered approach:

1. **Unit Testing**: Test individual functions and methods in isolation
2. **Integration Testing**: Test component interactions and external dependencies
3. **End-to-End Testing**: Test complete workflows from user perspective
4. **Deployment Testing**: Validate templates in real deployment environments
5. **Performance Testing**: Verify scalability and resource usage
6. **Security Testing**: Validate input handling and access controls

## Test Environment Setup

### Development Environment

```bash
# Install test dependencies
pip install -r requirements-dev.txt

# Dependencies include:
# - pytest (testing framework)
# - pytest-asyncio (async test support)
# - pytest-cov (coverage reporting)
# - pytest-mock (mocking utilities)
# - responses (HTTP request mocking)
# - faker (test data generation)
# - testcontainers (containerized testing)
```

### Test Configuration

*pytest.ini*
```ini
[tool:pytest]
asyncio_mode = auto
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
markers =
    unit: Unit tests (fast, isolated)
    integration: Integration tests (slower, external deps)
    e2e: End-to-end tests (complete workflows)
    slow: Slow tests (performance, load testing)
    security: Security-focused tests
addopts =
    --strict-markers
    --disable-warnings
    --tb=short
    -v
filterwarnings =
    ignore::DeprecationWarning
    ignore::PendingDeprecationWarning
```

*conftest.py*
```python
"""
Shared test fixtures and configuration
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
import tempfile
import json
from typing import Dict, Any

from src.config import Config
from src.server import MyTemplateMCPServer
from src.tools import MyTemplateTools

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_config():
    """Mock configuration for testing"""
    return Config(
        api_key="test-api-key",
        api_base_url="https://api.test.com",
        timeout=30,
        rate_limit=100,
        connection_limit=10,
        supported_formats=["json", "csv", "parquet"],
        features=["feature1", "feature2"]
    )

@pytest.fixture
def sample_data():
    """Sample data for testing"""
    return [
        {"id": 1, "name": "Alice", "category": "A", "value": 100},
        {"id": 2, "name": "Bob", "category": "B", "value": 200},
        {"id": 3, "name": "Charlie", "category": "A", "value": 150}
    ]

@pytest.fixture
def mock_http_session():
    """Mock HTTP session for API testing"""
    session = AsyncMock()
    session.get = AsyncMock()
    session.post = AsyncMock()
    session.close = AsyncMock()
    return session

@pytest.fixture
async def tools_instance(mock_config):
    """Create tools instance for testing"""
    tools = MyTemplateTools(mock_config)
    yield tools
    await tools.close()

@pytest.fixture
async def server_instance(mock_config):
    """Create server instance for testing"""
    server = MyTemplateMCPServer(mock_config)
    yield server
    # Cleanup if needed

@pytest.fixture
def temp_config_file():
    """Create temporary configuration file"""
    config_data = {
        "api_key": "test-key",
        "base_url": "https://api.test.com",
        "features": ["test_feature"]
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config_data, f)
        yield f.name

    # Cleanup handled by tempfile

@pytest.fixture
def mock_external_api():
    """Mock external API responses"""
    responses = {
        "GET /data": {"items": [{"id": 1, "name": "test"}]},
        "GET /health": {"status": "healthy"},
        "POST /process": {"result": "processed"}
    }

    return responses
```

## Unit Testing

### Testing Tools

*tests/test_tools.py*
```python
"""
Unit tests for template tools
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
import aiohttp
import json

from src.tools import MyTemplateTools

class TestDataFetching:
    """Test data fetching functionality"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_fetch_data_success(self, tools_instance, mock_external_api):
        """Test successful data fetching"""
        # Setup mock response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = mock_external_api["GET /data"]
        mock_response.headers = {"content-type": "application/json"}
        mock_response.raise_for_status.return_value = None

        with patch.object(tools_instance, 'session') as mock_session:
            mock_session.get.return_value.__aenter__.return_value = mock_response

            result = await tools_instance.fetch_data("data")

            # Assertions
            assert result["success"] is True
            assert result["data"] == mock_external_api["GET /data"]
            assert result["metadata"]["endpoint"] == "data"
            assert result["metadata"]["status_code"] == 200

            # Verify API call
            mock_session.get.assert_called_once()
            call_args = mock_session.get.call_args
            assert "data" in call_args[0][0]

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_fetch_data_with_filters(self, tools_instance):
        """Test data fetching with query filters"""
        filters = {"category": "test", "limit": 10}

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {"filtered": "data"}
        mock_response.headers = {"content-type": "application/json"}
        mock_response.raise_for_status.return_value = None

        with patch.object(tools_instance, 'session') as mock_session:
            mock_session.get.return_value.__aenter__.return_value = mock_response

            result = await tools_instance.fetch_data("data", filters=filters)

            # Verify filters were passed as parameters
            call_args = mock_session.get.call_args
            params = call_args[1]["params"]
            assert params["category"] == "test"
            assert params["limit"] == 10

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_fetch_data_http_error(self, tools_instance):
        """Test handling of HTTP errors"""
        mock_response = AsyncMock()
        mock_response.raise_for_status.side_effect = aiohttp.ClientResponseError(
            request_info=Mock(),
            history=(),
            status=404,
            message="Not Found"
        )

        with patch.object(tools_instance, 'session') as mock_session:
            mock_session.get.return_value.__aenter__.return_value = mock_response

            with pytest.raises(Exception, match="API request failed"):
                await tools_instance.fetch_data("nonexistent")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_fetch_data_timeout(self, tools_instance):
        """Test handling of request timeouts"""
        with patch.object(tools_instance, 'session') as mock_session:
            mock_session.get.side_effect = asyncio.TimeoutError()

            with pytest.raises(Exception, match="Request timeout"):
                await tools_instance.fetch_data("slow-endpoint")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_fetch_data_csv_format(self, tools_instance):
        """Test CSV format data fetching"""
        csv_data = "id,name\n1,test\n2,test2"

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text.return_value = csv_data
        mock_response.headers = {"content-type": "text/csv"}
        mock_response.raise_for_status.return_value = None

        with patch.object(tools_instance, 'session') as mock_session:
            mock_session.get.return_value.__aenter__.return_value = mock_response

            result = await tools_instance.fetch_data("data", format="csv")

            assert result["success"] is True
            assert len(result["data"]) == 2
            assert result["data"][0]["name"] == "test"

class TestDataTransformation:
    """Test data transformation functionality"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_transform_rename_field(self, tools_instance, sample_data):
        """Test field renaming transformation"""
        transformations = [{
            "type": "rename_field",
            "from": "name",
            "to": "full_name"
        }]

        result = await tools_instance.transform_data(sample_data, transformations)

        assert result["success"] is True
        assert len(result["data"]) == 3

        # Verify field was renamed
        for record in result["data"]:
            assert "full_name" in record
            assert "name" not in record

        assert result["data"][0]["full_name"] == "Alice"
        assert result["statistics"]["records_processed"] == 3

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_transform_add_field(self, tools_instance, sample_data):
        """Test field addition transformation"""
        transformations = [{
            "type": "add_field",
            "name": "status",
            "value": "active"
        }]

        result = await tools_instance.transform_data(sample_data, transformations)

        assert result["success"] is True

        # Verify field was added
        for record in result["data"]:
            assert record["status"] == "active"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_transform_filter_field(self, tools_instance, sample_data):
        """Test field filtering transformation"""
        transformations = [{
            "type": "filter_field",
            "field": "category",
            "condition": {"operator": "eq", "value": "A"}
        }]

        result = await tools_instance.transform_data(sample_data, transformations)

        assert result["success"] is True
        # Should only keep records with category "A"
        assert result["statistics"]["records_processed"] == 2
        assert result["statistics"]["records_skipped"] == 1

        # Verify filtered data
        for record in result["data"]:
            assert record["category"] == "A"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_transform_format_field(self, tools_instance, sample_data):
        """Test field formatting transformation"""
        transformations = [{
            "type": "format_field",
            "field": "name",
            "format": "uppercase"
        }]

        result = await tools_instance.transform_data(sample_data, transformations)

        assert result["success"] is True

        # Verify field was formatted
        assert result["data"][0]["name"] == "ALICE"
        assert result["data"][1]["name"] == "BOB"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_transform_multiple_transformations(self, tools_instance, sample_data):
        """Test multiple transformations in sequence"""
        transformations = [
            {"type": "format_field", "field": "name", "format": "uppercase"},
            {"type": "add_field", "name": "processed", "value": True},
            {"type": "rename_field", "from": "value", "to": "amount"}
        ]

        result = await tools_instance.transform_data(sample_data, transformations)

        assert result["success"] is True
        assert result["statistics"]["transformations_applied"] == 9  # 3 records * 3 transformations

        # Verify all transformations applied
        record = result["data"][0]
        assert record["name"] == "ALICE"  # Formatted
        assert record["processed"] is True  # Added
        assert "amount" in record  # Renamed
        assert "value" not in record  # Original field removed

class TestDataExport:
    """Test data export functionality"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_export_json(self, tools_instance, sample_data):
        """Test JSON export functionality"""
        result = await tools_instance.export_data(sample_data, format="json")

        assert result["success"] is True
        assert result["format"] == "json"
        assert result["records_exported"] == 3
        assert result["bytes_written"] > 0

        # Verify JSON is valid
        exported_data = result["data"]
        parsed_data = json.loads(exported_data)
        assert len(parsed_data) == 3
        assert parsed_data[0]["name"] == "Alice"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_export_csv(self, tools_instance, sample_data):
        """Test CSV export functionality"""
        result = await tools_instance.export_data(sample_data, format="csv")

        assert result["success"] is True
        assert result["format"] == "csv"
        assert result["records_exported"] == 3

        # Verify CSV format
        csv_data = result["data"]
        lines = csv_data.strip().split('\n')
        assert len(lines) == 4  # Header + 3 data rows
        assert "id,name,category,value" in lines[0]
        assert "1,Alice,A,100" in lines[1]

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_export_with_destination(self, tools_instance, sample_data):
        """Test export with file destination"""
        with patch.object(tools_instance, '_write_to_destination') as mock_write:
            mock_write.return_value = None

            result = await tools_instance.export_data(
                sample_data,
                format="json",
                destination="/tmp/test.json"
            )

            assert result["success"] is True
            assert result["destination"] == "/tmp/test.json"
            mock_write.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_export_unsupported_format(self, tools_instance, sample_data):
        """Test handling of unsupported export formats"""
        with pytest.raises(Exception, match="Unsupported export format"):
            await tools_instance.export_data(sample_data, format="xml")

class TestHealthChecks:
    """Test health check functionality"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_api_health_check_success(self, tools_instance):
        """Test successful API health check"""
        mock_response = AsyncMock()
        mock_response.status = 200

        with patch.object(tools_instance, 'session') as mock_session:
            mock_session.get.return_value.__aenter__.return_value = mock_response

            result = await tools_instance.check_api_health()

            assert result is True
            # Verify health endpoint was called
            call_args = mock_session.get.call_args
            assert "health" in call_args[0][0]

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_api_health_check_failure(self, tools_instance):
        """Test failed API health check"""
        mock_response = AsyncMock()
        mock_response.status = 503  # Service unavailable

        with patch.object(tools_instance, 'session') as mock_session:
            mock_session.get.return_value.__aenter__.return_value = mock_response

            result = await tools_instance.check_api_health()

            assert result is False

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_api_health_check_exception(self, tools_instance):
        """Test health check with network exception"""
        with patch.object(tools_instance, 'session') as mock_session:
            mock_session.get.side_effect = Exception("Network error")

            result = await tools_instance.check_api_health()

            assert result is False
```

### Testing Configuration

*tests/test_config.py*
```python
"""
Unit tests for configuration management
"""

import pytest
import os
import json
import tempfile
from unittest.mock import patch

from src.config import Config, load_config

class TestConfiguration:
    """Test configuration loading and validation"""

    @pytest.mark.unit
    def test_config_creation(self):
        """Test basic configuration creation"""
        config = Config(
            api_key="test-key",
            api_base_url="https://api.test.com"
        )

        assert config.api_key == "test-key"
        assert config.api_base_url == "https://api.test.com"
        assert config.timeout == 30  # Default value

    @pytest.mark.unit
    def test_config_validation_success(self):
        """Test successful configuration validation"""
        config = Config(
            api_key="valid-key",
            api_base_url="https://api.test.com"
        )

        assert config.validate() is True

    @pytest.mark.unit
    def test_config_validation_missing_api_key(self):
        """Test validation failure with missing API key"""
        config = Config(
            api_base_url="https://api.test.com"
        )

        assert config.validate() is False

    @pytest.mark.unit
    def test_config_validation_invalid_url(self):
        """Test validation failure with invalid URL"""
        config = Config(
            api_key="test-key",
            api_base_url="not-a-url"
        )

        assert config.validate() is False

    @pytest.mark.unit
    def test_load_config_from_env(self):
        """Test loading configuration from environment variables"""
        env_vars = {
            "CUSTOM_API_KEY": "env-api-key",
            "CUSTOM_BASE_URL": "https://env.api.com",
            "CUSTOM_FEATURES": "feature1,feature2,feature3"
        }

        with patch.dict(os.environ, env_vars):
            config = load_config()

            assert config.api_key == "env-api-key"
            assert config.api_base_url == "https://env.api.com"
            assert config.features == ["feature1", "feature2", "feature3"]

    @pytest.mark.unit
    def test_load_config_from_file(self, temp_config_file):
        """Test loading configuration from file"""
        with patch.dict(os.environ, {"MCP_CONFIG_FILE": temp_config_file}):
            config = load_config()

            assert config.api_key == "test-key"
            assert config.api_base_url == "https://api.test.com"

    @pytest.mark.unit
    def test_config_precedence(self, temp_config_file):
        """Test configuration precedence (env > file > defaults)"""
        env_vars = {
            "CUSTOM_API_KEY": "env-override-key",
            "MCP_CONFIG_FILE": temp_config_file
        }

        with patch.dict(os.environ, env_vars):
            config = load_config()

            # API key should come from environment (highest precedence)
            assert config.api_key == "env-override-key"
            # Base URL should come from file
            assert config.api_base_url == "https://api.test.com"

    @pytest.mark.unit
    def test_nested_config_from_env(self):
        """Test loading nested configuration from environment"""
        env_vars = {
            "CUSTOM_ADVANCED__TIMEOUT": "60",
            "CUSTOM_ADVANCED__RETRY_ATTEMPTS": "5"
        }

        with patch.dict(os.environ, env_vars):
            config = load_config()

            assert config.advanced["timeout"] == 60
            assert config.advanced["retry_attempts"] == 5
```

## Integration Testing

### Testing External Dependencies

*tests/test_integration.py*
```python
"""
Integration tests for external dependencies and workflows
"""

import pytest
import asyncio
from unittest.mock import patch
import responses
import aioresponses

from src.server import MyTemplateMCPServer
from src.tools import MyTemplateTools
from src.config import Config

class TestAPIIntegration:
    """Test integration with external APIs"""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_api_health_check(self):
        """Test health check against real API endpoint"""
        # Use httpbin.org for reliable testing
        config = Config(
            api_key="test-key",
            api_base_url="https://httpbin.org"
        )

        tools = MyTemplateTools(config)

        try:
            # httpbin.org/status/200 returns 200 OK
            with patch.object(tools, 'config') as mock_config:
                mock_config.api_base_url = "https://httpbin.org"

                # Mock the health endpoint to use httpbin status
                with patch.object(tools, 'check_api_health') as mock_health:
                    async def mock_health_check():
                        try:
                            async with tools.session.get("https://httpbin.org/status/200") as response:
                                return response.status == 200
                        except:
                            return False

                    mock_health.side_effect = mock_health_check
                    result = await tools.check_api_health()

                    assert result is True
        finally:
            await tools.close()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_fetch_data_with_mock_api(self):
        """Test data fetching with mocked API responses"""
        config = Config(
            api_key="test-key",
            api_base_url="https://api.test.com"
        )

        tools = MyTemplateTools(config)

        # Mock API responses
        with aioresponses.aioresponses() as m:
            m.get(
                "https://api.test.com/data",
                payload={"items": [{"id": 1, "name": "test"}]},
                status=200
            )

            result = await tools.fetch_data("data")

            assert result["success"] is True
            assert len(result["data"]["items"]) == 1
            assert result["data"]["items"][0]["name"] == "test"

        await tools.close()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_fetch_data_api_error_handling(self):
        """Test handling of API errors in integration"""
        config = Config(
            api_key="test-key",
            api_base_url="https://api.test.com"
        )

        tools = MyTemplateTools(config)

        # Mock API error response
        with aioresponses.aioresponses() as m:
            m.get(
                "https://api.test.com/error",
                status=500,
                payload={"error": "Internal server error"}
            )

            with pytest.raises(Exception, match="API request failed"):
                await tools.fetch_data("error")

        await tools.close()

class TestWorkflowIntegration:
    """Test complete workflow integration"""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_complete_data_pipeline(self):
        """Test complete data processing pipeline"""
        config = Config(
            api_key="test-key",
            api_base_url="https://api.test.com"
        )

        server = MyTemplateMCPServer(config)

        # Mock the complete workflow
        sample_api_data = [
            {"id": 1, "name": "alice", "category": "user"},
            {"id": 2, "name": "bob", "category": "admin"}
        ]

        # Step 1: Fetch data (mocked)
        with patch.object(server.tools, 'fetch_data') as mock_fetch:
            mock_fetch.return_value = {
                "success": True,
                "data": sample_api_data
            }

            fetch_result = await server.tools.fetch_data("users")
            assert fetch_result["success"] is True

            # Step 2: Transform data (real implementation)
            transformations = [
                {"type": "format_field", "field": "name", "format": "uppercase"},
                {"type": "add_field", "name": "processed_at", "value": "2025-01-27T16:47:30Z"}
            ]

            transform_result = await server.tools.transform_data(
                fetch_result["data"],
                transformations
            )

            assert transform_result["success"] is True
            assert transform_result["data"][0]["name"] == "ALICE"
            assert "processed_at" in transform_result["data"][0]

            # Step 3: Export data (real implementation)
            export_result = await server.tools.export_data(
                transform_result["data"],
                format="json"
            )

            assert export_result["success"] is True
            assert export_result["records_exported"] == 2

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_error_recovery_workflow(self):
        """Test workflow error recovery"""
        config = Config(
            api_key="test-key",
            api_base_url="https://api.test.com"
        )

        server = MyTemplateMCPServer(config)

        # Test fetch failure recovery
        with patch.object(server.tools, 'fetch_data') as mock_fetch:
            mock_fetch.side_effect = Exception("API unavailable")

            try:
                await server.tools.fetch_data("users")
                assert False, "Should have raised exception"
            except Exception as e:
                assert "API unavailable" in str(e)

        # Test transformation with invalid data
        invalid_data = [{"incomplete": "data"}]
        transformations = [{"type": "rename_field", "from": "nonexistent", "to": "new"}]

        result = await server.tools.transform_data(invalid_data, transformations)
        # Should handle gracefully without complete failure
        assert result["success"] is True

class TestConfigurationIntegration:
    """Test configuration loading in integration scenarios"""

    @pytest.mark.integration
    def test_config_file_loading(self, temp_config_file):
        """Test configuration loading from file"""
        with patch.dict(os.environ, {"MCP_CONFIG_FILE": temp_config_file}):
            config = load_config()

            assert config.api_key == "test-key"
            assert config.validate() is True

    @pytest.mark.integration
    def test_environment_override(self, temp_config_file):
        """Test environment variable override of config file"""
        env_vars = {
            "MCP_CONFIG_FILE": temp_config_file,
            "CUSTOM_API_KEY": "override-key"
        }

        with patch.dict(os.environ, env_vars):
            config = load_config()

            # Environment should override file
            assert config.api_key == "override-key"
            # File values should still be loaded
            assert config.api_base_url == "https://api.test.com"
```

## End-to-End Testing

### Full System Testing

*tests/test_e2e.py*
```python
"""
End-to-end tests for complete system functionality
"""

import pytest
import asyncio
import json
import tempfile
from unittest.mock import patch
import docker
import requests

from src.server import MyTemplateMCPServer

class TestContainerDeployment:
    """Test containerized deployment scenarios"""

    @pytest.mark.e2e
    @pytest.mark.slow
    def test_docker_container_health(self):
        """Test template running in Docker container"""
        # This test requires Docker to be available
        try:
            client = docker.from_env()

            # Build test image
            image = client.images.build(
                path=".",
                tag="my-template:test",
                quiet=False
            )[0]

            # Run container with test configuration
            container = client.containers.run(
                "my-template:test",
                environment={
                    "CUSTOM_API_KEY": "test-key",
                    "CUSTOM_BASE_URL": "https://httpbin.org"
                },
                ports={"8080/tcp": 8080},
                detach=True,
                remove=True
            )

            try:
                # Wait for container to start
                asyncio.sleep(5)

                # Test health endpoint
                response = requests.get("http://localhost:8080/health", timeout=10)
                assert response.status_code == 200

                health_data = response.json()
                assert health_data["status"] == "healthy"

            finally:
                container.stop()

        except docker.errors.DockerException:
            pytest.skip("Docker not available for testing")

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_mcp_protocol_compliance(self):
        """Test MCP protocol compliance"""
        config = load_config()
        server = MyTemplateMCPServer(config)

        # Test tool discovery
        tools = await server._discover_tools()
        assert len(tools) > 0

        # Test each tool has required MCP fields
        for tool in tools:
            assert "name" in tool
            assert "description" in tool
            assert "inputSchema" in tool

        # Test tool execution
        for tool_name in ["fetch_data", "transform_data", "export_data"]:
            tool_info = next((t for t in tools if t["name"] == tool_name), None)
            assert tool_info is not None, f"Tool {tool_name} not found"

class TestUserWorkflows:
    """Test realistic user workflows"""

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_data_analyst_workflow(self):
        """Test typical data analyst workflow"""
        # Scenario: Data analyst needs to fetch, clean, and export data

        server = MyTemplateMCPServer()

        # Step 1: Fetch customer data
        with patch.object(server.tools, 'fetch_data') as mock_fetch:
            mock_fetch.return_value = {
                "success": True,
                "data": [
                    {"id": 1, "name": "  Alice Johnson  ", "email": "alice@example.com", "status": "active"},
                    {"id": 2, "name": "Bob Smith", "email": "BOB@EXAMPLE.COM", "status": "inactive"},
                    {"id": 3, "name": "Charlie Brown", "email": "charlie@example.com", "status": "active"}
                ]
            }

            # Fetch data
            raw_data = await server.tools.fetch_data("customers")
            assert raw_data["success"] is True

            # Step 2: Clean and transform data
            cleaning_transformations = [
                {"type": "format_field", "field": "name", "format": "strip"},
                {"type": "format_field", "field": "email", "format": "lowercase"},
                {"type": "filter_field", "field": "status", "condition": {"operator": "eq", "value": "active"}},
                {"type": "add_field", "name": "processed_date", "value": "2025-01-27"}
            ]

            cleaned_data = await server.tools.transform_data(
                raw_data["data"],
                cleaning_transformations
            )

            assert cleaned_data["success"] is True
            assert cleaned_data["statistics"]["records_processed"] == 2  # Only active users
            assert cleaned_data["data"][0]["name"] == "Alice Johnson"  # Trimmed
            assert cleaned_data["data"][0]["email"] == "alice@example.com"  # Lowercase

            # Step 3: Export for analysis
            export_result = await server.tools.export_data(
                cleaned_data["data"],
                format="csv"
            )

            assert export_result["success"] is True
            assert export_result["records_exported"] == 2

            # Verify CSV format is correct
            csv_content = export_result["data"]
            lines = csv_content.strip().split('\n')
            assert len(lines) == 3  # Header + 2 data rows
            assert "processed_date" in lines[0]  # Added field in header

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_developer_integration_workflow(self):
        """Test developer integration workflow"""
        # Scenario: Developer integrating MCP server into application

        server = MyTemplateMCPServer()

        # Test 1: Verify server health
        health_result = await server._health_check()
        assert health_result["status"] in ["healthy", "unhealthy"]
        assert "checks" in health_result

        # Test 2: Discover available tools
        tools = await server._discover_tools()
        expected_tools = ["fetch_data", "transform_data", "export_data", "health_check"]

        for expected_tool in expected_tools:
            tool_found = any(tool["name"] == expected_tool for tool in tools)
            assert tool_found, f"Tool {expected_tool} not found"

        # Test 3: Validate tool schemas
        for tool in tools:
            assert "inputSchema" in tool
            schema = tool["inputSchema"]
            assert "type" in schema
            assert schema["type"] == "object"
            if "properties" in schema:
                assert isinstance(schema["properties"], dict)

        # Test 4: Test error handling
        with patch.object(server.tools, 'fetch_data') as mock_fetch:
            mock_fetch.side_effect = Exception("Simulated failure")

            try:
                await server.tools.fetch_data("test")
                assert False, "Should have raised exception"
            except Exception as e:
                assert "Simulated failure" in str(e)

class TestPerformanceScenarios:
    """Test performance under various scenarios"""

    @pytest.mark.e2e
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_large_dataset_processing(self):
        """Test processing of large datasets"""
        # Generate large dataset
        large_dataset = [
            {"id": i, "name": f"User_{i}", "value": i * 10}
            for i in range(1000)  # 1000 records
        ]

        server = MyTemplateMCPServer()

        # Test transformation performance
        transformations = [
            {"type": "add_field", "name": "processed", "value": True},
            {"type": "format_field", "field": "name", "format": "uppercase"}
        ]

        import time
        start_time = time.time()

        result = await server.tools.transform_data(large_dataset, transformations)

        end_time = time.time()
        processing_time = end_time - start_time

        # Performance assertions
        assert result["success"] is True
        assert result["statistics"]["records_processed"] == 1000
        assert processing_time < 5.0  # Should process within 5 seconds

        # Verify transformations applied correctly
        assert result["data"][0]["processed"] is True
        assert result["data"][0]["name"] == "USER_0"

    @pytest.mark.e2e
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """Test handling of concurrent requests"""
        server = MyTemplateMCPServer()

        # Create multiple concurrent tasks
        async def fetch_task(endpoint):
            with patch.object(server.tools, 'fetch_data') as mock_fetch:
                mock_fetch.return_value = {
                    "success": True,
                    "data": [{"endpoint": endpoint, "timestamp": "2025-01-27T16:47:30Z"}]
                }
                return await server.tools.fetch_data(endpoint)

        # Run concurrent tasks
        tasks = [fetch_task(f"endpoint_{i}") for i in range(10)]
        results = await asyncio.gather(*tasks)

        # Verify all tasks completed successfully
        assert len(results) == 10
        for result in results:
            assert result["success"] is True
```

## Deployment Testing

### Template Validation

```bash
# Template structure validation
python -m mcp_template validate my-template --comprehensive

# Configuration schema validation
python -m mcp_template config my-template --validate-schema

# Docker build testing
python -m mcp_template build my-template --test

# Deployment smoke test
python -m mcp_template deploy my-template --test-mode --timeout 60
```

### Integration Testing with MCP Platform

*tests/test_platform_integration.py*
```python
"""
Test integration with MCP platform
"""

import pytest
import requests
import time
from unittest.mock import patch

class TestPlatformIntegration:
    """Test integration with MCP template platform"""

    @pytest.mark.integration
    def test_template_deployment(self):
        """Test template deployment through platform"""
        # This would typically use the platform API
        deployment_config = {
            "template_id": "my-template",
            "environment": "test",
            "config": {
                "api_key": "test-key",
                "base_url": "https://api.test.com"
            }
        }

        # Mock platform deployment
        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {
                "deployment_id": "test-deployment-123",
                "status": "running",
                "endpoint": "http://localhost:8080"
            }

            # Simulate deployment request
            response = requests.post(
                "http://platform.api/deploy",
                json=deployment_config
            )

            assert response.status_code == 200
            deployment_info = response.json()
            assert deployment_info["status"] == "running"

    @pytest.mark.integration
    def test_template_discovery(self):
        """Test template discovery by platform"""
        # Mock template registry API
        with patch('requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {
                "tools": [
                    {
                        "name": "fetch_data",
                        "description": "Fetch data from API",
                        "parameters": {"endpoint": {"type": "string"}}
                    }
                ]
            }

            response = requests.get("http://template.endpoint/tools")
            assert response.status_code == 200

            tools = response.json()["tools"]
            assert len(tools) > 0
            assert tools[0]["name"] == "fetch_data"
```

## Performance Testing

### Load Testing

*tests/test_performance.py*
```python
"""
Performance tests for template functionality
"""

import pytest
import asyncio
import time
import statistics
from concurrent.futures import ThreadPoolExecutor

from src.server import MyTemplateMCPServer

class TestPerformance:
    """Performance testing suite"""

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_transformation_performance(self):
        """Test data transformation performance"""
        server = MyTemplateMCPServer()

        # Generate test data of various sizes
        test_sizes = [100, 500, 1000, 5000]
        performance_results = {}

        for size in test_sizes:
            test_data = [
                {"id": i, "name": f"item_{i}", "value": i * 2}
                for i in range(size)
            ]

            transformations = [
                {"type": "add_field", "name": "processed", "value": True},
                {"type": "format_field", "field": "name", "format": "uppercase"}
            ]

            # Measure performance
            start_time = time.time()
            result = await server.tools.transform_data(test_data, transformations)
            end_time = time.time()

            duration = end_time - start_time
            performance_results[size] = duration

            # Verify correctness
            assert result["success"] is True
            assert result["statistics"]["records_processed"] == size

            print(f"Processed {size} records in {duration:.3f}s ({size/duration:.1f} records/sec)")

        # Performance regression test
        # Processing should be roughly linear with data size
        assert performance_results[5000] < performance_results[1000] * 6  # Allow some overhead

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_concurrent_tool_execution(self):
        """Test concurrent tool execution performance"""
        server = MyTemplateMCPServer()

        async def test_tool_call():
            """Single tool call for concurrency testing"""
            test_data = [{"id": 1, "name": "test"}]
            transformations = [{"type": "add_field", "name": "test", "value": True}]

            start = time.time()
            result = await server.tools.transform_data(test_data, transformations)
            duration = time.time() - start

            return {"success": result["success"], "duration": duration}

        # Test different concurrency levels
        concurrency_levels = [1, 5, 10, 20]

        for concurrency in concurrency_levels:
            tasks = [test_tool_call() for _ in range(concurrency)]

            start_time = time.time()
            results = await asyncio.gather(*tasks)
            total_time = time.time() - start_time

            # Verify all tasks succeeded
            success_count = sum(1 for r in results if r["success"])
            assert success_count == concurrency

            # Calculate performance metrics
            durations = [r["duration"] for r in results]
            avg_duration = statistics.mean(durations)

            print(f"Concurrency {concurrency}: {total_time:.3f}s total, {avg_duration:.3f}s avg per task")

            # Performance assertions
            assert total_time < concurrency * 2.0  # Should benefit from concurrency
            assert avg_duration < 1.0  # Each task should be reasonably fast
```

## Security Testing

### Security Validation

*tests/test_security.py*
```python
"""
Security tests for template functionality
"""

import pytest
from unittest.mock import patch

from src.tools import MyTemplateTools
from src.config import Config

class TestSecurity:
    """Security testing suite"""

    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_input_validation(self):
        """Test input validation and sanitization"""
        config = Config(api_key="test-key", api_base_url="https://api.test.com")
        tools = MyTemplateTools(config)

        # Test SQL injection attempts
        malicious_inputs = [
            "'; DROP TABLE users; --",
            "<script>alert('xss')</script>",
            "../../etc/passwd",
            "\x00\x01\x02",  # Binary data
            "A" * 10000,  # Large input
        ]

        for malicious_input in malicious_inputs:
            try:
                # Should handle malicious input gracefully
                with patch.object(tools, 'session'):
                    result = await tools.fetch_data(malicious_input)

                # If no exception, verify result is safe
                if isinstance(result, dict) and result.get("success"):
                    # Verify no malicious content in response
                    response_str = str(result)
                    assert "<script>" not in response_str
                    assert "DROP TABLE" not in response_str

            except Exception as e:
                # Exception is acceptable for malicious input
                assert "validation" in str(e).lower() or "invalid" in str(e).lower()

        await tools.close()

    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_api_key_protection(self):
        """Test API key is not exposed in logs or responses"""
        config = Config(api_key="secret-api-key-123", api_base_url="https://api.test.com")
        tools = MyTemplateTools(config)

        # Mock API call that might log request details
        with patch.object(tools, 'session') as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = {"data": "test"}
            mock_response.headers = {"content-type": "application/json"}
            mock_response.raise_for_status.return_value = None

            mock_session.get.return_value.__aenter__.return_value = mock_response

            result = await tools.fetch_data("test")

            # Verify API key is not in response
            response_str = str(result)
            assert "secret-api-key-123" not in response_str

            # Verify API key is not in logged request details
            # (This would require checking actual log output in a real scenario)

        await tools.close()

    @pytest.mark.security
    def test_configuration_validation(self):
        """Test configuration security validation"""
        # Test invalid/insecure configurations
        insecure_configs = [
            {"api_key": "", "api_base_url": "https://api.test.com"},  # Empty API key
            {"api_key": "test", "api_base_url": "http://api.test.com"},  # HTTP instead of HTTPS
            {"api_key": "test", "api_base_url": "javascript:alert('xss')"},  # Invalid URL scheme
        ]

        for config_data in insecure_configs:
            config = Config(**config_data)
            assert config.validate() is False, f"Should reject insecure config: {config_data}"
```

## Continuous Integration

### CI Pipeline Configuration

*.github/workflows/test.yml*
```yaml
name: Template Testing

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, "3.10", "3.11"]

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements-dev.txt
        pip install -e .

    - name: Run unit tests
      run: |
        pytest tests/ -m unit --cov=src --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        fail_ci_if_error: true

  integration-tests:
    runs-on: ubuntu-latest
    services:
      redis:
        image: redis:alpine
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: "3.10"

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements-dev.txt
        pip install -e .

    - name: Run integration tests
      run: |
        pytest tests/ -m integration
      env:
        TEST_REDIS_URL: redis://localhost:6379

  security-tests:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: "3.10"

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements-dev.txt
        pip install bandit safety

    - name: Run security tests
      run: |
        pytest tests/ -m security
        bandit -r src/
        safety check

    - name: Run SAST scan
      uses: github/super-linter@v4
      env:
        DEFAULT_BRANCH: main
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

  e2e-tests:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: "3.10"

    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v2

    - name: Build Docker image
      run: |
        docker build -t my-template:test .

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements-dev.txt
        pip install docker

    - name: Run E2E tests
      run: |
        pytest tests/ -m e2e
      env:
        DOCKER_IMAGE: my-template:test
```

## Testing Best Practices

### Test Organization

1. **Clear Test Structure**
   - Group tests by functionality
   - Use descriptive test names
   - Follow arrange-act-assert pattern

2. **Comprehensive Coverage**
   - Unit tests for all functions
   - Integration tests for external dependencies
   - End-to-end tests for user workflows

3. **Mock Strategy**
   - Mock external dependencies
   - Use real implementations for internal logic
   - Provide realistic test data

4. **Performance Awareness**
   - Mark slow tests appropriately
   - Use parallel execution where possible
   - Monitor test execution time

### Quality Gates

```bash
# Complete quality gate script
make quality-gate

# Individual checks
make test          # Run all tests
make test-unit     # Unit tests only
make test-integration  # Integration tests
make test-e2e      # End-to-end tests
make coverage      # Coverage report
make lint          # Code linting
make security      # Security checks
```

## Troubleshooting Tests

### Common Issues

1. **Async Test Failures**
   ```python
   # Ensure proper async test setup
   @pytest.mark.asyncio
   async def test_async_function():
       result = await async_function()
       assert result["success"] is True
   ```

2. **Mock Configuration**
   ```python
   # Proper mock setup for HTTP clients
   with patch.object(tools, 'session') as mock_session:
       mock_response = AsyncMock()
       mock_session.get.return_value.__aenter__.return_value = mock_response
   ```

3. **Resource Cleanup**
   ```python
   # Always clean up resources
   @pytest.fixture
   async def tools_instance():
       tools = MyTemplateTools(config)
       yield tools
       await tools.close()  # Cleanup
   ```

## Getting Help

### Community Resources

- **Documentation**: [Testing guides](../guides/testing.md)
- **GitHub Issues**: [Report test issues](https://github.com/Data-Everything/mcp-server-templates/issues)
- **Community Slack**: [Join testing discussions](https://join.slack.com/t/mcp-platform/shared_invite/zt-39z1p559j-8aWEML~IsSPwFFgr7anHRA)

### Professional Support

- **Custom Testing**: Professional test suite development
- **CI/CD Setup**: Automated testing pipeline configuration
- **Performance Optimization**: Test performance optimization
- **Contact**: [support@dataeverything.ai](mailto:support@dataeverything.ai)

---

**Next Steps:**
- [Learn about deployment testing](../cli/deploy.md)
- [Explore development workflows](development.md)
- [View testing examples](../examples/testing.md)
- [Contribute testing improvements](../guides/contributing.md)
