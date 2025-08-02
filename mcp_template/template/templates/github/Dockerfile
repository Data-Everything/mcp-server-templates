# Stage 1: Extract binary from GitHub's image
FROM ghcr.io/github/github-mcp-server:0.9.1 AS github-mcp

# Stage 2: Final image with shell support
FROM alpine

# Copy binary from GitHub MCP image to Alpine
COPY --from=github-mcp /server/github-mcp-server /server/github-mcp-server

# Copy and set up the script
COPY script.sh /server/script.sh
RUN chmod +x /server/script.sh

ENTRYPOINT ["/server/script.sh"]
