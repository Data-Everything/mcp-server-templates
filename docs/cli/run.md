# Run Command

The `run` command starts MCP server templates with specific transport and configuration options.

## Usage

```bash
mcpt run [options]
```

## Options

### Transport Options
- `--transport {http,stdio}`: Choose transport method (default: stdio)
- `--port PORT`: Port number for HTTP transport (default: 3000)

### Directory Options
- `--data-dir DATA_DIR`: Directory for persistent data storage
- `--config-dir CONFIG_DIR`: Directory for configuration files

### General Options
- `-h, --help`: Show help message and exit

## Transport Methods

### STDIO Transport
The default transport method using standard input/output:

```bash
mcpt run
mcpt run --transport stdio
```

**Use cases:**
- Direct integration with MCP clients
- Process-to-process communication
- Local development and testing

### HTTP Transport
HTTP-based transport for web integration:

```bash
mcpt run --transport http --port 8080
```

**Use cases:**
- Web service integration
- Remote access to MCP servers
- API-style interactions

## Configuration

### Data Directory
Specify where template data is stored:

```bash
mcpt run --data-dir /path/to/data
```

### Config Directory
Set configuration file location:

```bash
mcpt run --config-dir /path/to/config
```

## Examples

Run with default settings (STDIO):
```bash
mcpt run
```

Run HTTP server on port 8080:
```bash
mcpt run --transport http --port 8080
```

Run with custom directories:
```bash
mcpt run --data-dir ./data --config-dir ./config
```

Full configuration example:
```bash
mcpt run \
  --transport http \
  --port 9000 \
  --data-dir /opt/mcp/data \
  --config-dir /opt/mcp/config
```

## Prerequisites

- Template must be properly configured
- Required ports must be available (for HTTP transport)
- Data and config directories must be accessible

## Related Commands

- [`deploy`](deploy.md) - Deploy templates for containerized running
- [`interactive`](interactive.md) - Interactive mode with enhanced tool access
- [`config`](config.md) - Configure template settings
