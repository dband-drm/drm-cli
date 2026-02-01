# DRM-CLI: Data Release Management

<div align="center">

![DRM Logo](https://raw.githubusercontent.com/dband-drm/drm-cli/main/Images/dband_logo.jpg)

**A unified CLI tool for managing and controlling data releases across multiple platforms and source controls**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Latest Release](https://img.shields.io/github/v/release/dband-drm/drm-cli)](https://github.com/dband-drm/drm-cli/releases)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

[Website](https://www.d-band.com/) • [Documentation](https://github.com/dband-drm/drm-cli/wiki) • [Issues](https://github.com/dband-drm/drm-cli/issues) • [Releases](https://github.com/dband-drm/drm-cli/releases)

</div>

---

##  Introduction

DRM-CLI is a data release management tool for database deployments across multiple platforms. Born from 25+ years of database administration experience, DRM-CLI provides a unified Python-based CLI for managing database releases, tracking deployment history, and ensuring consistent deployments across environments.

### Why DRM-CLI?

Traditional data deployment requires juggling multiple tools:
- Source control systems
- Platform-specific deployment scripts
- Custom utilities for each database type
- Manual tracking of what's deployed where

**DRM-CLI provides a single interface for all database deployments.**

### Key Benefits

- **Unified interface** for Oracle, PostgreSQL, and SQL Server
- **Built-in retry mechanism** for resilient deployments
- **Parallel execution** for deploying to multiple targets
- **Deployment tracking** with SQLite or JSON database
- **Secure encryption** for sensitive configuration data
- **Cross-platform** support (Windows & Linux)
- **Integration** with Flyway, Liquibase, and sqlpackage

---

##  Getting Started

### Prerequisites

Before installing DRM-CLI, ensure you have the following:

- **Python 3.8 or higher**
- **pip** (Python package installer)
- **Git** (for version control integration)
- **Database drivers** (depending on your target platforms):
  - Oracle: `cx_Oracle` or `oracledb`
  - PostgreSQL: `psycopg2`
  - SQL Server: `pyodbc`
- **Optional deployment tools**:
  - Flyway (for database migrations)
  - Liquibase (for database version control)
  - sqlpackage (for SQL Server deployments)

### Installation

####  Installation Script (Recommended)

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

3. **Follow the interactive prompts** to configure your installation:
   - Choose installation type: JSON or SQLite (default: SQLite)
   - Set installation path (default: `~/drm`)
   - Configure encryption key (optional but recommended)



##  Software Dependencies

### Core Dependencies

- **Python 3.8+** - Core runtime
- **argparse** - CLI argument parsing (built-in)
- **json** - Configuration file handling (built-in)
- **logging** - Logging framework (built-in)
- **pathlib** - File path operations (built-in)

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

### Optional Deployment Tools

- **Flyway** - Database migration tool
- **Liquibase** - Database version control
- **sqlpackage** - SQL Server deployment tool
- **sqlcmd** - SQL Server command-line tool

---

##  Features & Usage

### Core Features

#### 1. Multi-Platform Support

Deploy to multiple database platforms from your DRM installation directory:

```bash
# Deploy to production Oracle
python drm_deploy.py -r OracleRelease1 -c production_oracle --deploy

# Deploy to PostgreSQL development environment
python drm_deploy.py -r PgRelease2 -c dev_postgres --deploy

# Deploy to SQL Server staging
python drm_deploy.py -r SqlRelease3 -c stage_mssql --deploy
```

#### 2. Source Control Integration

Configure your solutions in `drm_db` to point to source control repositories:

```json
"solutions": [
    {
        "name": "My Database Project",
        "solution_type_id": 1,
        "path": "../my-db-repo",
        ...
    }
]
```

#### 3. Intelligent Retry Mechanism

Configure automatic retry for transient failures in `drm_db`:

```json
{
    "max_retries": 3
}
```

#### 4. Parallel Execution

Deploy to multiple targets simultaneously by configuring parallel execution in `drm_db`:

```json
{
    "targets_list": "[\"DB_B1\", \"DB_B2\", \"DB_B3\", \"DB_B4\"]",
    "targets_priority": "[\"DB_B4\", \"DB_B2\"]",
    "max_degree_in_parallel": 2
}
```

#### 5. Dry Run Mode

Test deployments without executing them:

```bash
python drm_deploy.py -r MyRelease -c production --dryrun
```

#### 6. Secure Encryption

Protect sensitive data with encryption:

```bash
# Encrypt a password or sensitive text
python drm_crypto.py --encrypt -p MyEncryptionKey -t "my-db-password"

# Change encryption key
python drm_crypto.py --changepassword -p OldKey -n NewKey
```

#### 7. Alignment Mode

Align database state with DRM tracking:

```bash
python drm_deploy.py -r MyRelease -c production --align
```

### Configuration

DRM-CLI uses JSON/SQLite configuration files:

- **`drm_deploy.config`** - Main app configuration  
- **`install.config`** - Installation settings
- **DRM Database** - Stores releases, connections, and deployment history (SQLite or JSON)

#### Sample Configuration Structure

```json
{
    "drm_version": "1.1.0",
    "installation_info": {
        "installation_type": "sqlite",
        "db_secured": true,
        "security_text": "encrypted_validation_string"
    },
    "config": {
        "build_folder_name": "build",
        "db_folder_name": "db",
        "db_file_name": "drm_db"
    },
    "connections": [
        {
            "name": "production_oracle",
            "type": "oracle",
            "host": "oracle.example.com",
            "port": 1521,
            "service": "PROD"
        }
    ],
    "releases": [
        {
            "release_id": "Release1.0",
            "description": "Initial release"
        }
    ]
}
```

---

##  Latest Releases

### v1.1.0 (Latest)
-  Added PostgreSQL support
-  Enhanced Oracle integration
-  Fixed parallel execution bugs
-  Improved documentation

### v1.0.0
-  Initial release
-  Oracle database support
-  Git integration
-  Basic deployment workflows

[View all releases →](https://github.com/dband-drm/drm-cli/releases)

---




---

##  Project Structure

```
drm-cli/
├── drm/                      # Main deployment scripts
│   ├── drm_deploy.py         # Deployment CLI
│   ├── drm_crypto.py         # Encryption utilities
│   └── modules/              # Supporting modules (deprecated)
├── modules/                  # Core functionality
│   ├── auth.py               # Authentication & password validation
│   ├── builder.py            # Build release packages
│   ├── deploy.py             # Deployment orchestration
│   ├── validator.py          # Validation logic
│   ├── oracle.py             # Oracle database support
│   ├── postgresql.py         # PostgreSQL support
│   ├── mssql.py              # SQL Server support
│   ├── flyway.py             # Flyway integration
│   ├── liquibase.py          # Liquibase integration
│   ├── sqlpackage.py         # sqlpackage integration
│   ├── crypto.py             # Encryption/decryption
│   ├── drm_logger.py         # Logging framework
│   ├── files_and_folders.py  # File operations
│   └── init_db.py            # Database initialization
├── init_drm_db/              # DRM database initialization scripts
├── upgrade/                  # Upgrade scripts for DRM versions
├── Images/                   # Logo and images
├── install.py                # Installation script
├── uninstall.py              # Uninstallation script
├── install.config            # Installation configuration template
├── LICENSE                   # MIT License
└── README.md                 # This file
```

---

##  Contributing

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

-  Additional database platform support (MySQL, MongoDB, etc.)
-  Internationalization

For detailed guidelines, see [CONTRIBUTING.md](CONTRIBUTING.md)

---

##  API Reference

### Command Line Interface

#### Installation Commands

**`drm_install.py`** - Install or upgrade DRM
```bash
python drm_install.py [OPTIONS]

Options:
  -d INSTALL_TYPE     Installation type: json or sqlite (default: sqlite)
  -f INSTALL_PATH     Installation folder path (default: ~/drm)
  -p ENCRYPTION_KEY   Encryption key (none for no encryption)
  --trace             Enable debug logging
```

#### Deployment Commands

**`drm_deploy.py`** - Deploy a release
```bash
python drm_deploy.py [OPTIONS]

Required:
  -c CONNECTION       Connection name from drm_deploy.config
  -r RELEASE          Release ID from DRM database

Optional:
  -p ENCRYPTION_KEY   Encryption key (or use DRM_SECRET env var)
  --dryrun            Generate scripts without executing
  --deploy            Generate and execute deployment scripts
  --align             Align database state with DRM tracking
  --trace             Enable debug logging

Examples:
  python drm_deploy.py -r Release1.0 -c prod_db --dryrun
  python drm_deploy.py -r Release1.0 -c prod_db --deploy -p MyKey
  python drm_deploy.py -r Release1.0 -c prod_db --align
```

**`drm_crypto.py`** - Encryption utilities
```bash
python drm_crypto.py [OPTIONS]

Required (one of):
  --encrypt           Encrypt a text string
  --changepassword    Change DRM encryption key

Optional:
  -p ENCRYPTION_KEY   Current encryption key
  -n NEW_KEY          New encryption key (for changepassword)
  -t TEXT             Text to encrypt (for encrypt mode)
  --trace             Enable debug logging

Examples:
  python drm_crypto.py --encrypt -p MyKey -t "password123"
  python drm_crypto.py --changepassword -p OldKey -n NewKey
```

**`uninstall.py`** - Uninstall DRM
```bash
python uninstall.py [OPTIONS]
```
 
 



---

## 🛠️ Troubleshooting

### Common Issues

**Issue: `ModuleNotFoundError: No module named 'modules'`**
- **Solution**: Ensure you're running commands from the DRM installation directory or the repository root

**Issue: "Wrong encryption key!!!"**
- **Solution**: Use the correct encryption key set during installation, or set `DRM_SECRET` environment variable

**Issue: Connection timeout to database**
- **Solution**: Check network connectivity, firewall rules, and database credentials in `drm_deploy.config`

**Issue: Permission denied errors**
- **Solution**: Ensure your database user has necessary privileges for DDL/DML operations

**Issue: Flyway/Liquibase/sqlpackage not found**
- **Solution**: Install the required tool and configure its path in `drm_db`

### Environment Variables

- **`DRM_SECRET`** - Set this to avoid entering encryption key for each command
- **`DRM_LOGGER_LEVEL`** - Set logging level (automatically set by `--trace` flag)
- **`DRM_LOGGER_MODE`** - Logger mode: 0=install, 1=deploy, 2=crypto, 3=uninstall

### Getting Help

-  Check the [Wiki](https://github.com/dband-drm/drm-cli/wiki) for detailed documentation
-  Report bugs via [GitHub Issues](https://github.com/dband-drm/drm-cli/issues)
-  Join discussions in [GitHub Discussions](https://github.com/dband-drm/drm-cli/discussions)
-  Visit our website: [www.d-band.com](https://www.d-band.com/)

---

##  License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

##  Acknowledgments

Built with 💙 by experienced DBAs who understand the pain of data deployments.

Special thanks to:
- Our contributors and community members
- The open-source database driver maintainers
- Everyone who has provided feedback and bug reports

---

##  Links

-  **Website**: [www.d-band.com](https://www.d-band.com/)
-  **GitHub Repository**: [github.com/dband-drm/drm-cli](https://github.com/dband-drm/drm-cli)
-  **Documentation**: [GitHub Wiki](https://github.com/dband-drm/drm-cli/wiki)
-  **Issue Tracker**: [GitHub Issues](https://github.com/dband-drm/drm-cli/issues)
-  **LinkedIn**: [D-Band Company Page](https://www.linkedin.com/company/106630725)

---

##  Star Us!

If you find DRM-CLI helpful, please consider giving us a ⭐ on GitHub. 
It helps others discover the project and motivates us to keep improving!

---

<div align="center">

**Made with ❤️ by [D-Band](https://www.d-band.com/)**

*Simplifying data release management, one deployment at a time.*

</div>

