# `configure` Command

Set configuration for a template interactively.

## Functionality
- Stores configuration in session and cache.
- Masks sensitive values in output.
- Supports multiple config values at once.

## Options & Arguments
- `<template_name>`: Name of the template to configure.
- `<key>=<value>`: Configuration key-value pairs (multiple allowed).

## Configuration
- Used to set or update template configuration.
- Sensitive values (e.g., passwords, tokens) are masked in output.

## Example
```
configure my_template api_key=12345 endpoint=https://api.example.com
```

## When and How to Run
- Use before calling tools that require configuration.
- Run any time to update or set config values for a template.
