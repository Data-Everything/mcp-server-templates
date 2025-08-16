# Changelog

All notable changes to MCP Server Templates will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2025-07-26

### 🚀 Major Refactor - FastMCP Integration & HTTP-First Architecture

This release represents a significant refactoring of the MCP Platform to align with modern MCP server development practices, focusing on the demo template as a reference implementation.

### Added

#### FastMCP Integration
- **NEW**: Integration with FastMCP framework (>=2.10.0) for standardized MCP server development
- **NEW**: `BaseMCPServer` base class in `mcp_template/base.py` for consistent template implementation
- **NEW**: HTTP-first transport with stdio fallback support
- **NEW**: FastMCP decorators for tool definitions (`@mcp.tool()`)
- **NEW**: Middleware support for authentication and logging

#### Enhanced CLI Commands
- **NEW**: `mcp config <template>` - Show all configuration options including double-underscore notation
- **NEW**: `mcp tools <template>` - List available tools for a template
- **NEW**: `mcp connect <template> [--llm <llm>]` - Show integration examples for LLMs and frameworks
- **NEW**: `mcp run <template> [--transport http|stdio]` - Run template with transport options
- **NEW**: Double-underscore configuration notation (e.g., `--config demo__hello_from=value`)

#### Demo Template Refactor
- **NEW**: Completely refactored demo template using FastMCP best practices
- **NEW**: Modular structure: `config.py`, `server.py`, `tools.py`
- **NEW**: HTTP transport as default (port 7071) with stdio fallback
- **NEW**: Comprehensive test suite with unit and integration tests
- **NEW**: Enhanced Docker configuration with health checks

#### Docker Networking
- **NEW**: Automatic Docker network creation (`mcp-platform`)
- **NEW**: Container naming with endpoint path support
- **NEW**: Network-aware deployment with `--docker --http` flags

#### Integration Examples
- **NEW**: FastMCP client integration examples
- **NEW**: Claude Desktop configuration templates
- **NEW**: VS Code MCP integration setup
- **NEW**: Direct HTTP API testing with cURL
- **NEW**: Python async client examples

### Enhanced

#### Configuration System
- **ENHANCED**: Multi-source configuration with precedence (env > cli > file > defaults)
- **ENHANCED**: Automatic type conversion based on JSON schema
- **ENHANCED**: Nested configuration support with dot notation
- **ENHANCED**: Environment variable mapping improvements

#### Template Discovery
- **ENHANCED**: Templates now include transport information
- **ENHANCED**: Tools metadata integration for CLI discovery
- **ENHANCED**: Enhanced template validation and error reporting

#### CLI User Experience
- **ENHANCED**: Rich console output with improved formatting
- **ENHANCED**: Better error messages and troubleshooting guidance
- **ENHANCED**: Progress indicators for deployment operations
- **ENHANCED**: Comprehensive help and usage examples

### Technical Improvements

#### Code Organization
- **NEW**: `mcp_template/cli.py` - Enhanced CLI functionality
- **NEW**: `mcp_template/base.py` - Base server class
- **REFACTORED**: Template structure following best practices
- **IMPROVED**: Test coverage and organization

#### Dependencies
- **ADDED**: `fastmcp>=2.10.0` - Core FastMCP framework
- **MAINTAINED**: `rich>=13.0.0` - Console UI framework
- **MAINTAINED**: `pyyaml` - YAML configuration support

#### Documentation
- **NEW**: Comprehensive README for demo template
- **NEW**: API integration examples and guides
- **NEW**: Architecture documentation
- **ENHANCED**: Code documentation with type hints and docstrings

### Demo Template Features

The refactored demo template showcases:

#### Tools
- `say_hello(name?: string)` - Generate personalized greetings
- `get_server_info()` - Return comprehensive server metadata
- `echo_message(message: string)` - Echo messages with server identification

#### Configuration
- `hello_from` - Customizable greeting source (default: "MCP Platform")
- `log_level` - Logging level (debug, info, warning, error)
- Environment mapping: `MCP_HELLO_FROM`, `MCP_LOG_LEVEL`

#### Transport Options
- **HTTP** (default): `http://localhost:7071` with REST API
- **Stdio**: Standard input/output for direct integration

### Migration Guide

#### For Existing Users
1. Update dependencies: `pip install -r requirements.txt`
2. Templates moved from `templates_old/` to `templates/`
3. New CLI commands available: `config`, `tools`, `connect`, `run`
4. HTTP transport now available alongside stdio

#### For Template Developers
1. Use `BaseMCPServer` as base class
2. Implement tools using FastMCP decorators
3. Follow modular structure: `config.py`, `server.py`, `tools.py`
4. Add transport information to `template.json`

### Breaking Changes

⚠️ **Note**: This is a major refactor focused on the demo template. Other templates remain in `templates_old/` and will be migrated in future releases.

- Demo template completely rewritten (breaking changes for direct usage)
- New dependency on FastMCP framework
- Template structure changes for new templates

### Roadmap

#### Next Steps (as per strategy document)
1. **Week 1**: ✅ Demo template refactor, CLI enhancements, Docker networking
2. **Week 2**: 📋 Comprehensive testing, documentation updates, template scaling

#### Future Releases
- Web dashboard for non-technical users
- Template marketplace integration

### Acknowledgments

This refactor implements the strategy outlined in `refactor_strategy.md`, focusing on:
- FastMCP integration for consistency and maturity
- HTTP-first approach for scalability
- Enhanced CLI for developer experience
- Modular architecture for maintainability

The demo template serves as a reference implementation for future template development and showcases the full capabilities of the MCP Platform architecture.

---

## [1.0.0] - 2025-01-XX

### Added
- Initial release of MCP Server Templates
- Docker-based deployment system
- Template discovery and validation
- CLI interface for template management
- Basic template collection (demo, file-server, github, database)

### Features
- Zero-configuration deployment
- Multi-source configuration support
- Template-based MCP server deployment
- Docker container management
- Rich CLI interface
