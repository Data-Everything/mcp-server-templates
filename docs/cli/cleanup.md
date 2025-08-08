# Cleanup Command

The `cleanup` command removes deployed template containers and associated resources to free up system space.

## Usage

```bash
mcpt cleanup [template_name]
mcpt cleanup --all
```

## Options

- `--all`: Remove all deployed templates and resources
- `-h, --help`: Show help message

## Arguments

- `template_name` (optional): Specific template deployment to clean up

## Description

This command performs cleanup operations to remove:

- Stopped and running template containers
- Associated Docker volumes and networks
- Temporary files and configurations
- Deployment metadata

Use this command to:
- Free up disk space
- Remove old or unused deployments
- Clean up after testing
- Resolve deployment conflicts

## Examples

Clean up specific template:
```bash
mcpt cleanup my-github-server
```

Clean up all templates:
```bash
mcpt cleanup --all
```

## Behavior

- **Specific cleanup**: Removes only the specified template deployment
- **All cleanup**: Removes all template deployments created by mcp-template
- **Safe operation**: Confirms before removing critical resources
- **Thorough**: Cleans up containers, volumes, networks, and metadata

## Related Commands

- [`list`](list.md) - See active deployments before cleanup
- [`stop`](stop.md) - Stop templates before cleanup
- [`deploy`](deploy.md) - Deploy new templates after cleanup
