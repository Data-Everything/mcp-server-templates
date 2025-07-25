FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/

# Set environment variables
ENV MCP_HELLO_FROM="MCP Platform"
ENV MCP_LOG_LEVEL="info"

# Run the MCP server
CMD ["python", "-m", "src.server"]
