# Documentation Restructure Plan

## Current Issues
1. **Duplicate directories**: `templates/` and `server-templates/`
2. **Scattered template files**: Multiple loose template-related files in root
3. **Inconsistent naming**: Mixed naming conventions across files
4. **Redundant content**: Same information in multiple places
5. **Poor navigation**: No clear information hierarchy

## New Structure

### Root Level
- `index.md` - Main documentation hub
- `faq.md` - Frequently asked questions
- `CHANGELOG.md` - Version history and updates

### Core Directories
```
docs/
├── getting-started/        # Quick start and installation
│   ├── installation.md
│   ├── quickstart.md
│   ├── first-deployment.md
│   └── configuration.md
├── user-guide/            # User documentation
│   ├── templates.md       # Working with templates
│   ├── configuration.md   # Configuration management
│   ├── integration.md     # LLM integrations
│   └── monitoring.md      # Production monitoring
├── cli/                   # CLI reference (existing, good)
│   ├── index.md
│   ├── deploy.md
│   ├── create.md
│   └── ...
├── templates/             # Template documentation (consolidated)
│   ├── index.md          # Template overview
│   ├── demo.md           # Demo template
│   ├── file-server.md    # File server template
│   └── creating.md       # Creating custom templates
├── guides/                # How-to guides
│   ├── deployment.md     # Advanced deployment
│   ├── development.md    # Development workflows
│   ├── troubleshooting.md
│   └── contributing.md
├── reference/             # Technical reference
│   ├── api.md            # API documentation
│   ├── schema.md         # Configuration schemas
│   ├── discovery.md      # Tool/template discovery
│   └── architecture.md   # System architecture
└── examples/              # Code examples and tutorials
    ├── integrations.md   # Integration examples
    └── workflows.md      # Common workflows
```

## Actions Required
1. **Consolidate duplicate content** from templates/ and server-templates/
2. **Move scattered files** into appropriate directories
3. **Remove redundant files** with duplicate content
4. **Update all cross-references** in documentation
5. **Create missing index files** for navigation
6. **Validate all links** are working

## Implementation Steps
1. Create new directory structure
2. Consolidate and move content
3. Update navigation and cross-references
4. Remove old duplicate files
5. Update main index.md with new structure
