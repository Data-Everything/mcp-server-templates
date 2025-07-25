#!/usr/bin/env python3
"""
Documentation builder for MCP Server Templates.

This script:
1. Scans all template directories for docs/index.md files
2. Generates navigation for template documentation
3. Copies template docs to the main docs directory
4. Builds the documentation with mkdocs
"""

import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict

import yaml


def cleanup_old_docs(docs_dir: Path):
    """Clean up old generated documentation."""
    print("🧹 Cleaning up old docs...")

    templates_docs_dir = docs_dir / "server-templates"
    if templates_docs_dir.exists():
        for item in templates_docs_dir.iterdir():
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()
        print("  🗑️  Cleaned up old server-templates docs")


def scan_template_docs(templates_dir: Path) -> Dict[str, Dict]:
    """Scan template directories for documentation."""
    print("🔍 Scanning template directories for documentation...")

    template_docs = {}

    for template_dir in templates_dir.iterdir():
        if not template_dir.is_dir():
            continue

        template_name = template_dir.name
        docs_index = template_dir / "docs" / "index.md"
        template_json = template_dir / "template.json"

        if docs_index.exists() and template_json.exists():
            # Load template metadata
            try:
                import json

                with open(template_json) as f:
                    template_config = json.load(f)

                template_docs[template_name] = {
                    "name": template_config.get("name", template_name.title()),
                    "description": template_config.get("description", ""),
                    "docs_file": docs_index,
                    "config": template_config,
                }
                print(f"  ✅ Found docs for {template_name}")
            except Exception as e:
                print(f"  ⚠️  Error reading {template_name} config: {e}")
        else:
            print(f"  ❌ Missing docs for {template_name}")

    print(f"📋 Found documentation for {len(template_docs)} templates")
    return template_docs


def copy_template_docs(template_docs: Dict[str, Dict], docs_dir: Path):
    """Copy template documentation to docs directory."""
    print("� Copying template documentation...")

    templates_docs_dir = docs_dir / "server-templates"
    templates_docs_dir.mkdir(exist_ok=True)

    for template_id, template_info in template_docs.items():
        template_doc_dir = templates_docs_dir / template_id
        template_doc_dir.mkdir(exist_ok=True)

        # Copy the index.md file
        dest_file = template_doc_dir / "index.md"
        shutil.copy2(template_info["docs_file"], dest_file)

        # Copy any other documentation files if they exist
        template_docs_source = template_info["docs_file"].parent
        for doc_file in template_docs_source.iterdir():
            if doc_file.name != "index.md" and doc_file.is_file():
                shutil.copy2(doc_file, template_doc_dir / doc_file.name)

        print(f"  📄 Copied docs for {template_id}")


def generate_templates_index(template_docs: Dict[str, Dict], docs_dir: Path):
    """Generate an index page for all templates."""
    print("📝 Generating templates index...")

    templates_docs_dir = docs_dir / "server-templates"

    # Generate the main index.md for the templates section
    index_md = templates_docs_dir / "index.md"
    index_content = """# MCP Server Templates

Welcome to the MCP Server Templates documentation! This section provides comprehensive information about available Model Context Protocol (MCP) server templates that you can use to quickly deploy MCP servers for various use cases.

## What are MCP Server Templates?

MCP Server Templates are pre-configured, production-ready templates that implement the Model Context Protocol specification. Each template is designed for specific use cases and comes with:

- 🔧 **Complete configuration files**
- 📖 **Comprehensive documentation**
- 🧪 **Built-in tests**
- 🐳 **Docker support**
- ☸️ **Kubernetes deployment manifests**

## Available Templates

Browse our collection of templates:

- [Available Templates](available.md) - Complete list of all available templates

## Quick Start

1. **Choose a template** from our [available templates](available.md)
2. **Deploy locally** using Docker Compose or our deployment tools
3. **Configure** the template for your specific needs
4. **Deploy to production** using Kubernetes or your preferred platform

## Template Categories

Our templates are organized by functionality:

- **Database Connectors** - Connect to various database systems
- **File Servers** - File management and sharing capabilities
- **API Integrations** - Third-party service integrations
- **Demo Servers** - Learning and testing examples

## Getting Help

If you need assistance with any template:

1. Check the template-specific documentation
2. Review the troubleshooting guides
3. Visit our GitHub repository for issues and discussions

## Contributing

Interested in contributing a new template? See our contribution guidelines to get started.
"""

    with open(index_md, "w", encoding="utf-8") as f:
        f.write(index_content)

    # Generate the available.md file
    available_md = templates_docs_dir / "available.md"

    content = """# Available Templates

This page lists all available MCP server templates.

"""

    # Sort templates by name
    sorted_templates = sorted(template_docs.items(), key=lambda x: x[1]["name"])

    for template_id, template_info in sorted_templates:
        content += f"""## [{template_info["name"]}]({template_id}/)

{template_info["description"]}

**Template ID:** `{template_id}`

**Version:** {template_info["config"].get("version", "1.0.0")}

**Author:** {template_info["config"].get("author", "Unknown")}

---

"""

    with open(available_md, "w", encoding="utf-8") as f:
        f.write(content)

    print("✅ Templates index generated")


def update_mkdocs_nav(template_docs: Dict[str, Dict], mkdocs_file: Path):
    """Update mkdocs.yml navigation with template pages."""
    print("⚙️  Updating mkdocs navigation...")

    with open(mkdocs_file, "r", encoding="utf-8") as f:
        mkdocs_config = yaml.safe_load(f)

    # Find the Templates section in nav
    nav = mkdocs_config.get("nav", [])

    # Build template navigation
    template_nav_items = [
        {"Overview": "server-templates/index.md"},
        {"Available Templates": "server-templates/available.md"},
    ]

    # Add individual template pages
    sorted_templates = sorted(template_docs.items(), key=lambda x: x[1]["name"])
    for template_id, template_info in sorted_templates:
        template_nav_items.append(
            {template_info["name"]: f"server-templates/{template_id}/index.md"}
        )

    # Update the nav structure
    for i, section in enumerate(nav):
        if isinstance(section, dict) and "Templates" in section:
            nav[i]["Templates"] = template_nav_items
            break

    # Write back the updated config
    with open(mkdocs_file, "w", encoding="utf-8") as f:
        yaml.dump(
            mkdocs_config,
            f,
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
            width=1000,
        )

    print("✅ MkDocs navigation updated")


def build_docs():
    """Build the documentation with mkdocs."""
    print("🏗️  Building documentation with MkDocs...")

    try:
        result = subprocess.run(
            ["mkdocs", "build"], check=True, capture_output=True, text=True
        )
        print("✅ Documentation built successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Documentation build failed: {e}")
        print(f"Stdout: {e.stdout}")
        print(f"Stderr: {e.stderr}")
        return False
    except FileNotFoundError:
        print(
            "❌ mkdocs command not found. Please install mkdocs: pip install mkdocs mkdocs-material"
        )
        return False


def main():
    """Main function to build documentation."""
    project_root = Path(__file__).parent.parent  # Go up one level from scripts/
    templates_dir = project_root / "templates"
    docs_dir = project_root / "docs"
    mkdocs_file = project_root / "mkdocs.yml"

    print("🚀 Starting documentation build process...")

    # Ensure docs directory exists
    docs_dir.mkdir(exist_ok=True)

    # Clean docs directory
    cleanup_old_docs(docs_dir)

    # Scan for template documentation
    template_docs = scan_template_docs(templates_dir)

    if not template_docs:
        print("❌ No template documentation found. Exiting.")
        sys.exit(1)

    # Copy template docs
    copy_template_docs(template_docs, docs_dir)

    # Generate templates index
    generate_templates_index(template_docs, docs_dir)

    # Update mkdocs navigation
    update_mkdocs_nav(template_docs, mkdocs_file)

    # Build documentation
    if build_docs():
        print("🎉 Documentation build completed successfully!")
        print("📁 Documentation available in site/ directory")
    else:
        print("❌ Documentation build failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
