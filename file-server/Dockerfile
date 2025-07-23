# MCP File Server Template - extends official filesystem server
FROM node:20-alpine AS base

# Install the official MCP filesystem server
RUN npm install -g @modelcontextprotocol/server-filesystem

# Add platform-specific configurations and security enhancements
WORKDIR /app

# Copy platform integration files
COPY package.json ./
COPY src/ ./src/
COPY config/ ./config/

# Install any additional dependencies for platform integration
RUN npm install

# Create non-root user for security
RUN addgroup -g 1001 -S mcp && \
    adduser -S mcp -u 1001

# Set up secure directories
RUN mkdir -p /data /workspace /logs && \
    chown -R mcp:mcp /data /workspace /logs && \
    chmod 755 /data /workspace /logs

# Switch to non-root user
USER mcp

# Environment variables for filesystem server
ENV NODE_ENV=production
ENV MCP_ALLOWED_DIRS=/data:/workspace
ENV MCP_READ_ONLY=false

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD node src/health-check.js || exit 1

# Default command runs the filesystem server with platform config
CMD ["node", "src/platform-wrapper.js"]

# Expose port (though MCP typically uses stdio)
EXPOSE 8000

# Volume mounts
VOLUME ["/data", "/workspace", "/logs"]

# Labels for platform integration
LABEL maintainer="MCP Platform <support@mcp-platform.ai>"
LABEL description="Secure file system access for AI assistants"
LABEL version="1.0.0"
LABEL mcp.template="file-server"
LABEL mcp.base-server="@modelcontextprotocol/server-filesystem"
