# Shell Command

The `shell` command opens an interactive shell inside a deployed template's container, allowing you to debug and inspect the running environment.

## Usage

```bash
mcpt shell [template_name]
```

## Arguments

- `template_name` (optional): Name of the template to open shell in. If not provided, uses default naming.

## Description

This command provides direct access to the container environment where your MCP server template is running. It's particularly useful for:

- Debugging deployment issues
- Inspecting the runtime environment
- Testing configurations interactively
- Troubleshooting server behavior

## Examples

Open shell in default template container:
```bash
mcpt shell
```

Open shell in specific template deployment:
```bash
mcpt shell my-github-server
```

## Prerequisites

- Template must be deployed first using `mcpt deploy`
- Docker must be running
- Template container must be active

## Related Commands

- [`deploy`](deploy.md) - Deploy a template first
- [`logs`](logs.md) - View container logs
- [`stop`](stop.md) - Stop template deployment
