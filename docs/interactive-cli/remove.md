# `remove` Command

Remove deployments.

## Functionality
- Removes server deployments and associated resources
- Prompts for confirmation unless forced
- Can remove individual or multiple deployments
- Cleans up containers, volumes, and networks

## Options & Arguments
- `<target>`: Target deployment ID or name
- `--all`: Remove all deployments
- `--template NAME`: Remove deployments for specific template
- `--force`: Force removal without confirmation

## Configuration
- No configuration required

## Example
```
remove abc123def456
remove --all
remove --template github
remove my-deployment --force
```

### Sample Output
```
🗑️  Removing deployment: abc123def456
⚠️  This will permanently delete the deployment. Continue? [y/N]: y
✅ Deployment removed successfully
🧹 Cleaned up associated resources
```

## When and How to Run
- Use to permanently delete deployments
- Run after stopping deployments
- Use for cleanup and resource management

## Related Commands
- `stop` - Stop deployments first
- `servers` - List deployments to remove
- `cleanup` - Clean up additional resources
- `status` - Check available resources
