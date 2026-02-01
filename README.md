# DRM-CLI: Data Release Management

<div align="center">

![DRM Logo](https://raw.githubusercontent.com/dband-drm/drm-cli/main/Images/DRM_Logo.png)

**A unified CLI tool for managing and controlling data releases across multiple platforms and source controls**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Latest Release](https://img.shields.io/github/v/release/dband-drm/drm-cli)](https://github.com/dband-drm/drm-cli/releases)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

[Website](https://www.d-band.com/) • [Documentation](https://github.com/dband-drm/drm-cli/wiki) • [Issues](https://github.com/dband-drm/drm-cli/issues) • [Releases](https://github.com/dband-drm/drm-cli/releases)

</div>

---

## 🎯 Introduction

DRM-CLI is a revolutionary application for managing and controlling data releases across multiple platforms and source controls. Born from 25+ years of database administration experience, DRM-CLI solves the complexity of modern data deployments by providing a single, unified interface for all your deployment needs.

### Why DRM-CLI?

Traditional data deployment requires juggling multiple tools:
- 🔧 Source control tools
- 🔧 Platform-specific deployment scripts
- 🔧 Custom utilities for each database system
- 🔧 Monitoring and retry mechanisms

**DRM-CLI replaces all of that with ONE powerful CLI tool.**

### Key Benefits

- ⚡ **50% reduction** in deployment time and cost
- 🔄 **Unified interface** for all platforms and source controls
- 🛡️ **Built-in intelligent retry mechanism** for resilient deployments
- ⚙️ **Parallel execution support** for faster operations
- 🪟 **Cross-platform** support (Windows & Linux)
- 🗄️ **Multiple database support** (Oracle, PostgreSQL, and more)

---

## 🚀 Getting Started

### Prerequisites

Before installing DRM-CLI, ensure you have the following:

- **Python 3.8 or higher**
- **pip** (Python package installer)
- **Git** (for version control integration)
- **Database drivers** (depending on your target platforms):
  - Oracle: `cx_Oracle` or `oracledb`
  - PostgreSQL: `psycopg2`

### Installation

#### Option 1: Installation Script (Recommended)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/dband-drm/drm-cli.git
   cd drm-cli
   ```

2. **Run the installation script:**
   
   **On Windows:**
   ```powershell
   python install.py
   ```
   
   **On Linux:**
   ```bash
   python3 install.py
   ```

3. **Follow the interactive prompts** to configure your installation.

#### Option 2: Manual Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/dband-drm/drm-cli.git
   cd drm-cli
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure the application:**
   - Edit `install.config` with your environment settings
   - Initialize the DRM database using scripts in `init_drm_db/`

4. **Add to PATH** (optional but recommended):
   - Add the `drm-cli` directory to your system PATH

### Quick Start

After installation, verify DRM-CLI is working:

```bash
drm --version
```

Initialize a new DRM project:

```bash
drm init
```

Deploy your first release:

```bash
drm deploy --config myconfig.yml
```

---

## 📦 Software Dependencies

### Core Dependencies

- **Python 3.8+** - Core runtime
- **GitPython** - Git integration
- **PyYAML** - Configuration file parsing
- **Click** or **argparse** - CLI framework

### Database Drivers (Install as needed)

#### Oracle
```bash
pip install oracledb
# or
pip install cx_Oracle
```

#### PostgreSQL
```bash
pip install psycopg2-binary
```

#### SQL Server
```bash
pip install pyodbc
```

### Optional Dependencies

- **pytest** - For running tests
- **black** - Code formatting
- **flake8** - Linting

Install all development dependencies:
```bash
pip install -r requirements-dev.txt
```

---

## 🎯 Features & Usage

### Core Features

#### 1. Multi-Platform Support

Deploy to multiple database platforms with a single command:

```bash
drm deploy --platform oracle --target production
drm deploy --platform postgresql --target staging
```

#### 2. Source Control Integration

Seamlessly integrate with Git, SVN, and other version control systems:

```bash
drm deploy --from-git --branch main
drm deploy --from-commit abc123
```

#### 3. Intelligent Retry Mechanism

Automatic retry with exponential backoff for transient failures:

```yaml
retry:
  max_attempts: 3
  backoff: exponential
  timeout: 300
```

#### 4. Parallel Execution

Deploy to multiple environments simultaneously:

```bash
drm deploy --parallel --targets prod1,prod2,prod3
```

#### 5. Rollback Support

Quickly rollback failed deployments:

```bash
drm rollback --deployment-id abc123
```

### Configuration

DRM-CLI uses YAML configuration files for flexible deployment management:

```yaml
# config.yml
project_name: "MyProject"
version: "1.1.0"

platforms:
  - name: production_oracle
    type: oracle
    host: oracle.example.com
    port: 1521
    service: PROD
    
  - name: production_postgres
    type: postgresql
    host: postgres.example.com
    port: 5432
    database: prod_db

deployment:
  source_control: git
  repository: https://github.com/myorg/myrepo.git
  branch: main
  
  retry:
    enabled: true
    max_attempts: 3
    
  parallel: false
```

---

## 📖 Latest Releases

### v1.1.0 (Latest)
- ✨ Added PostgreSQL support
- ✨ Enhanced Oracle integration
- 🐛 Fixed parallel execution bugs
- 📚 Improved documentation

### v1.0.0
- 🎉 Initial release
- ✅ Oracle database support
- ✅ Git integration
- ✅ Basic deployment workflows

[View all releases →](https://github.com/dband-drm/drm-cli/releases)

---

## 🔧 Build and Test

### Running Tests

DRM-CLI includes a comprehensive test suite:

```bash
# Run all tests
pytest

# Run specific test module
pytest tests/test_deployment.py

# Run with coverage
pytest --cov=drm --cov-report=html
```

### Building from Source

```bash
# Clone and navigate to directory
git clone https://github.com/dband-drm/drm-cli.git
cd drm-cli

# Install in development mode
pip install -e .

# Run tests
pytest

# Build distribution packages
python setup.py sdist bdist_wheel
```

### Code Quality

Ensure code quality before contributing:

```bash
# Format code
black drm/

# Run linter
flake8 drm/

# Type checking (if using mypy)
mypy drm/
```

---

## 🤝 Contributing

We welcome contributions from the community! Whether it's bug fixes, new features, documentation improvements, or examples, your help is appreciated.

### How to Contribute

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Make your changes**
4. **Run tests**
   ```bash
   pytest
   ```
5. **Commit your changes**
   ```bash
   git commit -m "Add amazing feature"
   ```
6. **Push to your branch**
   ```bash
   git push origin feature/amazing-feature
   ```
7. **Open a Pull Request**

### Contribution Guidelines

- Follow PEP 8 style guidelines
- Add tests for new features
- Update documentation as needed
- Keep commits atomic and well-described
- Ensure all tests pass before submitting PR

### Areas Where We Need Help

- 🗄️ Additional database platform support (MySQL, MongoDB, etc.)
- 🔌 Integration with more source control systems
- 📚 Documentation and tutorials
- 🧪 More comprehensive test coverage
- 🌐 Internationalization

For detailed guidelines, see [CONTRIBUTING.md](CONTRIBUTING.md)

---

## 📚 API Reference

### Command Line Interface

#### Global Options
```
--version       Show version information
--help          Show help message
--config PATH   Path to configuration file
--verbose       Enable verbose output
--quiet         Suppress non-error output
```

#### Commands

**`drm init`** - Initialize a new DRM project
```bash
drm init [--template TEMPLATE] [--path PATH]
```

**`drm deploy`** - Deploy a release
```bash
drm deploy [OPTIONS]

Options:
  --config PATH          Configuration file path
  --platform PLATFORM    Target platform
  --target TARGET        Target environment
  --parallel            Enable parallel execution
  --dry-run             Simulate deployment without executing
  --from-git            Deploy from Git repository
  --branch BRANCH       Git branch to deploy
  --commit COMMIT       Specific commit to deploy
```

**`drm rollback`** - Rollback a deployment
```bash
drm rollback --deployment-id ID [--force]
```

**`drm status`** - Check deployment status
```bash
drm status [--deployment-id ID] [--all]
```

**`drm list`** - List deployments
```bash
drm list [--platform PLATFORM] [--limit N]
```

### Python API

For programmatic access, you can import DRM-CLI as a Python module:

```python
from drm import Deployment, Config

# Load configuration
config = Config.from_file('config.yml')

# Create deployment
deployment = Deployment(config)

# Execute deployment
result = deployment.deploy()

if result.success:
    print(f"Deployment {result.id} completed successfully")
else:
    print(f"Deployment failed: {result.error}")
```

---

## 🛠️ Troubleshooting

### Common Issues

**Issue: `ModuleNotFoundError: No module named 'drm'`**
- **Solution**: Ensure DRM-CLI is properly installed and in your PYTHONPATH

**Issue: Connection timeout to database**
- **Solution**: Check network connectivity, firewall rules, and database credentials

**Issue: Permission denied errors**
- **Solution**: Ensure your database user has necessary privileges for DDL/DML operations

### Getting Help

- 📖 Check the [Wiki](https://github.com/dband-drm/drm-cli/wiki) for detailed documentation
- 🐛 Report bugs via [GitHub Issues](https://github.com/dband-drm/drm-cli/issues)
- 💬 Join discussions in [GitHub Discussions](https://github.com/dband-drm/drm-cli/discussions)
- 🌐 Visit our website: [www.d-band.com](https://www.d-band.com/)

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

Built with 💙 by experienced DBAs who understand the pain of data deployments.

Special thanks to:
- Our contributors and community members
- The open-source database driver maintainers
- Everyone who has provided feedback and bug reports

---

## 🔗 Links

- 🌐 **Website**: [www.d-band.com](https://www.d-band.com/)
- 📦 **GitHub Repository**: [github.com/dband-drm/drm-cli](https://github.com/dband-drm/drm-cli)
- 📖 **Documentation**: [GitHub Wiki](https://github.com/dband-drm/drm-cli/wiki)
- 🐛 **Issue Tracker**: [GitHub Issues](https://github.com/dband-drm/drm-cli/issues)
- 📢 **LinkedIn**: [D-Band Company Page](https://www.linkedin.com/company/106630725)

---

## 🌟 Star Us!

If you find DRM-CLI helpful, please consider giving us a ⭐ on GitHub. It helps others discover the project and motivates us to keep improving!

---

<div align="center">

**Made with ❤️ by [D-Band](https://www.d-band.com/)**

*Simplifying data release management, one deployment at a time.*

</div>
