# Template Development Guide

**Complete development workflow for creating, testing, and maintaining high-quality MCP server templates with professional development practices.**

## Development Workflow

### Setting Up Development Environment

#### Prerequisites

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Development tools include:
# - pytest (testing framework)
# - black (code formatting)
# - flake8 (linting)
# - mypy (type checking)
# - coverage (test coverage)
# - pre-commit (git hooks)
```

#### Project Structure

```bash
# Clone the template repository
git clone https://github.com/Data-Everything/mcp-server-templates.git
cd mcp-server-templates

# Set up development environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate     # Windows

pip install -e .
```

#### Development Configuration

```bash
# Configure pre-commit hooks
pre-commit install

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Run development setup
make setup-dev
```

### Template Development Lifecycle

#### 1. Planning Phase

**Define Requirements**
```markdown
# Template Requirements Document
- **Template ID**: my-new-template
- **Purpose**: Integration with XYZ API
- **Target Users**: Data analysts, developers
- **Key Features**:
  - Data fetching tools
  - Transformation utilities
  - Export capabilities
- **Configuration Needs**:
  - API credentials
  - Output formats
  - Rate limiting options
```

**Architecture Design**
```python
# Design your tool structure
tools_design = {
    "fetch_data": {
        "purpose": "Retrieve data from XYZ API",
        "parameters": ["endpoint", "filters", "format"],
        "output": "structured_data"
    },
    "transform_data": {
        "purpose": "Apply transformations to data",
        "parameters": ["data", "transformations"],
        "output": "transformed_data"
    },
    "export_data": {
        "purpose": "Export data in various formats",
        "parameters": ["data", "format", "destination"],
        "output": "export_result"
    }
}
```

#### 2. Development Phase

**Create Template Structure**
```bash
# Use the template creator with development settings
mcp-template create my-new-template --dev-mode

# This creates:
templates/my-new-template/
├── template.json           # Template configuration
├── Dockerfile             # Container definition
├── requirements.txt       # Python dependencies
├── requirements-dev.txt   # Development dependencies
├── src/                   # Source code
│   ├── __init__.py        # Package initialization
│   ├── server.py          # Main server implementation
│   ├── tools.py           # Tool implementations
│   ├── config.py          # Configuration management
│   └── utils.py           # Utility functions
├── tests/                 # Test suite
│   ├── __init__.py        # Test package
│   ├── conftest.py        # Test configuration
│   ├── test_server.py     # Server tests
│   ├── test_tools.py      # Tool tests
│   ├── test_config.py     # Configuration tests
│   └── test_integration.py # Integration tests
├── config/                # Configuration examples
│   ├── development.json   # Development config
│   ├── testing.json       # Testing config
│   └── production.json    # Production config
├── docs/                  # Template documentation
│   ├── README.md          # Overview
│   ├── usage.md           # Usage guide
│   └── api.md             # API reference
├── .env.example           # Environment template
├── .gitignore             # Git ignore rules
├── Makefile               # Development commands
└── docker-compose.dev.yml # Development setup
```

**Implement Core Functionality**

*src/server.py - Main Server*
```python
#!/usr/bin/env python3
"""
My New Template - MCP Server

Professional MCP server implementation with comprehensive error handling,
logging, and configuration management.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from contextlib import asynccontextmanager

from fastmcp import FastMCP
from fastmcp.tools import tool

from .config import Config, load_config
from .tools import MyNewTemplateTools
from .utils import setup_logging

# Initialize logging
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("My New Template")

class MyNewTemplateMCPServer:
    """
    Professional MCP Server Implementation

    Features:
    - Comprehensive error handling
    - Structured logging
    - Configuration validation
    - Health monitoring
    - Graceful shutdown
    """

    def __init__(self, config: Optional[Config] = None):
        self.config = config or load_config()
        self.tools = MyNewTemplateTools(self.config)
        self.is_healthy = False
        self._register_tools()
        self._setup_monitoring()

    def _register_tools(self):
        """Register all available tools with comprehensive error handling"""

        @tool("fetch_data")
        async def fetch_data(
            endpoint: str,
            filters: Optional[Dict[str, Any]] = None,
            format: str = "json"
        ) -> Dict[str, Any]:
            """
            Retrieve data from XYZ API

            Args:
                endpoint: API endpoint to fetch from
                filters: Optional filters to apply
                format: Output format (json, csv, xml)

            Returns:
                Dict containing fetched data and metadata
            """
            try:
                logger.info(f"Fetching data from endpoint: {endpoint}")
                result = await self.tools.fetch_data(endpoint, filters, format)
                logger.info(f"Successfully fetched {len(result.get('data', []))} records")
                return result
            except Exception as e:
                logger.error(f"Failed to fetch data: {e}", exc_info=True)
                return {
                    "success": False,
                    "error": str(e),
                    "endpoint": endpoint,
                    "filters": filters
                }

        @tool("transform_data")
        async def transform_data(
            data: List[Dict[str, Any]],
            transformations: List[Dict[str, Any]]
        ) -> Dict[str, Any]:
            """
            Apply transformations to data

            Args:
                data: Input data to transform
                transformations: List of transformation rules

            Returns:
                Dict containing transformed data
            """
            try:
                logger.info(f"Applying {len(transformations)} transformations to {len(data)} records")
                result = await self.tools.transform_data(data, transformations)
                logger.info(f"Transformation completed: {result.get('records_processed', 0)} records")
                return result
            except Exception as e:
                logger.error(f"Data transformation failed: {e}", exc_info=True)
                return {
                    "success": False,
                    "error": str(e),
                    "input_records": len(data),
                    "transformations": len(transformations)
                }

        @tool("export_data")
        async def export_data(
            data: List[Dict[str, Any]],
            format: str = "json",
            destination: Optional[str] = None
        ) -> Dict[str, Any]:
            """
            Export data in various formats

            Args:
                data: Data to export
                format: Export format (json, csv, parquet, xlsx)
                destination: Optional destination path/URL

            Returns:
                Dict containing export results
            """
            try:
                logger.info(f"Exporting {len(data)} records as {format}")
                result = await self.tools.export_data(data, format, destination)
                logger.info(f"Export completed: {result.get('bytes_written', 0)} bytes written")
                return result
            except Exception as e:
                logger.error(f"Data export failed: {e}", exc_info=True)
                return {
                    "success": False,
                    "error": str(e),
                    "records": len(data),
                    "format": format
                }

        @tool("health_check")
        async def health_check() -> Dict[str, Any]:
            """Get server health status and diagnostics"""
            return await self._health_check()

        logger.info("Registered tools: fetch_data, transform_data, export_data, health_check")

    def _setup_monitoring(self):
        """Setup monitoring and health checks"""
        self.is_healthy = True
        logger.info("Monitoring setup completed")

    async def _health_check(self) -> Dict[str, Any]:
        """Comprehensive health check"""
        try:
            # Check external dependencies
            api_healthy = await self.tools.check_api_health()

            # Check configuration
            config_valid = self.config.validate()

            # Overall health status
            overall_healthy = api_healthy and config_valid and self.is_healthy

            return {
                "status": "healthy" if overall_healthy else "unhealthy",
                "version": "1.0.0",
                "timestamp": "2025-01-27T16:47:30Z",
                "checks": {
                    "api_connection": api_healthy,
                    "configuration": config_valid,
                    "server": self.is_healthy
                },
                "config": {
                    "api_configured": bool(self.config.api_key),
                    "export_formats": self.config.supported_formats,
                    "rate_limit": self.config.rate_limit
                }
            }

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": "2025-01-27T16:47:30Z"
            }

@asynccontextmanager
async def lifespan_manager():
    """Manage server startup and shutdown"""
    logger.info("MCP Server starting up...")
    yield
    logger.info("MCP Server shutting down...")

async def main():
    """Main server entry point with proper lifecycle management"""
    # Setup logging
    setup_logging()

    # Load and validate configuration
    config = load_config()
    if not config.validate():
        logger.error("Invalid configuration, exiting")
        return

    # Initialize server
    server = MyNewTemplateMCPServer(config)

    logger.info("My New Template MCP Server starting...")
    logger.info(f"Configuration: API configured={bool(config.api_key)}")

    try:
        await mcp.run()
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
    finally:
        logger.info("Server shutdown complete")

if __name__ == "__main__":
    asyncio.run(main())
```

*src/tools.py - Tool Implementations*
```python
"""
Tool implementations for My New Template

Professional tool implementations with comprehensive error handling,
validation, and logging.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
import aiohttp
import json
import csv
import pandas as pd
from io import StringIO, BytesIO

from .config import Config
from .utils import validate_input, rate_limit, retry_on_failure

logger = logging.getLogger(__name__)

class MyNewTemplateTools:
    """Professional tool implementations with comprehensive features"""

    def __init__(self, config: Config):
        self.config = config
        self.session = None
        self._setup_session()

    async def _setup_session(self):
        """Setup HTTP session with proper configuration"""
        timeout = aiohttp.ClientTimeout(total=self.config.timeout)
        connector = aiohttp.TCPConnector(limit=self.config.connection_limit)

        self.session = aiohttp.ClientSession(
            timeout=timeout,
            connector=connector,
            headers={
                "User-Agent": "MCP-Server-MyNewTemplate/1.0.0",
                "Authorization": f"Bearer {self.config.api_key}"
            }
        )

    @validate_input
    @rate_limit
    @retry_on_failure(max_attempts=3)
    async def fetch_data(
        self,
        endpoint: str,
        filters: Optional[Dict[str, Any]] = None,
        format: str = "json"
    ) -> Dict[str, Any]:
        """
        Fetch data from external API with comprehensive error handling

        Args:
            endpoint: API endpoint to fetch from
            filters: Optional query filters
            format: Response format

        Returns:
            Dict containing fetched data and metadata
        """
        if not self.session:
            await self._setup_session()

        try:
            # Build request URL
            url = f"{self.config.api_base_url.rstrip('/')}/{endpoint.lstrip('/')}"

            # Prepare query parameters
            params = filters or {}
            params['format'] = format

            logger.debug(f"Fetching data from: {url} with params: {params}")

            # Make API request
            async with self.session.get(url, params=params) as response:
                response.raise_for_status()

                # Parse response based on format
                if format.lower() == 'json':
                    data = await response.json()
                elif format.lower() == 'csv':
                    text = await response.text()
                    data = self._parse_csv(text)
                else:
                    data = await response.text()

                # Return structured response
                return {
                    "success": True,
                    "data": data,
                    "metadata": {
                        "endpoint": endpoint,
                        "filters": filters,
                        "format": format,
                        "status_code": response.status,
                        "content_type": response.headers.get('content-type'),
                        "timestamp": "2025-01-27T16:47:30Z"
                    }
                }

        except aiohttp.ClientError as e:
            logger.error(f"HTTP client error: {e}")
            raise Exception(f"API request failed: {e}")
        except asyncio.TimeoutError:
            logger.error(f"Request timeout for endpoint: {endpoint}")
            raise Exception(f"Request timeout for endpoint: {endpoint}")
        except Exception as e:
            logger.error(f"Unexpected error fetching data: {e}")
            raise

    @validate_input
    async def transform_data(
        self,
        data: List[Dict[str, Any]],
        transformations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Apply transformations to data with comprehensive validation

        Args:
            data: Input data to transform
            transformations: List of transformation rules

        Returns:
            Dict containing transformed data and statistics
        """
        try:
            transformed_data = []
            processing_stats = {
                "records_processed": 0,
                "records_skipped": 0,
                "transformations_applied": 0,
                "errors": []
            }

            for record in data:
                try:
                    transformed_record = dict(record)  # Copy original

                    # Apply each transformation
                    for transformation in transformations:
                        transformed_record = await self._apply_transformation(
                            transformed_record,
                            transformation
                        )
                        processing_stats["transformations_applied"] += 1

                    transformed_data.append(transformed_record)
                    processing_stats["records_processed"] += 1

                except Exception as e:
                    logger.warning(f"Skipping record due to transformation error: {e}")
                    processing_stats["records_skipped"] += 1
                    processing_stats["errors"].append(str(e))

            return {
                "success": True,
                "data": transformed_data,
                "statistics": processing_stats,
                "timestamp": "2025-01-27T16:47:30Z"
            }

        except Exception as e:
            logger.error(f"Data transformation failed: {e}")
            raise Exception(f"Data transformation failed: {e}")

    async def _apply_transformation(
        self,
        record: Dict[str, Any],
        transformation: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply a single transformation to a record"""

        transform_type = transformation.get("type")

        if transform_type == "rename_field":
            # Rename field
            old_name = transformation["from"]
            new_name = transformation["to"]
            if old_name in record:
                record[new_name] = record.pop(old_name)

        elif transform_type == "add_field":
            # Add computed field
            field_name = transformation["name"]
            field_value = transformation["value"]
            record[field_name] = field_value

        elif transform_type == "filter_field":
            # Filter field based on condition
            field_name = transformation["field"]
            condition = transformation["condition"]
            if not self._evaluate_condition(record.get(field_name), condition):
                raise Exception(f"Record filtered out by condition: {condition}")

        elif transform_type == "format_field":
            # Format field value
            field_name = transformation["field"]
            format_type = transformation["format"]
            if field_name in record:
                record[field_name] = self._format_value(record[field_name], format_type)

        return record

    @validate_input
    async def export_data(
        self,
        data: List[Dict[str, Any]],
        format: str = "json",
        destination: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Export data in various formats with comprehensive options

        Args:
            data: Data to export
            format: Export format (json, csv, parquet, xlsx)
            destination: Optional destination path/URL

        Returns:
            Dict containing export results and metadata
        """
        try:
            # Export data based on format
            if format.lower() == "json":
                exported_data = self._export_json(data)
            elif format.lower() == "csv":
                exported_data = self._export_csv(data)
            elif format.lower() == "parquet":
                exported_data = self._export_parquet(data)
            elif format.lower() == "xlsx":
                exported_data = self._export_xlsx(data)
            else:
                raise ValueError(f"Unsupported export format: {format}")

            # Handle destination if specified
            if destination:
                await self._write_to_destination(exported_data, destination, format)

            return {
                "success": True,
                "format": format,
                "records_exported": len(data),
                "bytes_written": len(exported_data) if isinstance(exported_data, (str, bytes)) else 0,
                "destination": destination,
                "timestamp": "2025-01-27T16:47:30Z",
                "data": exported_data if not destination else None
            }

        except Exception as e:
            logger.error(f"Data export failed: {e}")
            raise Exception(f"Data export failed: {e}")

    def _export_json(self, data: List[Dict[str, Any]]) -> str:
        """Export data as JSON"""
        return json.dumps(data, indent=2, default=str)

    def _export_csv(self, data: List[Dict[str, Any]]) -> str:
        """Export data as CSV"""
        if not data:
            return ""

        output = StringIO()
        fieldnames = list(data[0].keys())
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
        return output.getvalue()

    def _export_parquet(self, data: List[Dict[str, Any]]) -> bytes:
        """Export data as Parquet"""
        df = pd.DataFrame(data)
        buffer = BytesIO()
        df.to_parquet(buffer, index=False)
        return buffer.getvalue()

    def _export_xlsx(self, data: List[Dict[str, Any]]) -> bytes:
        """Export data as Excel"""
        df = pd.DataFrame(data)
        buffer = BytesIO()
        df.to_excel(buffer, index=False, engine='openpyxl')
        return buffer.getvalue()

    async def check_api_health(self) -> bool:
        """Check if external API is healthy"""
        try:
            if not self.session:
                await self._setup_session()

            health_url = f"{self.config.api_base_url}/health"
            async with self.session.get(health_url) as response:
                return response.status == 200

        except Exception as e:
            logger.warning(f"API health check failed: {e}")
            return False

    def _parse_csv(self, csv_text: str) -> List[Dict[str, Any]]:
        """Parse CSV text into list of dictionaries"""
        reader = csv.DictReader(StringIO(csv_text))
        return list(reader)

    def _evaluate_condition(self, value: Any, condition: Dict[str, Any]) -> bool:
        """Evaluate a filter condition"""
        operator = condition.get("operator", "eq")
        expected = condition.get("value")

        if operator == "eq":
            return value == expected
        elif operator == "ne":
            return value != expected
        elif operator == "gt":
            return value > expected
        elif operator == "lt":
            return value < expected
        elif operator == "contains":
            return expected in str(value)
        else:
            return True

    def _format_value(self, value: Any, format_type: str) -> Any:
        """Format a value according to specified type"""
        if format_type == "uppercase":
            return str(value).upper()
        elif format_type == "lowercase":
            return str(value).lower()
        elif format_type == "title":
            return str(value).title()
        elif format_type == "strip":
            return str(value).strip()
        else:
            return value

    async def close(self):
        """Clean up resources"""
        if self.session:
            await self.session.close()
```

#### 3. Testing Phase

**Comprehensive Test Suite**

*tests/test_tools.py*
```python
"""
Comprehensive tests for My New Template tools
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
import aiohttp

from src.tools import MyNewTemplateTools
from src.config import Config

@pytest.fixture
def mock_config():
    """Create mock configuration for testing"""
    config = Mock(spec=Config)
    config.api_key = "test-key"
    config.api_base_url = "https://api.example.com"
    config.timeout = 30
    config.connection_limit = 10
    config.rate_limit = 100
    return config

@pytest.fixture
async def tools(mock_config):
    """Create tools instance for testing"""
    tools = MyNewTemplateTools(mock_config)
    yield tools
    await tools.close()

class TestFetchData:
    """Test data fetching functionality"""

    @pytest.mark.asyncio
    async def test_fetch_data_success(self, tools):
        """Test successful data fetching"""
        mock_response_data = {"items": [{"id": 1, "name": "test"}]}

        with patch.object(tools, 'session') as mock_session:
            # Setup mock response
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = mock_response_data
            mock_response.headers = {'content-type': 'application/json'}
            mock_response.raise_for_status.return_value = None

            mock_session.get.return_value.__aenter__.return_value = mock_response

            # Test the method
            result = await tools.fetch_data("test/endpoint")

            # Assertions
            assert result["success"] is True
            assert result["data"] == mock_response_data
            assert result["metadata"]["endpoint"] == "test/endpoint"
            assert result["metadata"]["status_code"] == 200

    @pytest.mark.asyncio
    async def test_fetch_data_http_error(self, tools):
        """Test handling of HTTP errors"""
        with patch.object(tools, 'session') as mock_session:
            # Setup mock to raise HTTP error
            mock_response = AsyncMock()
            mock_response.raise_for_status.side_effect = aiohttp.ClientResponseError(
                request_info=Mock(),
                history=(),
                status=404,
                message="Not Found"
            )

            mock_session.get.return_value.__aenter__.return_value = mock_response

            # Test that exception is raised
            with pytest.raises(Exception, match="API request failed"):
                await tools.fetch_data("nonexistent/endpoint")

    @pytest.mark.asyncio
    async def test_fetch_data_with_filters(self, tools):
        """Test data fetching with filters"""
        filters = {"category": "test", "limit": 10}

        with patch.object(tools, 'session') as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = {"items": []}
            mock_response.headers = {'content-type': 'application/json'}
            mock_response.raise_for_status.return_value = None

            mock_session.get.return_value.__aenter__.return_value = mock_response

            result = await tools.fetch_data("test/endpoint", filters=filters)

            # Verify filters were passed
            call_args = mock_session.get.call_args
            assert call_args[1]['params']['category'] == 'test'
            assert call_args[1]['params']['limit'] == 10

class TestTransformData:
    """Test data transformation functionality"""

    @pytest.mark.asyncio
    async def test_transform_data_rename_field(self, tools):
        """Test field renaming transformation"""
        data = [{"old_name": "value1"}, {"old_name": "value2"}]
        transformations = [{
            "type": "rename_field",
            "from": "old_name",
            "to": "new_name"
        }]

        result = await tools.transform_data(data, transformations)

        assert result["success"] is True
        assert len(result["data"]) == 2
        assert "new_name" in result["data"][0]
        assert "old_name" not in result["data"][0]
        assert result["data"][0]["new_name"] == "value1"

    @pytest.mark.asyncio
    async def test_transform_data_add_field(self, tools):
        """Test field addition transformation"""
        data = [{"id": 1}, {"id": 2}]
        transformations = [{
            "type": "add_field",
            "name": "status",
            "value": "active"
        }]

        result = await tools.transform_data(data, transformations)

        assert result["success"] is True
        assert result["data"][0]["status"] == "active"
        assert result["data"][1]["status"] == "active"

    @pytest.mark.asyncio
    async def test_transform_data_error_handling(self, tools):
        """Test error handling in transformations"""
        data = [{"field": "value1"}, {"field": "value2"}]
        transformations = [{
            "type": "filter_field",
            "field": "field",
            "condition": {"operator": "eq", "value": "nonexistent"}
        }]

        result = await tools.transform_data(data, transformations)

        # All records should be skipped due to filter
        assert result["success"] is True
        assert result["statistics"]["records_skipped"] == 2
        assert result["statistics"]["records_processed"] == 0

class TestExportData:
    """Test data export functionality"""

    @pytest.mark.asyncio
    async def test_export_json(self, tools):
        """Test JSON export"""
        data = [{"id": 1, "name": "test"}]

        result = await tools.export_data(data, format="json")

        assert result["success"] is True
        assert result["format"] == "json"
        assert result["records_exported"] == 1
        assert "data" in result
        assert '"id": 1' in result["data"]

    @pytest.mark.asyncio
    async def test_export_csv(self, tools):
        """Test CSV export"""
        data = [{"id": 1, "name": "test"}, {"id": 2, "name": "test2"}]

        result = await tools.export_data(data, format="csv")

        assert result["success"] is True
        assert result["format"] == "csv"
        assert result["records_exported"] == 2
        csv_data = result["data"]
        assert "id,name" in csv_data
        assert "1,test" in csv_data

    @pytest.mark.asyncio
    async def test_export_unsupported_format(self, tools):
        """Test handling of unsupported export format"""
        data = [{"id": 1}]

        with pytest.raises(Exception, match="Unsupported export format"):
            await tools.export_data(data, format="xml")

class TestHealthCheck:
    """Test health check functionality"""

    @pytest.mark.asyncio
    async def test_api_health_check_success(self, tools):
        """Test successful API health check"""
        with patch.object(tools, 'session') as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_session.get.return_value.__aenter__.return_value = mock_response

            result = await tools.check_api_health()

            assert result is True

    @pytest.mark.asyncio
    async def test_api_health_check_failure(self, tools):
        """Test failed API health check"""
        with patch.object(tools, 'session') as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 500
            mock_session.get.return_value.__aenter__.return_value = mock_response

            result = await tools.check_api_health()

            assert result is False
```

**Integration Tests**

*tests/test_integration.py*
```python
"""
Integration tests for My New Template
"""

import pytest
import asyncio
from unittest.mock import patch
import tempfile
import json

from src.server import MyNewTemplateMCPServer
from src.config import Config

@pytest.fixture
def integration_config():
    """Create integration test configuration"""
    return Config(
        api_key="integration-test-key",
        api_base_url="https://httpbin.org",
        timeout=30,
        rate_limit=10
    )

@pytest.mark.integration
class TestFullWorkflow:
    """Test complete workflows end-to-end"""

    @pytest.mark.asyncio
    async def test_fetch_transform_export_workflow(self, integration_config):
        """Test complete data pipeline workflow"""
        server = MyNewTemplateMCPServer(integration_config)

        # Mock external API calls
        with patch.object(server.tools, 'fetch_data') as mock_fetch, \
             patch.object(server.tools, 'transform_data') as mock_transform, \
             patch.object(server.tools, 'export_data') as mock_export:

            # Setup mock responses
            mock_fetch_result = {
                "success": True,
                "data": [{"id": 1, "name": "test1"}, {"id": 2, "name": "test2"}]
            }
            mock_fetch.return_value = mock_fetch_result

            mock_transform_result = {
                "success": True,
                "data": [{"id": 1, "name": "TEST1"}, {"id": 2, "name": "TEST2"}],
                "statistics": {"records_processed": 2}
            }
            mock_transform.return_value = mock_transform_result

            mock_export_result = {
                "success": True,
                "format": "json",
                "records_exported": 2
            }
            mock_export.return_value = mock_export_result

            # Execute workflow
            fetch_result = await server.tools.fetch_data("test/data")
            assert fetch_result["success"] is True

            transform_result = await server.tools.transform_data(
                fetch_result["data"],
                [{"type": "format_field", "field": "name", "format": "uppercase"}]
            )
            assert transform_result["success"] is True

            export_result = await server.tools.export_data(
                transform_result["data"],
                format="json"
            )
            assert export_result["success"] is True

@pytest.mark.integration
class TestErrorRecovery:
    """Test error recovery and resilience"""

    @pytest.mark.asyncio
    async def test_api_failure_recovery(self, integration_config):
        """Test recovery from API failures"""
        server = MyNewTemplateMCPServer(integration_config)

        # Test graceful handling of API failures
        with patch.object(server.tools, 'session') as mock_session:
            mock_session.get.side_effect = Exception("Network error")

            result = await server.tools.fetch_data("test/endpoint")

            # Should handle error gracefully
            assert "error" in str(result).lower()
```

#### 4. Quality Assurance

**Code Quality Tools**

*Makefile*
```makefile
# Development commands for My New Template

.PHONY: setup-dev test lint format type-check coverage clean build

# Development setup
setup-dev:
	pip install -e .
	pip install -r requirements-dev.txt
	pre-commit install

# Testing
test:
	pytest tests/ -v --tb=short

test-integration:
	pytest tests/ -v --tb=short -m integration

test-coverage:
	pytest tests/ --cov=src --cov-report=html --cov-report=term

# Code quality
lint:
	flake8 src/ tests/
	pylint src/

format:
	black src/ tests/
	isort src/ tests/

type-check:
	mypy src/

# Quality gate (run all checks)
quality-gate: format lint type-check test-coverage
	@echo "✅ All quality checks passed!"

# Build
build:
	docker build -t my-new-template .

build-dev:
	docker build -f Dockerfile.dev -t my-new-template:dev .

# Cleanup
clean:
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf dist/
	rm -rf build/

# Template operations
validate:
	mcp-template validate .

deploy-test:
	mcp-template deploy . --config environment=test

deploy-prod:
	mcp-template deploy . --config environment=production
```

*pyproject.toml*
```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "my-new-template"
version = "1.0.0"
description = "Professional MCP server template"
readme = "README.md"
requires-python = ">=3.8"
dependencies = [
    "fastmcp>=0.9.0",
    "aiohttp>=3.8.0",
    "pandas>=1.3.0",
    "openpyxl>=3.0.0",
    "pyarrow>=5.0.0"
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.0.0",
    "black>=22.0.0",
    "flake8>=5.0.0",
    "pylint>=2.15.0",
    "mypy>=0.991",
    "pre-commit>=2.20.0",
    "isort>=5.10.0"
]

[tool.black]
line-length = 88
target-version = ['py38']

[tool.isort]
profile = "black"
line_length = 88

[tool.pylint.messages_control]
disable = ["C0330", "C0326"]

[tool.mypy]
python_version = "3.8"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
markers = [
    "integration: marks tests as integration tests (deselect with '-m \"not integration\"')",
    "slow: marks tests as slow (deselect with '-m \"not slow\"')"
]

[tool.coverage.run]
source = ["src"]
omit = ["tests/*"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError"
]
```

#### 5. Documentation Phase

**Comprehensive Documentation**

*README.md*
```markdown
# My New Template

Professional MCP server template for XYZ API integration with comprehensive data processing capabilities.

## Features

- **Data Fetching**: Retrieve data from XYZ API with flexible filtering
- **Data Transformation**: Apply complex transformations with validation
- **Data Export**: Export in multiple formats (JSON, CSV, Parquet, Excel)
- **Health Monitoring**: Comprehensive health checks and diagnostics
- **Error Recovery**: Robust error handling and recovery mechanisms
- **Performance**: Optimized for high-throughput data processing

## Quick Start

### Using MCP Template Platform

```bash
# Deploy with basic configuration
mcp-template deploy my-new-template --config api_key=your-key

# Deploy with custom configuration
mcp-template deploy my-new-template --config-file config.json
```

### Manual Docker Deployment

```bash
# Build the image
docker build -t my-new-template .

# Run with environment variables
docker run -d \
  -e CUSTOM_API_KEY=your-api-key \
  -e CUSTOM_BASE_URL=https://api.example.com \
  -p 8080:8080 \
  my-new-template
```

## Configuration

### Required Configuration

| Option | Environment Variable | Description |
|--------|---------------------|-------------|
| `api_key` | `CUSTOM_API_KEY` | API authentication key |

### Optional Configuration

| Option | Environment Variable | Default | Description |
|--------|---------------------|---------|-------------|
| `base_url` | `CUSTOM_BASE_URL` | `https://api.example.com` | API base URL |
| `features` | `CUSTOM_FEATURES` | `["feature1","feature2"]` | Enabled features (comma-separated) |
| `advanced.timeout` | `CUSTOM_ADVANCED__TIMEOUT` | `30` | Request timeout in seconds |
| `advanced.retry_attempts` | `CUSTOM_ADVANCED__RETRY_ATTEMPTS` | `3` | Number of retry attempts |

### Configuration File Example

```json
{
  "api_key": "your-api-key-here",
  "base_url": "https://api.example.com",
  "features": ["data_processing", "export_support"],
  "advanced": {
    "timeout": 60,
    "retry_attempts": 5
  }
}
```

## Available Tools

### fetch_data

Retrieve data from XYZ API with flexible filtering options.

**Parameters:**
- `endpoint` (string, required): API endpoint to fetch from
- `filters` (object, optional): Query filters to apply
- `format` (string, optional): Response format (json, csv, xml)

**Example:**
```json
{
  "endpoint": "users",
  "filters": {
    "category": "active",
    "limit": 100
  },
  "format": "json"
}
```

### transform_data

Apply transformations to data with comprehensive validation.

**Parameters:**
- `data` (array, required): Input data to transform
- `transformations` (array, required): List of transformation rules

**Transformation Types:**
- `rename_field`: Rename a field
- `add_field`: Add a computed field
- `filter_field`: Filter records based on conditions
- `format_field`: Format field values

**Example:**
```json
{
  "data": [{"old_name": "value"}],
  "transformations": [
    {
      "type": "rename_field",
      "from": "old_name",
      "to": "new_name"
    }
  ]
}
```

### export_data

Export data in various formats with destination support.

**Parameters:**
- `data` (array, required): Data to export
- `format` (string, optional): Export format (json, csv, parquet, xlsx)
- `destination` (string, optional): Destination path or URL

**Example:**
```json
{
  "data": [{"id": 1, "name": "test"}],
  "format": "csv",
  "destination": "/tmp/export.csv"
}
```

### health_check

Get comprehensive server health status and diagnostics.

**Returns:**
- Server status and version
- Configuration validation
- External dependency health
- Performance metrics

## Integration Examples

### Claude Desktop

Add to your Claude Desktop configuration:

```json
{
  "mcpServers": {
    "my-new-template": {
      "command": "python",
      "args": ["-m", "mcp_template", "run", "my-new-template"],
      "env": {
        "CUSTOM_API_KEY": "your-api-key"
      }
    }
  }
}
```

### Continue.dev

Add to your Continue configuration:

```json
{
  "mcpServers": [
    {
      "name": "my-new-template",
      "command": ["python", "-m", "mcp_template", "run", "my-new-template"],
      "env": {
        "CUSTOM_API_KEY": "your-api-key"
      }
    }
  ]
}
```

## Development

See [Development Guide](docs/development.md) for comprehensive development documentation.

### Quick Development Setup

```bash
# Clone and setup
git clone <repository>
cd my-new-template
make setup-dev

# Run tests
make test

# Quality checks
make quality-gate

# Build and deploy
make build
make deploy-test
```

## Support

- **Documentation**: [Template docs](docs/)
- **Issues**: [GitHub Issues](https://github.com/Data-Everything/mcp-server-templates/issues)
- **Community**: [Join our Slack](https://join.slack.com/t/mcp-platform/shared_invite/zt-39z1p559j-8aWEML~IsSPwFFgr7anHRA)
- **Professional Support**: [Contact us](mailto:support@dataeverything.ai)

## License

MIT License - see [LICENSE](LICENSE) file for details.
```

## Deployment and Distribution

### Production Deployment

```bash
# Production build with optimizations
docker build --target production -t my-template:prod .

# Deploy to production environment
mcp-template deploy my-template \
  --config-file production-config.json \
  --environment production \
  --replicas 3 \
  --monitor
```

### Template Registry Submission

```bash
# Package template for distribution
mcp-template package my-template \
  --include-tests \
  --validate \
  --optimize

# Submit to template registry
mcp-template submit my-template.tar.gz \
  --category api \
  --tags "data,api,integration" \
  --license MIT
```

## Best Practices Summary

### Code Quality
- **Comprehensive Testing**: Unit, integration, and end-to-end tests
- **Error Handling**: Graceful error handling with meaningful messages
- **Type Safety**: Full type annotations with mypy validation
- **Code Style**: Consistent formatting with Black and isort
- **Documentation**: Comprehensive docstrings and user documentation

### Performance
- **Async/Await**: Non-blocking operations for scalability
- **Connection Pooling**: Efficient HTTP client management
- **Rate Limiting**: Respectful API usage patterns
- **Resource Management**: Proper cleanup and resource management

### Security
- **Input Validation**: Comprehensive parameter validation
- **Secret Management**: Secure handling of API keys and credentials
- **Principle of Least Privilege**: Minimal required permissions
- **Dependency Management**: Regular security updates

### Operations
- **Health Monitoring**: Comprehensive health checks
- **Structured Logging**: Detailed operational logging
- **Metrics Collection**: Performance and usage metrics
- **Graceful Degradation**: Resilient error handling

---

**Next Steps:**
- [Learn about testing strategies](testing.md)
- [Explore deployment options](../cli/deploy.md)
- [View integration examples](../examples/integrations.md)
- [Contribute to the platform](../guides/contributing.md)
