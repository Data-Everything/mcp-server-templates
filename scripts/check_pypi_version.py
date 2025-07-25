#!/usr/bin/env python3
"""
Script to check PyPI for existing versions and auto-increment if needed.
"""

import json
import re
import sys
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen


def get_current_version():
    """Get the current version from setup.py."""
    setup_file = Path(__file__).parent.parent / "setup.py"

    with open(setup_file, "r", encoding="utf-8") as f:
        content = f.read()

    # Extract version from setup.py
    version_match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
    if not version_match:
        raise ValueError("Could not find version in setup.py")

    return version_match.group(1)


def get_pypi_versions(package_name):
    """Get all versions available on PyPI for a package."""
    url = f"https://pypi.org/pypi/{package_name}/json"

    try:
        request = Request(url)
        request.add_header("User-Agent", "mcp-templates-ci/1.0")

        with urlopen(request) as response:
            data = json.loads(response.read().decode("utf-8"))
            return list(data["releases"].keys())

    except HTTPError as e:
        if e.code == 404:
            print(f"Package {package_name} not found on PyPI (first release?)")
            return []
        else:
            raise


def parse_version(version_str):
    """Parse a version string into a tuple of integers."""
    try:
        return tuple(map(int, version_str.split(".")))
    except ValueError:
        # Handle pre-release versions, etc.
        return tuple(map(int, re.findall(r"\d+", version_str)))


def increment_version(version_str):
    """Increment the patch version number."""
    parts = version_str.split(".")

    if len(parts) >= 3:
        # Increment patch version (third part)
        parts[2] = str(int(parts[2]) + 1)
    elif len(parts) == 2:
        # Add patch version if only major.minor
        parts.append("1")
    else:
        # Fallback for unusual version formats
        parts[-1] = str(int(parts[-1]) + 1)

    return ".".join(parts)


def update_setup_version(new_version):
    """Update the version in setup.py."""
    setup_file = Path(__file__).parent.parent / "setup.py"

    with open(setup_file, "r", encoding="utf-8") as f:
        content = f.read()

    # Replace version string
    updated_content = re.sub(
        r'(version\s*=\s*["\'])([^"\']+)(["\'])', rf"\g<1>{new_version}\g<3>", content
    )

    with open(setup_file, "w", encoding="utf-8") as f:
        f.write(updated_content)

    print(f"✅ Updated setup.py version to {new_version}")


def main():
    """Main function."""
    package_name = "mcp-templates"  # Our package name on PyPI

    print(f"🔍 Checking PyPI versions for {package_name}...")

    # Get current version from setup.py
    current_version = get_current_version()
    print(f"📦 Current version in setup.py: {current_version}")

    # Get PyPI versions
    pypi_versions = get_pypi_versions(package_name)

    if not pypi_versions:
        print("✅ No existing versions on PyPI, proceeding with current version")
        return

    print(f"🔍 Found {len(pypi_versions)} versions on PyPI")

    # Check if current version exists
    if current_version in pypi_versions:
        print(f"❌ Version {current_version} already exists on PyPI")

        # Find the latest version
        valid_versions = []
        for v in pypi_versions:
            try:
                parsed = parse_version(v)
                valid_versions.append((parsed, v))
            except (ValueError, TypeError):
                continue

        if valid_versions:
            valid_versions.sort(reverse=True)
            latest_version = valid_versions[0][1]
            print(f"📈 Latest version on PyPI: {latest_version}")

            # Choose version to increment from
            version_to_increment = max(
                current_version, latest_version, key=parse_version
            )
            new_version = increment_version(version_to_increment)

            print(f"🚀 Auto-incrementing to: {new_version}")
            update_setup_version(new_version)
        else:
            # Fallback: increment current version
            new_version = increment_version(current_version)
            print(f"🚀 Incrementing current version to: {new_version}")
            update_setup_version(new_version)
    else:
        print(f"✅ Version {current_version} is available on PyPI")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, IOError, HTTPError) as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
