# `cleanup` Command

Cleanup stopped containers and unused resources.

## Functionality
- Removes stopped containers
- Cleans up unused Docker resources
- Frees up system resources
- Removes orphaned volumes and networks

## Options & Arguments
- No arguments required

## Configuration
- No configuration required

## Example
```
cleanup
```

### Sample Output
```
🧹 Cleaning up resources...
🗑️  Removed 3 stopped containers
📦 Freed 1.2GB of disk space
🔗 Cleaned up 2 unused networks
✅ Cleanup completed successfully
```

## When and How to Run
- Use periodically to free up resources
- Run after removing multiple deployments
- Use when disk space is running low
- Good practice for system maintenance

## Related Commands
- `status` - Check resource usage before cleanup
- `remove` - Remove specific deployments
- `stop` - Stop running deployments
