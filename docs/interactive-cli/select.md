# `select` Command

Select a template for the session to avoid repeating template names.

## Functionality
- Sets the template as the default for the session
- Subsequent commands can omit the template name
- Shows confirmation with template details
- Updates the CLI prompt to show selected template

## Options & Arguments
- `<template_name>`: Name of the template to select

## Configuration
- No configuration required to select a template

## Example
```
select demo
```

### Sample Output
```
✅ Selected template: demo
mcpt(demo)>
```

## When and How to Run
- Use at the beginning of a session when working primarily with one template
- Allows you to run commands like `tools`, `configure`, `call` without specifying template name
- Run any time to switch the active template for the session

## Related Commands
- `unselect` - Clear the template selection
- `templates` - List available templates to select from
