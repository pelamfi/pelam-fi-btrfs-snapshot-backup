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

```bash
# Install uv (see: https://docs.astral.sh/uv/)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Setup and run checks
git clone <repository>
cd pelam-fi-btrfs-snapshot-backup
./build.sh
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

## Configuration

Uses TOML format for human-readable configuration. See `backup_config.toml` for a commented example.

Key concepts:
- Each backup pair has independent retention policies
- Retention uses the larger of days or count limits
- Target locations can have different retention than source

## Development

Run `./build.sh` for formatting, linting, and testing. See `docs/testing-approach.md` for details on the reference-based testing system.

## Technical Notes

- Snapshot names: `YYYY-MM-DDTHH:MM:SS-suffix` format for proper chronological ordering
- Parent relationships maintained for BTRFS CoW efficiency
- Operations scan existing snapshots before making changes

