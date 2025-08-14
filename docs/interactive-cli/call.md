# `call` Command

Call a tool from a template (via stdio or HTTP transport).

## Functionality
- Executes the specified tool, prompting for missing configuration if needed.
- Handles both stdio and HTTP transports.
- Displays results in user-friendly tabular format by default.
- Provides raw JSON output when using the `--raw` flag.

## Syntax
```
call [options] <template_name> <tool_name> [json_args]
```

## Options & Arguments
- `<template_name>`: Name of the template to use.
- `<tool_name>`: Name of the tool to call.
- `[json_args]`: Optional JSON string of arguments for the tool (e.g. '{"param": "value"}').

### Options
- `-c, --config-file`: Path to JSON config file
- `-e, --env`: Environment variables (KEY=VALUE format, can be used multiple times)
- `-C, --config`: Temporary config KEY=VALUE pairs (can be used multiple times)
- `-NP, --no-pull`: Do not pull the Docker image
- `-R, --raw`: Show raw JSON response instead of formatted table

## Configuration
- Configuration for the template may be required; CLI will prompt if missing.
- For HTTP templates, server must be running.

## Examples

### Basic call with tabular output (default)
```
call demo say_hello '{"name": "Sam"}'
```

### Using raw JSON output
```
call --raw demo say_hello '{"name": "Sam"}'
```

### With configuration options
```
call --config-file config.json --env API_KEY=xyz demo my_tool '{"input": "value"}'
```

## When and How to Run
- Use to execute a tool from a deployed template.
- Run after configuring the template and ensuring the server is running (for HTTP transport).

## Example Output

### Default Tabular Format
```
mcpt> call demo say_hello {"name": "Sam"}
🚀 Calling tool 'say_hello' from template 'demo'
Checking for running server (HTTP first, stdio fallback)...
                     🎯 say_hello Results                     
╭──────────────┬─────────────────────────────────────────────╮
│ Type         │ Content                                     │
├──────────────┼─────────────────────────────────────────────┤
│ text         │ Hello Sam! Greetings from "MCP Platform"!  │
╰──────────────┴─────────────────────────────────────────────╯
```

### Raw JSON Format (--raw flag)
```
mcpt> call --raw demo say_hello {"name": "Sam"}
🚀 Calling tool 'say_hello' from template 'demo'
Checking for running server (HTTP first, stdio fallback)...
Tool Result: say_hello
├── content
│   └── [0]
│       ├── type: text
│       └── text: Hello Sam! Greetings from "MCP Platform"!
├── structuredContent
│   └── result: Hello Sam! Greetings from "MCP Platform"!
└── isError: ✗
```
