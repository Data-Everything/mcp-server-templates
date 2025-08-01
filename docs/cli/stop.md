# stop

**Stop one or more MCP template deployments.**

## Synopsis

```bash
mcp-template stop [TEMPLATE] [--name NAME] [--all]
```

## Description

The `stop` command allows you to stop a specific deployment, all deployments of a template, or all deployments across all templates. You can target deployments by template name, by custom container name, or stop everything at once using `--all`.

## Options

| Option         | Description                                                                 | Default |
|----------------|-----------------------------------------------------------------------------|---------|
| `TEMPLATE`     | Template name to stop (optional if --name or --all is provided)             | None    |
| `--name NAME`  | Custom container name (stop a specific deployment by name)                  | None    |
| `--all`        | Stop all deployments of this template, or all templates if no template given | False   |

## Examples

### Stop a specific template deployment

```bash
mcp-template stop file-server
```

### Stop a deployment by custom container name

```bash
mcp-template stop --name mcp-file-server-abc123
```

### Stop all deployments of a template

```bash
mcp-template stop file-server --all
```

### Stop all deployments across all templates

```bash
mcp-template stop --all
```

## Output

- ✅ Success: `[green]✅ Stopped <container-name>[/green]`
- ⚠️  Not found: `[yellow]⚠️  No running deployments found for <template>[/yellow]`
- ❌ Error: `[red]❌ Error stopping <template>: <error>[/red]`

## Usage Notes

- You must provide at least one of: `TEMPLATE`, `--name`, or `--all`.
- If no arguments are provided, the command will show an error and exit.
- `--all` without a template stops all deployments in the system.
- You can combine `TEMPLATE` and `--all` to stop all deployments of a specific template.
- Use `--name` to stop a deployment by its exact container name.

## See Also

- [list](list.md) - List templates and deployments
- [deploy](deploy.md) - Deploy templates
- [logs](logs.md) - View deployment logs
