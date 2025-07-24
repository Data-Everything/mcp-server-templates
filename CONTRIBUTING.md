# Contributing to MCP Server Templates

Thank you for your interest in contributing to the MCP Server Templates project! This guide will help you get started.

## 🚀 Quick Start for Contributors

1. **Fork** this repository
2. **Clone** your fork locally
3. **Create** a new branch for your feature/fix
4. **Make** your changes
5. **Test** locally using our scripts
6. **Submit** a pull request

## 📋 Types of Contributions

### 🏗️ New Templates
- Implement new MCP server functionality
- Follow our template structure and conventions
- Include comprehensive documentation and examples

### 🐛 Bug Fixes
- Fix issues in existing templates
- Improve error handling and edge cases
- Update documentation as needed

### 📚 Documentation
- Improve READMEs and guides
- Add usage examples
- Fix typos and clarity issues

### 🔧 Infrastructure
- Improve build scripts and CI/CD
- Enhance Docker configurations
- Optimize performance

## 🏗️ Creating a New Template

### 1. Template Structure

```
templates/your-template/
├── README.md              # Template documentation
├── template.json          # Configuration schema
├── Dockerfile            # Container definition
├── docker-compose.yml    # Local testing setup
├── requirements.txt      # Python dependencies (if applicable)
├── package.json          # Node.js dependencies (if applicable)
├── src/                  # Source code
│   ├── server.py        # Main MCP server (Python)
│   ├── server.js        # Main MCP server (JavaScript)
│   └── platform-wrapper.js  # Platform integration layer
└── config/               # Configuration examples
    └── config.yaml.example
```

### 2. Template Configuration Schema

Your `template.json` must include:

```json
{
  "name": "Your Template Name",
  "description": "Brief description of what this template does",
  "version": "1.0.0",
  "author": "Your Name <your.email@domain.com>",
  "docker_image": "ghcr.io/data-everything/mcp-your-template",
  "categories": ["category1", "category2"],
  "config_schema": {
    "type": "object",
    "properties": {
      "your_setting": {
        "type": "string",
        "title": "Setting Display Name",
        "description": "What this setting controls",
        "env_mapping": "MCP_YOUR_SETTING",
        "default": "default_value"
      }
    },
    "required": ["your_setting"]
  },
  "health_check": {
    "path": "/health",
    "interval": "30s",
    "timeout": "10s"
  }
}
```

### 3. Environment Variable Mapping

All configuration options should support environment variables:

- **Naming Convention**: `MCP_` prefix, uppercase, underscores for separators
- **Arrays**: Use comma-separated values (`MCP_ALLOWED_DIRS=/path1,/path2`)
- **Booleans**: Use `true`/`false` strings
- **Objects**: Use `env_separator` in template.json for nested configs

Example:
```json
{
  "database_config": {
    "type": "object",
    "env_mapping": "MCP_DATABASE",
    "env_separator": "__",
    "properties": {
      "host": {"env_mapping": "MCP_DATABASE__HOST"},
      "port": {"env_mapping": "MCP_DATABASE__PORT"}
    }
  }
}
```

### 4. Platform Integration

Include a `platform-wrapper.js` for environment variable parsing:

```javascript
async function loadConfiguration() {
  const config = {};
  
  // Parse environment variables
  for (const [key, value] of Object.entries(process.env)) {
    if (key.startsWith('MCP_')) {
      // Parse based on your template's schema
      parseEnvironmentVariable(config, key, value);
    }
  }
  
  // Merge with config file if present
  if (fs.existsSync('/app/config/config.yaml')) {
    const fileConfig = yaml.load(fs.readFileSync('/app/config/config.yaml', 'utf8'));
    Object.assign(config, fileConfig);
  }
  
  return config;
}
```

## 🧪 Testing Your Template

### Local Testing Script

```bash
# Build your template
./scripts/build-template.sh your-template

# Test with environment variables
docker run --rm \
  --env=MCP_YOUR_SETTING=test_value \
  --env=MCP_LOG_LEVEL=debug \
  -p 8000:8000 \
  ghcr.io/data-everything/mcp-your-template:latest

# Test with config file
docker run --rm \
  --volume=$(pwd)/templates/your-template/config:/app/config \
  -p 8000:8000 \
  ghcr.io/data-everything/mcp-your-template:latest
```

### Integration Testing

Create test scripts in the `tests/` directory:

```python
# tests/test_your_template.py
import pytest
import requests
from test_utils import build_and_run_template

def test_your_template_health():
    with build_and_run_template('your-template') as container:
        response = requests.get(f"http://localhost:{container.port}/health")
        assert response.status_code == 200

def test_your_template_mcp_protocol():
    with build_and_run_template('your-template') as container:
        # Test MCP protocol endpoints
        pass
```

## 📚 Documentation Requirements

### Template README

Each template must include:

```markdown
# Template Name

Brief description of what this template does.

## Features
- Feature 1
- Feature 2
- Feature 3

## Configuration

### Environment Variables
| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `MCP_SETTING` | What it does | `default` | Yes |

### Config File (Optional)
```yaml
setting: value
nested:
  option: value
```

## Usage Examples

### Docker
```bash
docker run -d \
  --env=MCP_SETTING=value \
  -p 8000:8000 \
  ghcr.io/data-everything/mcp-template-name:latest
```

### Docker Compose
```yaml
version: '3.8'
services:
  template:
    image: ghcr.io/data-everything/mcp-template-name:latest
    environment:
      - MCP_SETTING=value
    ports:
      - "8000:8000"
```

## Troubleshooting
Common issues and solutions.
```

## 🔍 Code Review Guidelines

### Checklist for Reviewers

- [ ] Template follows directory structure conventions
- [ ] `template.json` schema is complete and valid
- [ ] Environment variable mapping is consistent
- [ ] Docker image builds successfully
- [ ] Health check endpoint works
- [ ] Documentation is comprehensive
- [ ] Tests are included and pass
- [ ] No hardcoded secrets or credentials

### Code Quality Standards

- Use clear, descriptive variable names
- Include error handling and logging
- Follow language-specific best practices
- Add comments for complex logic
- Validate all inputs
- Use secure coding practices

## 🚀 Pull Request Process

1. **Create Issue**: Describe what you're building/fixing
2. **Fork & Branch**: Create a feature branch from main
3. **Develop**: Follow our guidelines and test thoroughly
4. **Document**: Update READMEs and add examples
5. **Test**: Ensure all tests pass locally
6. **Submit PR**: Include clear description and link to issue
7. **Review**: Address feedback from maintainers
8. **Merge**: We'll merge once approved

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] New template
- [ ] Bug fix
- [ ] Documentation update
- [ ] Infrastructure improvement

## Testing
- [ ] Built template locally
- [ ] Tested with environment variables
- [ ] Tested with config file
- [ ] Added automated tests
- [ ] Updated documentation

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Tests added/updated
- [ ] No breaking changes (or documented)
```

## 🛠️ Development Environment

### Prerequisites

- Docker and Docker Compose
- Git
- Your preferred language runtime (Python, Node.js, etc.)

### Setup

```bash
# Clone the repository
git clone https://github.com/your-username/mcp-server-templates.git
cd mcp-server-templates

# Make scripts executable
chmod +x scripts/*.sh

# Build and test a template
./scripts/build-template.sh file-server
```

## 🎯 Coding Standards

### Python Templates
- Use `black` for formatting
- Follow PEP 8 guidelines
- Include type hints
- Use `pytest` for testing

### JavaScript/Node.js Templates
- Use `prettier` for formatting
- Follow ESLint recommended rules
- Use modern async/await syntax
- Use `jest` for testing

### Docker Best Practices
- Use multi-stage builds
- Minimize image size
- Run as non-root user
- Include health checks
- Pin base image versions

## 🤝 Community Guidelines

- Be respectful and inclusive
- Help newcomers get started
- Provide constructive feedback
- Share knowledge and best practices
- Follow our Code of Conduct

## 📞 Getting Help

- **Issues**: Use GitHub Issues for bugs and feature requests
- **Discussions**: Use GitHub Discussions for questions
- **Documentation**: Check our docs/ directory
- **Examples**: Look at existing templates for reference

## 🏆 Recognition

Contributors will be:
- Listed in our CONTRIBUTORS.md file
- Credited in template documentation
- Invited to join our contributor community
- Featured in release notes for significant contributions

Thank you for contributing to the MCP Server Templates project! 🎉
