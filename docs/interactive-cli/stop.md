# `stop` Command

Stop deployments.

## Functionality
- Stops running server deployments
- Prompts for confirmation unless forced
- Can stop individual or multiple deployments
- Gracefully shuts down services

## Options & Arguments
- `[target]`: Target deployment ID or name (optional)
- `--all`: Stop all deployments
- `--template NAME`: Stop deployments for specific template
- `--force`: Force stop without confirmation

## Configuration
- No configuration required

## Example
```
stop abc123def456
stop --all
stop --template github
stop my-deployment --force
```

### Sample Output
```
🛑 Stopping deployment: abc123def456
⚠️  Are you sure you want to stop this deployment? [y/N]: y
✅ Deployment stopped successfully
```

## When and How to Run
- Use when you need to shut down servers
- Run before removing deployments
- Use for resource cleanup or maintenance

## Related Commands
- `servers` - List running deployments
- `remove` - Remove stopped deployments
- `status` - Check deployment status
- `cleanup` - Clean up resources
