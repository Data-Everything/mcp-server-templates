FROM mgoltzsche/podman:5.5.2
LABEL maintainer="dataeverything"
LABEL tool="mcp-template"
LABEL tool-shorthand="mcpt"
LABEL backend="docker"
LABEL description="MCP Server Templates for rapid deployment and management of AI servers with Docker, Kubernetes, or Mock backends."
LABEL original-backend="podman"

# Install pythhon 3.13.5 and cleanup to keep image size small
RUN apt-get update && \
    apt-get install -y python3.13 python3.13-venv python3.13-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install dependencies
WORKDIR /app
COPY mcp_template /app/mcp_template
COPY pyproject.toml /app/
COPY README.md /app/
RUN pip install --no-cache-dir -e .

# Set the entrypoint to the CLI tool
ENTRYPOINT ["mcpt"]
