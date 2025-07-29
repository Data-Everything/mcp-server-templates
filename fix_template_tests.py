#!/usr/bin/env python3
"""
Fix TemplateCreator constructor calls in test files.
"""

import re
from pathlib import Path


def fix_template_creator_calls(file_path: Path):
    """Fix TemplateCreator constructor calls in a test file."""
    with open(file_path, "r") as f:
        content = f.read()

    # Pattern to match TemplateCreator constructor calls with template_data parameter
    pattern = (
        r"TemplateCreator\(\s*template_data=([^,)]+)(?:,\s*output_dir=([^)]+))?\s*\)"
    )

    def replace_constructor(match):
        template_data = match.group(1)
        output_dir = match.group(2) if match.group(2) else "self.temp_dir"

        return f"""TemplateCreator(
            templates_dir={output_dir} / "templates",
            tests_dir={output_dir} / "tests"
        )
        creator.template_data = {template_data}"""

    # Replace all occurrences
    new_content = re.sub(pattern, replace_constructor, content)

    # Fix any remaining issues with the pattern
    new_content = re.sub(
        r"creator\.template_data = ([^)]+)\s*creator\.template_data = ([^)]+)",
        r"creator.template_data = \2",
        new_content,
    )

    if new_content != content:
        with open(file_path, "w") as f:
            f.write(new_content)
        print(f"Fixed constructor calls in {file_path}")
        return True
    return False


if __name__ == "__main__":
    test_file = Path(
        "/home/sam/data-everything/mcp-platform/mcp-server-templates/tests/test_template_creation.py"
    )
    fix_template_creator_calls(test_file)
