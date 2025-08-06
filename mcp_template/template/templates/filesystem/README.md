# Filesystem

Local filesystem access with configurable allowed paths.

## Features

- **example**: A simple example tool


## Configuration

This template supports the following configuration parameters:

- `log_level`: Logging level (DEBUG, INFO, WARNING, ERROR)


## Usage

1. Deploy the template using the MCP platform
2. Configure the required parameters
3. Connect your MCP client to the deployed server

## Development

### Running Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Run the server
python -m server
```

### Running Tests

```bash
# Run template-specific tests
pytest templates/filesystem/tests/
```

## Docker

```bash
# Build the image
docker build -t dataeverything/mcp-filesystem .

# Run the container
docker run -p 8000:8000 dataeverything/mcp-filesystem
```

## Author

Sam Arora

## Version

1.0.0
