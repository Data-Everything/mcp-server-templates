# Multi-stage build to create GitLab MCP server with transport selection
FROM iwakitakuma/gitlab-mcp:latest AS gitlab-mcp

# Stage 2: Final image with shell support
FROM node:22-alpine

# Install necessary packages for running Node.js application
RUN apk add --no-cache bash curl

# Copy the built application from the base image
COPY --from=gitlab-mcp /app /app

# Copy our script for transport handling
COPY script.sh /app/script.sh
RUN chmod +x /app/script.sh

# Set working directory
WORKDIR /app

# Ensure node_modules are properly set up
RUN if [ ! -d "node_modules" ]; then npm ci --ignore-scripts --omit-dev; fi

# Set default environment variables
ENV NODE_ENV=production
ENV HOST=0.0.0.0
ENV PORT=3002

# Use our script as entrypoint for transport selection
ENTRYPOINT ["/app/script.sh"]
