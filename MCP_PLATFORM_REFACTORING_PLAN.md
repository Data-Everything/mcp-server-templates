# MCP Platform Refactoring Plan: mcp-template → mcp-platform

## Executive Summary

This document outlines a comprehensive refactoring plan to migrate the existing `mcp-template` project to `mcp-platform`. This is not an in-place replacement but rather the creation of a new project that maintains the complete history while updating all naming conventions, URLs, package names, and tooling.

**Current State:**
- Project: `mcp-server-templates`
- Repository: `Data-Everything/mcp-server-templates`
- Python Package: `mcp-templates` (PyPI)
- CLI Commands: `mcp-template`, `mcpt`
- Python Module: `mcp_template`

**Target State:**
- Project: `mcp-platform`
- Repository: `Data-Everything/mcp-platform`
- Python Package: `mcp-platform` (PyPI)
- CLI Commands: `mcp-platform`, `mcpp`
- Python Module: `mcp_platform`

---

## 1. Repository and Infrastructure Changes

### 1.1 GitHub Repository Migration

**Actions Required:**
1. **Create New Repository:**
   - Create `Data-Everything/mcp-platform`
   - Mirror all branches, tags, and history from `mcp-server-templates`
   - Set up branch protection rules matching current repository

2. **Repository Settings:**
   - Update repository description: "MCP Platform: Production-ready Model Context Protocol server deployment and management platform"
   - Update topics: `mcp`, `model-context-protocol`, `ai-platform`, `server-deployment`, `docker`, `kubernetes`
   - Configure repository settings (Issues, Discussions, Wiki, Security)

3. **GitHub Pages Configuration:**
   - Update GitHub Pages source to new repository
   - Configure custom domain (if applicable)
   - Update documentation deployment workflow

### 1.2 Branch and Release Strategy

**Current Branches to Migrate:**
- `main` (primary development)
- Any feature branches
- Release tags following pattern: `release-pypi-*`

**New Release Pattern:**
- Continue using: `release-pypi-X.Y.Z` format
- Update version scheme in `pyproject.toml`

---

## 2. Python Package and Module Changes

### 2.1 PyPI Package Migration

**Current Package:** `mcp-templates`
**New Package:** `mcp-platform`

**Actions Required:**
1. **PyPI Package Registration:**
   - Reserve `mcp-platform` package name on PyPI
   - Reserve `mcp_platform` alternative name
   - Test package upload to TestPyPI first

2. **Package Configuration Updates:**
   ```toml
   # pyproject.toml changes
   [project]
   name = "mcp-platform"
   description = "MCP Platform: Production-ready Model Context Protocol server deployment and management"

   [project.urls]
   Bug-Reports = "https://github.com/Data-Everything/mcp-platform/issues"
   Source = "https://github.com/Data-Everything/mcp-platform"
   Documentation = "https://data-everything.github.io/mcp-platform"
   Issue-Tracker = "https://github.com/Data-Everything/mcp-platform/issues"

   [project.scripts]
   mcp-platform = "mcp_platform:main"
   mcpp = "mcp_platform:main"
   ```

3. **Package Deprecation Strategy:**
   - Publish final version of `mcp-templates` with deprecation notice
   - Include migration instructions in package description
   - Redirect users to new `mcp-platform` package

### 2.2 Python Module Refactoring

**Directory Structure Changes:**
```
# Current
mcp_template/
├── __init__.py
├── __main__.py
├── cli/
├── core/
├── backends/
├── client/
├── template/
├── tools/
└── utils/

# New
mcp_platform/
├── __init__.py
├── __main__.py
├── cli/
├── core/
├── backends/
├── client/
├── template/
├── tools/
└── utils/
```

**Import Statement Updates Required:**
- Update all `from mcp_template` → `from mcp_platform`
- Update all internal imports across 200+ files
- Update test imports in `tests/` directory
- Update example code in documentation

### 2.3 CLI Command Updates

**Current CLI Commands:**
- Primary: `mcp-template`
- Alias: `mcpt`

**New CLI Commands:**
- Primary: `mcp-platform`
- Alias: `mcpp`

**Files Requiring Updates:**
- `pyproject.toml` - script entry points
- All documentation mentioning CLI commands
- README examples
- Docker ENTRYPOINT
- GitHub workflow files
- Makefile targets

---

## 3. Documentation Updates

### 3.1 Core Documentation Files

**Files Requiring Complete Updates:**

1. **README.md**
   - Update all command examples: `mcpt` → `mcpp`
   - Update PyPI installation: `pip install mcp-platform`
   - Update repository URLs
   - Add migration notice section
   - Update badges and links

2. **docs/ Directory** (90+ files)
   - Update site configuration in `mkdocs.yml`
   - Update all CLI examples throughout documentation
   - Update installation instructions
   - Update API references
   - Update troubleshooting guides

3. **Individual Documentation Pages:**
   ```markdown
   # Key files requiring updates:
   - docs/index.md
   - docs/getting-started/installation.md
   - docs/getting-started/quickstart.md
   - docs/cli/*.md (15+ files)
   - docs/guides/*.md (10+ files)
   - docs/templates/*.md (20+ files)
   ```

### 3.2 MkDocs Configuration

**mkdocs.yml Updates Required:**
```yaml
site_name: MCP Platform
site_description: Deploy and manage MCP servers with production-ready platform
site_url: https://data-everything.github.io/mcp-platform
repo_name: Data-Everything/mcp-platform
repo_url: https://github.com/Data-Everything/mcp-platform
```

### 3.3 Migration Documentation

**Create New Documentation Sections:**
1. **Migration Guide** (`docs/migration/from-mcp-templates.md`)
   - Step-by-step migration instructions
   - Command equivalency table
   - Configuration migration guide
   - Troubleshooting migration issues

2. **Legacy Support** (`docs/legacy/mcp-templates.md`)
   - Information about old package
   - Deprecation timeline
   - Support policy

---

## 4. Configuration and Template Updates

### 4.1 Template Configuration Files

**Template Files Requiring Updates:**
- `mcp_platform/template/templates/*/template.json` (5+ templates)
- Docker image references in templates
- Documentation within templates
- Example configurations

**Example Template Updates:**
```json
{
  "docker_image": "dataeverything/mcp-demo",  # Keep existing
  "description": "Demo server for MCP Platform",  # Update references
  // Update any mcp-template references to mcp-platform
}
```

### 4.2 Docker and Container Updates

**Dockerfile Changes:**
```dockerfile
# Update labels
LABEL tool="mcp-platform"
LABEL tool-shorthand="mcpp"
LABEL description="MCP Platform for rapid deployment and management of AI servers"

# Update entrypoint
ENTRYPOINT ["mcpp"]
```

**Docker Image Strategy:**
- Keep existing Docker images (`dataeverything/mcp-*`) unchanged
- Update base deployment image: `dataeverything/mcp-platform`
- Update Docker Compose examples
- Update Kubernetes manifests

### 4.3 Kubernetes and Helm Charts

**Helm Chart Updates:**
```yaml
# charts/mcp-server/Chart.yaml
name: mcp-platform
description: A Helm chart for deploying MCP Platform servers
home: https://github.com/Data-Everything/mcp-platform
sources:
  - https://github.com/Data-Everything/mcp-platform
```

**Kubernetes Manifest Updates:**
- Update all example YAML files in `examples/kubernetes/`
- Update image references where applicable
- Update labels and annotations

---

## 5. CI/CD and Automation Updates

### 5.1 GitHub Workflows

**Workflow Files to Update:**
- `.github/workflows/unified-ci.yml`
- `.github/workflows/docker-hub.yml`
- `.github/workflows/docs.yml`

**Key Changes Required:**
```yaml
# Update environment variables
env:
  PACKAGE_NAME: "mcp-platform"
  MODULE_NAME: "mcp_platform"

# Update test commands
python -c "
from mcp_platform import TemplateDiscovery, DockerDeploymentService, DeploymentManager
print('✅ All imports successful')
"

# Update PyPI publishing
- name: Publish to PyPI
  run: |
    python -m twine upload dist/* --repository pypi
    # Will now publish mcp-platform instead of mcp-templates
```

### 5.2 Build and Release Automation

**Scripts Requiring Updates:**
- `scripts/check_pypi_version.py` - Update package name checks
- `scripts/mcp_endpoint_manager.py` - Update documentation links
- `Makefile` - Update all target references
- `conftest.py` - Update test imports

**Version Management:**
- Continue using `setuptools_scm` with new tag pattern
- Update version scheme to reflect new package
- Maintain semantic versioning

---

## 6. Testing Strategy Updates

### 6.1 Test Suite Migration

**Test Directory Updates:**
```
tests/
├── test_unit/
│   ├── test_cli/           # Update CLI command tests
│   ├── test_client/        # Update import statements
│   ├── test_core/          # Update module imports
│   └── test_template/      # Update template tests
└── test_integration/
    ├── test_backends/      # Update backend tests
    ├── test_cli/           # Update end-to-end CLI tests
    └── test_deployment/    # Update deployment tests
```

**Test Updates Required:**
- Update all `import mcp_template` → `import mcp_platform`
- Update CLI command tests to use `mcpp` instead of `mcpt`
- Update test fixtures and mock configurations
- Update integration test expectations

### 6.2 Test Configuration

**Files Requiring Updates:**
- `pytest.ini` - Update test paths if needed
- `conftest.py` - Update imports and fixtures
- Test requirements in `requirements-dev.txt`

**Mock and Fixture Updates:**
- Update mock CLI command calls
- Update test data files with new names
- Update environment variable names in tests

---

## 7. Community and Ecosystem Updates

### 7.1 External References

**Third-Party Integration Updates:**
- MCP Registry listings (if any)
- Community forums and discussions
- Blog posts and tutorials
- Integration examples in other projects

### 7.2 Community Communication

**Communication Strategy:**
1. **Announcement Phase:**
   - GitHub Discussions announcement
   - Discord community notification
   - Documentation banner on old site
   - Social media announcements

2. **Transition Phase:**
   - Gradual migration of community resources
   - Support for both old and new package names
   - Clear migration timeline

3. **Completion Phase:**
   - Archive old repository with clear redirect
   - Deprecate old PyPI package
   - Update all external references

---

## 8. Legacy Support and Migration Path

### 8.1 Backward Compatibility Strategy

**Package Compatibility:**
1. **Transition Period (3-6 months):**
   - Both `mcp-templates` and `mcp-platform` available
   - Old package shows deprecation warnings
   - Cross-compatibility where possible

2. **Deprecation Period (6-12 months):**
   - `mcp-templates` package marked as deprecated
   - Security updates only for old package
   - Migration tools provided

3. **End-of-Life:**
   - `mcp-templates` package no longer maintained
   - Clear documentation on migration path

### 8.2 Migration Tools

**Automated Migration Utilities:**
1. **Configuration Migrator:**
   - Script to update existing config files
   - Command alias mapping tool
   - Environment variable migration guide

2. **Installation Migration:**
   ```bash
   # Old installation
   pip uninstall mcp-templates
   pip install mcp-platform

   # Update shell aliases
   alias mcpt="mcpp"  # Temporary compatibility
   ```

---

## 9. Risk Assessment and Mitigation

### 9.1 Technical Risks

**High-Risk Areas:**
1. **Import Statement Updates:**
   - Risk: Breaking changes across large codebase
   - Mitigation: Comprehensive testing, staged rollout

2. **CLI Command Changes:**
   - Risk: User workflow disruption
   - Mitigation: Alias support, clear migration docs

3. **Docker Image Dependencies:**
   - Risk: Broken deployment configurations
   - Mitigation: Keep existing images, provide upgrade path

### 9.2 Community Impact

**User Impact Assessment:**
- **Current Users:** ~1000+ (estimated from PyPI downloads)
- **Documentation Users:** GitHub Pages traffic
- **Integration Users:** Projects depending on the package

**Mitigation Strategies:**
- Clear communication timeline
- Extensive migration documentation
- Community support during transition
- Backward compatibility period

---

## 10. Implementation Timeline

### Phase 1: Preparation (Weeks 1-2)
- [ ] Reserve new PyPI package name
- [ ] Create new GitHub repository
- [ ] Set up basic CI/CD for new repository
- [ ] Prepare communication materials

### Phase 2: Core Migration (Weeks 3-4)
- [ ] Update Python module structure
- [ ] Update all import statements
- [ ] Update CLI commands and entry points
- [ ] Update core documentation

### Phase 3: Infrastructure Update (Weeks 5-6)
- [ ] Update Docker configurations
- [ ] Update Kubernetes/Helm charts
- [ ] Update CI/CD workflows
- [ ] Update test suites

### Phase 4: Documentation and Examples (Weeks 7-8)
- [ ] Complete documentation migration
- [ ] Update all examples and tutorials
- [ ] Create migration guides
- [ ] Update external references

### Phase 5: Release and Communication (Weeks 9-10)
- [ ] Publish new package to PyPI
- [ ] Deploy new documentation site
- [ ] Announce migration to community
- [ ] Begin deprecation of old package

### Phase 6: Support and Transition (Weeks 11-24)
- [ ] Support both packages during transition
- [ ] Monitor and assist user migration
- [ ] Address migration issues
- [ ] Plan end-of-life for old package

---

## 11. Success Metrics

### 11.1 Technical Metrics
- [ ] All imports successfully updated (0 import errors)
- [ ] 100% test suite passing
- [ ] CI/CD pipelines green
- [ ] Documentation site deployed successfully
- [ ] PyPI package published and installable

### 11.2 Community Metrics
- [ ] User migration rate (target: 80% within 6 months)
- [ ] Issue volume related to migration (target: <10% of total issues)
- [ ] Community feedback sentiment
- [ ] Documentation site traffic transfer

### 11.3 Operational Metrics
- [ ] Package download trends on PyPI
- [ ] Docker image pull statistics
- [ ] GitHub repository engagement
- [ ] Support request volume

---

## 12. Resource Requirements

### 12.1 Human Resources
- **Development Team:** 2-3 developers for 4-6 weeks
- **DevOps/Infrastructure:** 1 engineer for CI/CD and deployment
- **Documentation:** 1 technical writer for 2-3 weeks
- **Community Management:** 1 community manager for communication

### 12.2 Infrastructure Resources
- **GitHub Actions:** Increased usage for parallel CI/CD
- **Storage:** Additional space for duplicated repositories during transition
- **Monitoring:** Enhanced monitoring during migration period

---

## 13. Rollback Plan

### 13.1 Rollback Triggers
- Critical bugs in new package affecting >50% of users
- Significant decrease in adoption (<20% migration after 3 months)
- Major security vulnerabilities discovered
- Community backlash or resistance

### 13.2 Rollback Procedure
1. **Immediate Actions:**
   - Pause new package promotion
   - Continue support for old package
   - Communicate rollback decision

2. **Medium-term Actions:**
   - Address issues causing rollback
   - Plan revised migration strategy
   - Extended support for old package

---

## 14. Post-Migration Maintenance

### 14.1 Ongoing Support
- **Old Package Maintenance:** Security updates only for 12 months
- **Migration Support:** Dedicated support for migration issues
- **Documentation Maintenance:** Keep migration docs updated

### 14.2 Future Considerations
- **Package Namespace:** Reserve related package names
- **Trademark/Legal:** Consider trademark registration for "MCP Platform"
- **Community Building:** Focus on building community around new brand

---

## 15. Detailed File-by-File Change List

### 15.1 Python Source Files (mcp_template/ → mcp_platform/)

**Critical Python Files:**
```
mcp_template/__init__.py → mcp_platform/__init__.py
mcp_template/__main__.py → mcp_platform/__main__.py
mcp_template/cli/cli.py → mcp_platform/cli/cli.py
mcp_template/client/client.py → mcp_platform/client/client.py
mcp_template/core/*.py → mcp_platform/core/*.py (15+ files)
mcp_template/backends/*.py → mcp_platform/backends/*.py (10+ files)
mcp_template/template/utils/*.py → mcp_platform/template/utils/*.py (5+ files)
mcp_template/tools/*.py → mcp_platform/tools/*.py (8+ files)
```

**Import Statement Pattern:**
```python
# Every Python file needs these changes:
# OLD: from mcp_template.core import DeploymentManager
# NEW: from mcp_platform.core import DeploymentManager

# OLD: import mcp_template.backends.docker
# NEW: import mcp_platform.backends.docker
```

### 15.2 Configuration Files

**Root Configuration Files:**
- `pyproject.toml` - Package name, entry points, URLs
- `setup.py` (if exists) - Package configuration
- `MANIFEST.in` - Package inclusion rules
- `requirements.txt` - No changes needed
- `requirements-dev.txt` - No changes needed

**Docker and Container Files:**
- `Dockerfile` - Labels, entrypoint, description
- `docker-compose.yml` (examples) - Service names, commands
- `.dockerignore` - No changes needed

**CI/CD Configuration:**
- `.github/workflows/*.yml` - Environment variables, commands
- `.github/pull_request_template.md` - Repository references
- `Makefile` - Target names, commands
- `pytest.ini` - Module paths (if any)

### 15.3 Documentation Files

**Markdown Files (90+ files):**
```
README.md - Complete rewrite of examples
docs/index.md - Site title, descriptions
docs/getting-started/*.md - Installation commands
docs/cli/*.md - CLI command examples
docs/guides/*.md - Usage examples
docs/templates/*.md - Template references
docs/faq.md - Command examples
```

**Configuration Files:**
```
mkdocs.yml - Site metadata, URLs
docs/stylesheets/extra.css - No changes needed
```

### 15.4 Test Files

**Test Python Files (200+ test files):**
```
tests/test_unit/**/*.py - All import statements
tests/test_integration/**/*.py - All import statements
tests/conftest.py - Fixture imports
tests/mcp_test_utils.py - Helper imports
```

**Test CLI Commands:**
```python
# Every test using CLI needs updates:
# OLD: runner.invoke(app, ["mcpt", "deploy", "demo"])
# NEW: runner.invoke(app, ["mcpp", "deploy", "demo"])
```

### 15.5 Example and Template Files

**Example Configuration:**
```
examples/config/*.json - No changes needed (unless referencing commands)
examples/docker-compose/*.yml - Service names, commands
examples/kubernetes/*.yaml - Labels, image references
```

**Template Files:**
```
mcp_platform/template/templates/*/template.json - Description fields
mcp_platform/template/templates/*/docs/*.md - Documentation references
mcp_platform/template/templates/*/server.py - No changes needed
```

---

## 16. Quality Assurance Plan

### 16.1 Testing Strategy

**Automated Testing:**
- [ ] Unit test suite: 100% pass rate
- [ ] Integration test suite: 100% pass rate
- [ ] CLI functionality tests: All commands working
- [ ] Docker container tests: All images building and running
- [ ] Documentation build tests: All docs generating correctly

**Manual Testing:**
- [ ] End-to-end user workflows
- [ ] Installation from PyPI
- [ ] CLI command functionality
- [ ] Template deployment testing
- [ ] Documentation navigation and accuracy

### 16.2 Review Process

**Code Review Requirements:**
- [ ] All Python file changes reviewed by 2+ developers
- [ ] Documentation changes reviewed by technical writer
- [ ] CI/CD changes reviewed by DevOps engineer
- [ ] Package configuration reviewed by maintainer

**Testing Review:**
- [ ] Test coverage maintained or improved
- [ ] Performance regression testing
- [ ] Security review of package changes
- [ ] Accessibility review of documentation

---

## 17. Communication and Change Management

### 17.1 Stakeholder Communication

**Internal Team:**
- Development team: Technical implementation details
- DevOps team: Infrastructure and deployment changes
- Product team: Timeline and user impact
- Support team: Migration support procedures

**External Community:**
- Current users: Migration timeline and instructions
- Contributors: Development workflow changes
- Documentation users: New site and content location
- Integration partners: API and package changes

### 17.2 Communication Channels

**Announcement Strategy:**
1. **GitHub Discussions:** Detailed technical announcement
2. **Discord Community:** Interactive Q&A and support
3. **Documentation Banner:** Visible notice on current docs
4. **PyPI Package Description:** Deprecation notice and migration link
5. **Social Media:** Broad community announcement

**Support Channels:**
- GitHub Issues: Technical problems and bugs
- Discord: Real-time community support
- Documentation: Self-service migration guides
- Email: Direct support for complex migrations

---

## 18. Appendices

### Appendix A: Complete File Inventory

**Python Module Files (120+ files):**
```
mcp_template/
├── __init__.py (imports, exports)
├── __main__.py (entry point)
├── cli/
│   ├── __init__.py
│   ├── cli.py (main CLI application)
│   └── interactive_cli.py (interactive commands)
├── core/
│   ├── __init__.py
│   ├── deployment_manager.py (deployment logic)
│   ├── config_processor.py (configuration handling)
│   ├── template_manager.py (template operations)
│   ├── tool_manager.py (tool discovery)
│   └── response_formatter.py (output formatting)
├── backends/
│   ├── __init__.py
│   ├── base.py (backend abstraction)
│   ├── docker.py (Docker backend)
│   ├── kubernetes.py (Kubernetes backend)
│   └── mock.py (testing backend)
├── client/
│   ├── __init__.py
│   └── client.py (MCP client implementation)
├── template/
│   ├── __init__.py
│   ├── templates/
│   │   ├── demo/ (demo template)
│   │   ├── github/ (GitHub integration)
│   │   ├── gitlab/ (GitLab integration)
│   │   └── filesystem/ (file operations)
│   └── utils/
│       ├── __init__.py
│       ├── discovery.py (template discovery)
│       └── creation.py (template creation)
├── tools/
│   ├── __init__.py
│   ├── base_probe.py (base tool discovery)
│   ├── docker_probe.py (Docker tool discovery)
│   └── kubernetes_probe.py (K8s tool discovery)
└── utils/
    ├── __init__.py
    └── common.py (shared utilities)
```

### Appendix B: Regular Expression Patterns for Updates

**For automated search and replace:**
```bash
# Python imports
find . -name "*.py" -exec sed -i 's/from mcp_template/from mcp_platform/g' {} \;
find . -name "*.py" -exec sed -i 's/import mcp_template/import mcp_platform/g' {} \;

# CLI commands in documentation
find . -name "*.md" -exec sed -i 's/mcpt /mcpp /g' {} \;
find . -name "*.md" -exec sed -i 's/mcp-template/mcp-platform/g' {} \;

# Repository URLs
find . -name "*.md" -exec sed -i 's/Data-Everything\/mcp-server-templates/Data-Everything\/mcp-platform/g' {} \;
find . -name "*.yml" -exec sed -i 's/Data-Everything\/mcp-server-templates/Data-Everything\/mcp-platform/g' {} \;

# PyPI package references
find . -name "*.md" -exec sed -i 's/mcp-templates/mcp-platform/g' {} \;
```

### Appendix C: Migration Timeline Gantt Chart

```
Week 1-2: Preparation Phase
├── Day 1-3: Repository setup
├── Day 4-7: PyPI package reservation
├── Day 8-10: Communication planning
└── Day 11-14: Development environment setup

Week 3-4: Core Migration Phase
├── Day 15-17: Python module renaming
├── Day 18-21: Import statement updates
├── Day 22-24: CLI command updates
└── Day 25-28: Core functionality testing

Week 5-6: Infrastructure Phase
├── Day 29-31: Docker configuration updates
├── Day 32-35: CI/CD pipeline updates
├── Day 36-38: Kubernetes/Helm updates
└── Day 39-42: Infrastructure testing

Week 7-8: Documentation Phase
├── Day 43-45: Core documentation migration
├── Day 46-49: Example and tutorial updates
├── Day 50-52: Migration guide creation
└── Day 53-56: Documentation review and testing

Week 9-10: Release Phase
├── Day 57-59: Final testing and validation
├── Day 60-63: PyPI package publishing
├── Day 64-66: Documentation site deployment
└── Day 67-70: Community announcement

Week 11-24: Support Phase
├── Ongoing: User migration support
├── Ongoing: Issue resolution
├── Month 3: Migration progress review
└── Month 6: Deprecation planning
```

---

## Conclusion

This comprehensive refactoring plan provides a roadmap for successfully migrating from `mcp-template` to `mcp-platform` while maintaining all project history, minimizing user disruption, and ensuring a smooth transition for the entire ecosystem.

The plan addresses every aspect of the migration including code changes, infrastructure updates, community communication, testing strategies, and long-term maintenance considerations. With proper execution, this migration will position the project for continued growth and adoption under its new identity as the MCP Platform.

**Next Steps:**
1. Review and approve this migration plan
2. Assemble migration team and allocate resources
3. Begin Phase 1 preparation activities
4. Establish communication channels and timelines
5. Execute migration according to planned timeline

**Success Dependencies:**
- Dedicated team commitment for 10-week timeline
- Thorough testing at each phase
- Clear community communication
- Robust rollback planning
- Post-migration support commitment

This migration represents a significant investment in the project's future and should establish MCP Platform as the definitive solution for Model Context Protocol server deployment and management.
