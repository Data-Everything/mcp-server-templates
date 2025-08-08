# run-tool (Deprecated)

⚠️ **This command has been deprecated and removed.**

## Migration Notice

The `run-tool` command is no longer available. Please use the `call` command in interactive mode instead.

### Old Usage (No Longer Works)
```bash
mcpt run-tool  # ❌ Deprecated
```

### New Usage (Recommended)
```bash
mcpt interactive
# Then in interactive mode:
mcpt> call [tool-name] [arguments]
```

## Why the Change?

The `run-tool` command was replaced with the more powerful interactive CLI that provides:

- Better tool discovery and management
- Enhanced error handling
- Real-time feedback
- Session persistence
- Improved user experience

## Migration Guide

1. **Start interactive mode**:
   ```bash
   mcpt interactive
   ```

2. **Use the call command**:
   ```bash
   mcpt> call list_repositories
   mcpt> call create_issue --title "Bug fix" --body "Description"
   ```

3. **Exit when done**:
   ```bash
   mcpt> exit
   ```

## Related Documentation

- [Interactive CLI](interactive.md) - Learn about the interactive mode
- [Call Command](../interactive-cli/call.md) - Documentation for the call command
- [FAQ](../faq.md) - Common questions

## Need Help?

If you have questions about migrating from `run-tool` to the new interactive CLI, please:

- Check the [Interactive CLI documentation](../interactive-cli/)
- Join our [Discord community](https://discord.gg/55Cfxe9gnr)
- Review the [FAQ](../faq.md)
