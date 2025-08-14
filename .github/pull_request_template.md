## Description

Brief description of the changes in this pull request.

## Type of Change

Please delete options that are not relevant:

- [ ] 🐛 Bug fix (non-breaking change which fixes an issue)
- [ ] ✨ New feature (non-breaking change which adds functionality)
- [ ] 💥 Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] 📚 Documentation update
- [ ] 🏗️ New template
- [ ] 🔧 Template enhancement
- [ ] 🚀 Infrastructure/build changes

## Template(s) Affected

List the templates that are affected by this change:

- [ ] filesystem
- [ ] gitlab
- [ ] github
- [ ] demo
- [ ] other: ___________

## Testing

Describe the tests you ran and provide instructions so reviewers can reproduce:

### Local Testing

- [ ] Built template locally
- [ ] Tested with environment variables
- [ ] Tested with config file
- [ ] Health check passes
- [ ] Template-specific functionality works

### Test Commands

```bash
# Commands used to test the changes
./scripts/build-template.sh template-name

docker run --rm \
  --env=MCP_SETTING=value \
  -p 8000:8000 \
  data-everything/mcp-template-name:latest

curl http://localhost:8000/health
```

## Configuration Changes

If this PR introduces new configuration options, document them here:

### New Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `MCP_NEW_SETTING` | Description of the setting | `default_value` | No |

### Config File Changes

```yaml
# New configuration options
new_section:
  option: value
```

## Breaking Changes

List any breaking changes and migration steps:

- [ ] No breaking changes
- [ ] Breaking changes documented below

### Migration Guide

If there are breaking changes, explain how users should migrate:

1. Step 1: Update environment variables
2. Step 2: Modify config files
3. Step 3: Rebuild containers

## Documentation

- [ ] Updated template README.md
- [ ] Updated configuration documentation
- [ ] Added usage examples
- [ ] Updated template.json schema
- [ ] No documentation changes needed

## Checklist

Please review and check all applicable items:

### Code Quality
- [ ] My code follows the style guidelines of this project
- [ ] I have performed a self-review of my code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] My changes generate no new warnings

### Testing
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes
- [ ] I have tested my changes in a Docker container
- [ ] Health checks pass with my changes

### Template Requirements (if applicable)
- [ ] Template includes proper `template.json` with valid schema
- [ ] Template includes comprehensive README.md
- [ ] Template includes working Dockerfile
- [ ] Template includes docker-compose.yml for local development
- [ ] Environment variable mapping is properly implemented
- [ ] Configuration file support is implemented (if needed)

### Security
- [ ] No hardcoded secrets or credentials
- [ ] Sensitive configuration marked as `"secret": true` in template.json
- [ ] Input validation implemented for user inputs
- [ ] Container runs as non-root user

## Screenshots (if applicable)

Add screenshots to help explain your changes.

## Additional Notes

Any additional information that reviewers should know about this change.

---

## Reviewer Notes

*This section will be filled by reviewers during the review process.*

### Review Checklist
- [ ] Code quality and style
- [ ] Test coverage adequate
- [ ] Documentation complete
- [ ] Template builds successfully
- [ ] Configuration schema valid
- [ ] Security considerations addressed
- [ ] Breaking changes properly documented
