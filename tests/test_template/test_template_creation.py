#!/usr/bin/env python3
"""
Test script to verify template creation functionality.
"""

import shutil
import subprocess
import sys
from pathlib import Path


def test_template_creation():
    """Test creating a simple template and verify its structure."""
    template_name = "test-simple"

    # Remove existing test template if it exists
    templates_dir = Path("templates")
    test_dir = Path("tests/templates")

    if (templates_dir / template_name).exists():
        shutil.rmtree(templates_dir / template_name)

    if (test_dir / template_name).exists():
        shutil.rmtree(test_dir / template_name)

    print(f"Creating template: {template_name}")

    # Test with minimal inputs
    process = subprocess.Popen(
        [sys.executable, "-m", "mcp_deploy", "create", template_name],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    # Provide minimal inputs
    inputs = [
        "Simple Test Template",  # Template display name
        "A simple test template for validation",  # Description
        "1.0.0",  # Version
        "Test Author",  # Author
        "dataeverything/mcp-test-simple",  # Docker image
        "",  # Confirm (Enter to accept)
    ]

    stdout, stderr = process.communicate("\n".join(inputs))

    print("STDOUT:", stdout)
    print("STDERR:", stderr)
    print("Return code:", process.returncode)

    # Verify template directory structure
    template_dir = templates_dir / template_name
    expected_files = [
        "Dockerfile",
        "README.md",
        "template.json",
        "USAGE.md",
        "requirements.txt",
        "src/server.py",
        "src/__init__.py",
    ]

    for file_path in expected_files:
        full_path = template_dir / file_path
        if not full_path.exists():
            print(f"❌ Missing file: {file_path}")
        else:
            print(f"✅ Found file: {file_path}")

    # Verify test directory structure
    test_template_dir = test_dir / template_name
    expected_test_files = [
        "__init__.py",
        "conftest.py",
        f"test_{template_name.replace('-', '_')}_unit.py",
        f"test_{template_name.replace('-', '_')}_integration.py",
    ]

    for file_path in expected_test_files:
        full_path = test_template_dir / file_path
        if not full_path.exists():
            print(f"❌ Missing test file: {file_path}")
        else:
            print(f"✅ Found test file: {file_path}")

    # Check test coverage
    print("\n🧪 Running test coverage check...")
    try:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                f"tests/templates/{template_name}",
                "--cov=templates/" + template_name,
                "--cov-report=term-missing",
                "--tb=short",
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )

        print("Test output:", result.stdout)
        if result.stderr:
            print("Test errors:", result.stderr)

    except subprocess.TimeoutExpired:
        print("❌ Tests timed out")
    except Exception as e:
        print(f"❌ Test execution failed: {e}")


if __name__ == "__main__":
    test_template_creation()
