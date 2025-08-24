# Personal Server BTRFS Backup Script

A Python-based tool for managing BTRFS snapshots and incremental backups using BTRFS send/receive.

## Key Features

- **Snapshot management**: Creates timestamped snapshots with optional comments
- **Incremental backups**: Uses BTRFS send/receive with proper parent relationships for efficient transfers
- **Retention policies**: Configurable age and count-based cleanup for both source and target locations
- **Multiple backup pairs**: Support for different source/target combinations (e.g. `/home` and `/`)
- **Safety-focused**: Clear error messages, dry-run mode, and operation halting on issues
- **Minimal dependencies**: Standalone script with type hints and comprehensive testing

## Quick Start

- Install [uv](https://docs.astral.sh/uv/)

```bash
./build.sh
```

## Project Structure

```
├── src/                    # Source code modules
├── tests/                  # Test files and reference outputs
├── docs/                   # Documentation
├── backup_script.py        # Main entry point
├── backup_config.toml      # Configuration file with comments
├── build.sh               # Development setup and checks
└── pyproject.toml          # Project dependencies and tool config
```

## Usage

The script operates on backup pairs defined in `backup_config.toml`:

```bash
# Create snapshots
./backup_script.py --snapshot --pair=root_system --suffix=pre-upgrade
./backup_script.py --snapshot --pair=home_directories

# Transfer snapshots to backup location
./backup_script.py --backup --pair=root_system
./backup_script.py --backup --all

# Clean up old snapshots
./backup_script.py --purge --pair=root_system
./backup_script.py --purge --all

# Options
./backup_script.py --dry-run --verbose --config=/path/to/config.toml
```

## Command line help

```
 ./backup_script.py --help
usage: backup_script.py [-h] (--snapshot | --backup | --purge) (--pair PAIR | --all) [--suffix SUFFIX] [-v] [--dry-run] [--config CONFIG]

BTRFS Snapshot Backup Tool

options:
  -h, --help       show this help message and exit
  --snapshot       Create a new snapshot
  --backup         Backup snapshots to target
  --purge          Remove old snapshots according to retention policy
  --pair PAIR      Target specific backup pair by name
  --all            Target all configured backup pairs
  --suffix SUFFIX  Suffix to add to snapshot name (for --snapshot only)
  -v, --verbose    Enable verbose output
  --dry-run        Show what would be done without executing
  --config CONFIG  Path to configuration file (default: backup_config.toml)
```

## Configuration

Uses TOML format for human-readable configuration. See [backup_config.toml](./backup_config.toml) for a commented example.

Key concepts:
- Each backup pair has independent retention policies
- Retention uses the larger of days or count limits
- Target locations can have different retention than source

## Development

Run [./build.sh](./build.sh) for formatting, linting, and testing. See [testing-approach.md](./docs/testing-approach.md) for details on the reference-based testing system.

## Technical Notes

- Snapshot names: `YYYY-MM-DDTHH:MM:SS-suffix` format for proper chronological ordering
- Parent relationships maintained for BTRFS CoW efficiency
- Operations scan existing snapshots before making changes

