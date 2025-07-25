# Installation

## Requirements

- Python 3.10 or higher
- Docker (for containerized deployment)
- Git

## Install from PyPI

```bash
pip install mcp-templates
```

## Installation Methods

### Option 1: Install from PyPI (Recommended)

The simplest way to install MCP Server Templates is directly from PyPI:

```bash
# Install the latest stable version
pip install mcp-templates

# Verify installation
python -m mcp_template --version
```

**Benefits:**
- ✅ Latest stable release
- ✅ Automatic dependency management
- ✅ Works across all platforms
- ✅ No need to clone the repository

### Option 2: From Source (Development)

For development or to get the latest features:

```bash
# Clone the repository
git clone https://github.com/Data-Everything/mcp-server-templates
cd mcp-server-templates

# Install in development mode
pip install -e .

## Verify Installation

```bash
python -m mcp_template --version
python -m mcp_template list
```

You should see the available templates listed.
