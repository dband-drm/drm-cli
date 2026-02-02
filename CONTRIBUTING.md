# Contributing to DRM-CLI

First off, thank you for considering contributing to DRM-CLI! 

It's people like you that make DRM-CLI such a great tool for the DevOps and database administration community.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
  - [Reporting Bugs](#reporting-bugs)
  - [Suggesting Enhancements](#suggesting-enhancements)
  - [Your First Code Contribution](#your-first-code-contribution)
  - [Pull Requests](#pull-requests)
- [Style Guidelines](#style-guidelines)
  - [Git Commit Messages](#git-commit-messages)
  - [Python Style Guide](#python-style-guide)
  - [Documentation Style Guide](#documentation-style-guide)
- [Development Setup](#development-setup)
- [Testing](#testing)
- [Community](#community)

---

## Code of Conduct

This project and everyone participating in it is governed by respect, professionalism, and collaboration. By participating, you are expected to uphold these values. Please be kind and courteous to others.

### Our Standards

-  Be respectful and inclusive
-  Welcome newcomers and help them get started
-  Focus on what is best for the community
-  Show empathy towards other community members
-  No harassment, trolling, or insulting/derogatory comments
-  No political or off-topic discussions

---

## How Can I Contribute?

### Reporting Bugs

Bugs are tracked as [GitHub issues](https://github.com/dband-drm/drm-cli/issues). Before creating a bug report, please check existing issues to avoid duplicates.

#### How to Submit a Good Bug Report

Include as many details as possible:

**Use this template:**

```markdown
**Description**
A clear and concise description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Run command '...'
2. With configuration '...'
3. See error

**Expected Behavior**
What you expected to happen.

**Actual Behavior**
What actually happened.

**Environment:**
- OS: [e.g., Windows 11, Ubuntu 22.04]
- Python Version: [e.g., 3.10.5]
- DRM-CLI Version: [e.g., 1.1.0]
- Database: [e.g., Oracle 19c, PostgreSQL 14]

**Additional Context**
- Configuration files (sanitize sensitive data)
- Error logs
- Screenshots if applicable
```

### Suggesting Enhancements

Enhancement suggestions are also tracked as [GitHub issues](https://github.com/dband-drm/drm-cli/issues).

#### How to Submit a Good Enhancement Suggestion

**Use this template:**

```markdown
**Is your feature request related to a problem?**
A clear description of what the problem is. Ex. I'm always frustrated when [...]

**Describe the solution you'd like**
A clear description of what you want to happen.

**Describe alternatives you've considered**
Alternative solutions or features you've considered.

**Additional context**
Any other context, screenshots, or examples.

**Use Cases**
Who would benefit and how?
```

### Your First Code Contribution

Unsure where to begin? Look for issues labeled:

- `good first issue` - Good for newcomers
- `help wanted` - Extra attention needed
- `documentation` - Documentation improvements

#### Setting Up Your Development Environment

1. **Fork the repository**

2. **Clone your fork:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/drm-cli.git
   cd drm-cli
   ```

3. **Add upstream remote:**
   ```bash
   git remote add upstream https://github.com/dband-drm/drm-cli.git
   ```

4. **Create a virtual environment:**
   ```bash
   python -m venv venv
   
   # On Windows:
   venv\Scripts\activate
   
   # On Linux/Mac:
   source venv/bin/activate
   ```

5. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

6. **Create a feature branch:**
   ```bash
   git checkout -b feature/amazing-feature
   ```

### Pull Requests

1. **Follow the style guidelines** (see below)
2. **Update documentation** if you're changing functionality
3. **Add tests** for new features
4. **Ensure all tests pass**
5. **Keep PRs focused** - one feature/fix per PR
6. **Write a clear PR description**

#### Pull Request Template

```markdown
**Description**
Brief description of what this PR does.

**Related Issue**
Closes #123 (if applicable)

**Type of Change**
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

**How Has This Been Tested?**
Describe the tests you ran to verify your changes.

**Checklist:**
- [ ] My code follows the style guidelines of this project
- [ ] I have performed a self-review of my own code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes
```

---

## Style Guidelines

### Git Commit Messages

- Use the present tense ("Add feature" not "Added feature")
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit the first line to 72 characters or less
- Reference issues and pull requests liberally after the first line

**Examples:**
```
Add PostgreSQL connection pooling

- Implement connection pool with configurable size
- Add retry logic for failed connections
- Update documentation

Fixes #123
```

### Python Style Guide

We follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) with some adjustments:

- **Line length**: 100 characters (not 80)
- **Indentation**: 4 spaces (no tabs)
- **String quotes**: Double quotes preferred
- **Imports**: Group stdlib, third-party, local; alphabetize within groups

#### Code Formatting

We use **Black** for code formatting:

```bash
black drm/
```

#### Linting

We use **flake8** for linting:

```bash
flake8 drm/ --max-line-length=100
```

#### Type Hints

Use type hints for function signatures:

```python
def deploy(config: Config, target: str) -> DeploymentResult:
    """Deploy to specified target."""
    pass
```

#### Docstrings

Use Google-style docstrings:

```python
def connect_database(host: str, port: int, database: str) -> Connection:
    """Connect to a database.
    
    Args:
        host: Database hostname or IP address
        port: Database port number
        database: Database name
        
    Returns:
        A database connection object
        
    Raises:
        ConnectionError: If connection fails
        
    Example:
        >>> conn = connect_database("localhost", 5432, "mydb")
    """
    pass
```

### Documentation Style Guide

- Use Markdown for all documentation
- Include code examples where applicable
- Keep language clear and concise
- Use proper heading hierarchy (H1 → H2 → H3)
- Add links to related documentation

---

## Development Setup

### Project Structure

```
drm-cli/
├── drm/                    # Main package
│   ├── __init__.py
│   ├── cli.py             # CLI interface
│   ├── deployment.py      # Deployment logic
│   ├── config.py          # Configuration handling
│   └── platforms/         # Platform-specific implementations
├── tests/                 # Test suite
├── docs/                  # Documentation
├── init_drm_db/          # Database initialization scripts
├── modules/              # Reusable modules
├── README.md
├── CONTRIBUTING.md
├── LICENSE
├── requirements.txt
├── requirements-dev.txt
└── setup.py
```

### Running DRM-CLI Locally

```bash
# Install  
drm_install.py

# Run CLI
drm_deploy.py --help
```

### Environment Variables

Create a `.env` file for local development (never commit this):

```bash
# Database connections
DRM_ORACLE_HOST=localhost
DRM_ORACLE_PORT=1521
DRM_POSTGRES_HOST=localhost
DRM_POSTGRES_PORT=5432

# Development settings
DRM_DEBUG=true
DRM_LOG_LEVEL=DEBUG
```

## Community

### Getting Help

-  Check the [README](README.md) and [Wiki](https://github.com/dband-drm/drm-cli/wiki)
-  Ask questions in [GitHub Discussions](https://github.com/dband-drm/drm-cli/discussions)
-  Report bugs via [GitHub Issues](https://github.com/dband-drm/drm-cli/issues)
-  Visit our website: [www.d-band.com](https://www.d-band.com/)

### Communication Channels

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: Questions, ideas, and general discussion
- **LinkedIn**: Follow [D-Band](https://www.linkedin.com/company/106630725) for updates


## Recognition

Contributors will be:
- Listed in our README
- Mentioned in release notes
- Featured on our website (for significant contributions)
- Invited to become maintainers (for sustained contributions)

---

## Questions?

Don't hesitate to ask questions! We're here to help:

- Open a [Discussion](https://github.com/dband-drm/drm-cli/discussions)
- Comment on an existing Issue
- Reach out via our [website](https://www.d-band.com/)

---

## Thank You! 🙏

Your contributions make DRM-CLI better for everyone. Whether you're fixing typos, reporting bugs, or implementing major features, every contribution matters.

**Happy coding!** 🚀

---

<div align="center">

Made with ❤️ by the DRM-CLI community

[Website](https://www.d-band.com/) • [GitHub](https://github.com/dband-drm/drm-cli) • [LinkedIn](https://www.linkedin.com/company/106630725)

</div>
