FROM mgoltzsche/podman:5.5.2
LABEL maintainer="dataeverything"
LABEL tool="mcp-template"
LABEL tool-shorthand="mcpt"
LABEL backend="docker"
LABEL description="MCP Server Templates for rapid deployment and management of AI servers with Docker, Kubernetes, or Mock backends."
LABEL original-backend="podman"

# Install pythhon and cleanup to keep image size small
RUN apk add --no-cache python3 py3-pip && \
    rm -rf /var/cache/apk/* && \
    ln -sf python3 /usr/bin/python
# Install dependencies
WORKDIR /app
COPY mcp_template /app/mcp_template
COPY pyproject.toml /app/
COPY README.md /app/
RUN python3 -m venv /app/venv && \
    . /app/venv/bin/activate && \
    pip install --no-cache-dir -e .
ENV PATH="/app/venv/bin:$PATH"

# Set the entrypoint to the CLI tool
ENTRYPOINT ["mcpt"]
