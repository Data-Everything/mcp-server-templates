FROM python:3.11-slim

LABEL maintainer="Data Everything <tooling@dataeverything.com>"
LABEL description="Demo MCP Server using FastMCP"
LABEL version="1.0.0"

# Set working directory
WORKDIR /data

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends     && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy demo template source code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash mcp
RUN chown -R mcp:mcp /data
USER mcp

# Expose the default HTTP port
EXPOSE 7071

# Set environment variables
ENV LOG_LEVEL=info
