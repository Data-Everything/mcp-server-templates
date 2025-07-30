"""
Setup script for MCP server templates package.
"""

from setuptools import find_packages, setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="mcp-templates",
    version="0.1.1",
    author="Data Everything",
    author_email="tooling@dataeverything.com",
    description="Deploy MCP server templates with zero configuration",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Data-Everything/mcp-server-templates",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Systems Administration",
    ],
    python_requires=">=3.10",
    install_requires=[
        "rich>=13.0.0",
    ],
    entry_points={
        "console_scripts": [
            "mcp-template=mcp_template:main",
        ],
    },
    keywords="mcp, model-context-protocol, ai, deployment, docker, templates",
    project_urls={
        "Bug Reports": "https://github.com/Data-Everything/mcp-server-templates/issues",
        "Source": "https://github.com/Data-Everything/mcp-server-templates",
        "Documentation": "https://github.com/Data-Everything/mcp-server-templates#readme",
    },
)
