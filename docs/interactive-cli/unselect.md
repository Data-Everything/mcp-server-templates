# `unselect` Command

Unselect the currently selected template.

## Functionality
- Clears the session template selection
- Commands will require explicit template names again
- Resets the CLI prompt to normal mode

## Options & Arguments
- No arguments required

## Configuration
- No configuration required

## Example
```
unselect
```

### Sample Output
```
✅ Template unselected
mcpt>
```

## When and How to Run
- Use when you want to work with multiple templates in the same session
- Run when you no longer want a default template selected
- Useful before switching to work with different templates

## Related Commands
- `select <template>` - Select a template for the session
- `templates` - List available templates
