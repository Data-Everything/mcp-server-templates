# MCP File Server Template - FastMCP Pure Python Implementation
FROM python:3.11-slim AS base

# Set working directory
WORKDIR /app

# Copy requirements first for better layer caching
COPY requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY src/ ./src/
COPY config/ ./config/

# Create non-root user for security
RUN addgroup --gid 1001 --system mcp && \
    adduser --system --uid 1001 --gid 1001 mcp

# Set up secure directories with proper permissions
RUN mkdir -p /data /workspace /logs && \
    chown -R mcp:mcp /data /workspace /logs /app && \
    chmod 755 /data /workspace /logs

# Switch to non-root user
USER mcp

# Environment variables for filesystem server
ENV PYTHONPATH=/app
ENV MCP_ALLOWED_DIRS=/data:/workspace
ENV MCP_READ_ONLY=false

# Health check - using the FastMCP server version check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python src/server.py --version > /dev/null || exit 1

# Default command runs the FastMCP filesystem server
CMD ["python", "src/server.py"]

# Volume mounts
VOLUME ["/data", "/workspace", "/logs"]

# Labels for platform integration
LABEL maintainer="MCP Platform <support@mcp-platform.ai>"
LABEL description="Secure file system access for AI assistants - FastMCP Python Implementation"
LABEL version="2.0"
LABEL language="python"
LABEL version="1.0.0"
LABEL mcp.template="file-server"
LABEL mcp.base-server="@modelcontextprotocol/server-filesystem"
