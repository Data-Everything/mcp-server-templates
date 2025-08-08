FROM python:3.11-slim

LABEL maintainer="Data Everything <tooling@dataeverything.com>"
LABEL description="Demo MCP Server using FastMCP"
LABEL version="1.0.0"

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy demo template source code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash mcp
RUN chown -R mcp:mcp /app
USER mcp

ENV MCP_PORT=7071

# Expose the default HTTP port
EXPOSE ${MCP_PORT}

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f "http://localhost:${MCP_PORT}/health" || exit 1

# Set environment variables
ENV MCP_LOG_LEVEL=info
ENV MCP_HELLO_FROM="MCP Platform"

RUN chmod +x script.sh

# Default command
ENTRYPOINT ["/app/script.sh"]
