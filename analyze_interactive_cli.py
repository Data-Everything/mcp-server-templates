#!/usr/bin/env python3
"""
Script to analyze the InteractiveCLI class and identify all methods that need testing.
"""

import sys
import os
import inspect

# Add the project path to sys.path
project_path = "/home/samarora/data-everything/mcp-server-templates"
sys.path.insert(0, project_path)

try:
    from mcp_template.interactive_cli import (
        InteractiveCLI,
        ResponseBeautifier,
        start_interactive_cli,
        merge_config_sources,
    )

    print("=== InteractiveCLI Class Analysis ===\n")

    # Get all methods from InteractiveCLI
    cli_methods = inspect.getmembers(InteractiveCLI, predicate=inspect.isfunction)

    # Separate command methods from helper methods
    command_methods = []
    helper_methods = []

    for name, method in cli_methods:
        if name.startswith("do_"):
            command_methods.append((name, method))
        elif name.startswith("_") or name in ["cmdloop", "default", "emptyline"]:
            helper_methods.append((name, method))
        else:
            helper_methods.append((name, method))

    print(f"Found {len(command_methods)} command methods:")
    for name, method in command_methods:
        # Get docstring
        doc = method.__doc__ or "No docstring"
        print(f"  - {name}: {doc.split('.')[0]}")

    print(f"\nFound {len(helper_methods)} helper/utility methods:")
    for name, method in helper_methods:
        doc = method.__doc__ or "No docstring"
        print(f"  - {name}: {doc.split('.')[0] if doc else 'No docstring'}")

    print("\n=== ResponseBeautifier Class Analysis ===\n")

    # Get all methods from ResponseBeautifier
    beautifier_methods = inspect.getmembers(
        ResponseBeautifier, predicate=inspect.isfunction
    )

    public_methods = []
    private_methods = []

    for name, method in beautifier_methods:
        if name.startswith("_"):
            private_methods.append((name, method))
        else:
            public_methods.append((name, method))

    print(f"Found {len(public_methods)} public methods:")
    for name, method in public_methods:
        doc = method.__doc__ or "No docstring"
        print(f"  - {name}: {doc.split('.')[0] if doc else 'No docstring'}")

    print(f"\nFound {len(private_methods)} private/helper methods:")
    for name, method in private_methods:
        doc = method.__doc__ or "No docstring"
        print(f"  - {name}: {doc.split('.')[0] if doc else 'No docstring'}")

    print("\n=== Module Level Functions ===\n")

    module_functions = [
        ("merge_config_sources", merge_config_sources),
        ("start_interactive_cli", start_interactive_cli),
    ]

    for name, func in module_functions:
        doc = func.__doc__ or "No docstring"
        print(f"  - {name}: {doc.split('.')[0] if doc else 'No docstring'}")

    print("\n=== Test Coverage Plan ===\n")

    test_categories = {
        "Unit Tests - InteractiveCLI Commands": command_methods,
        "Unit Tests - InteractiveCLI Helpers": [
            m for m in helper_methods if not m[0].startswith("__")
        ],
        "Unit Tests - ResponseBeautifier Public": public_methods,
        "Unit Tests - ResponseBeautifier Helpers": private_methods[
            :5
        ],  # Test key helper methods
        "Unit Tests - Module Functions": module_functions,
        "Integration Tests - Command Flow": [
            ("command_validation", "Test command parsing and validation"),
            ("config_management_flow", "Test configuration management workflow"),
            ("tool_calling_flow", "Test tool calling workflow"),
            ("server_management_flow", "Test server management workflow"),
        ],
    }

    for category, methods in test_categories.items():
        print(f"{category}:")
        for name, method in methods[:5]:  # Show first 5
            print(f"  - test_{name.replace('do_', '')}")
        if len(methods) > 5:
            print(f"  ... and {len(methods) - 5} more tests")
        print()

except Exception as e:
    print(f"Error analyzing InteractiveCLI: {e}")
    import traceback

    traceback.print_exc()
