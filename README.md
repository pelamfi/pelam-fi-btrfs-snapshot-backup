# Personal Server BTRFS Backup Script

Features and specs:

- Python 3 stand alone script
- No packaging, used straight from git repo
- When invoked with --snapshot option takes snapshots with a timestamp format and optional comment
- When invoked with --backup option uses BTRFS send/receive to incrementally back up existing snapshots using BTRFS parent (`-p`) functionality
- When invoked with --purge option removes old snapshots according to schedule
  - Configuration defines number of snapshots and number of days to keep for both source and target
    - Larger number of snapshots is kept
- Reads a config file describing the locations and their schedules
  - Supports multiple pairs of source and target folders (eg one for `/home` and one for `/`)

- Nice command line interface

- Maximal safety with clear error messages and halting operation if something goes wrong

- Default no news is good news type operation, but `-v` option supported

- Current snapshot names are of format YYYY-MM-DD-some-text, but new ones will be YYYY-MM-DDTHH:MM:SS-some-text to support accurate parenting.


NOTE: Snapshots must maintain strict order because btrfs-send maintains block reuse / CoW properties if the parenting relationship of snapshots is correct.

# Tools used

- Minimal dependencies
- Strict python type hints
- `ruff` for formatting linting
- `uv` for virtual environment, dependencies etc
- `pytest` for tests
- `build.sh` gets possible dependencies and runs all checks and tests

# Command Line Design

The script supports three main operations, each targeting a specific backup pair defined in the configuration:

## Snapshot Creation
```bash
./backup_script.py --snapshot --pair=root_system --suffix=pre-upgrade
./backup_script.py --snapshot --pair=home_directories --suffix=weekly-backup
./backup_script.py --snapshot --pair=root_system  # No suffix, just timestamp
```

## Backup Execution
```bash
./backup_script.py --backup --pair=root_system
./backup_script.py --backup --pair=home_directories
./backup_script.py --backup --all  # Backup all configured pairs
```

## Purge Old Snapshots
```bash
./backup_script.py --purge --pair=root_system
./backup_script.py --purge --pair=home_directories  
./backup_script.py --purge --all  # Purge all configured pairs
```

## Global Options
- `-v, --verbose`: Enable verbose output
- `--dry-run`: Show what would be done without executing
- `--config=/path/to/config.toml`: Use custom config file (default: `./backup_config.toml`)

# Configuration File Format

The script uses TOML format for configuration, providing a human-readable and type-safe configuration structure:

```toml
[global]
default_verbose = false
dry_run = false

[[backup_pairs]]
name = "root_system"
source = "/btrfs/btrfs-subvolumes/root"
target = "/backup/btrfs-subvolumes/root"
retention_days = 30
retention_count = 10
target_retention_days = 90
target_retention_count = 20

[[backup_pairs]]
name = "home_directories"
source = "/btrfs/btrfs-subvolumes/home"
target = "/backup/btrfs-subvolumes/home"
retention_days = 14
retention_count = 15
target_retention_days = 60
target_retention_count = 30
```

## Configuration Options

### Global Section
- `default_verbose`: Enable verbose output by default
- `dry_run`: Enable dry-run mode by default

### Backup Pairs
Each `[[backup_pairs]]` section defines a source/target pair with:
- `name`: Unique identifier used with `--pair` option
- `source`: Source BTRFS subvolume path where snapshots are created
- `target`: Target location where snapshots are backed up
- `retention_days`: Days to keep snapshots in source location
- `retention_count`: Minimum number of snapshots to keep in source (whichever is larger applies)
- `target_retention_days`: Days to keep backups in target location
- `target_retention_count`: Minimum number of backups to keep in target (whichever is larger applies)

## Raw examples for inspiration

Not actual output for this program, but stored here to help initial dev:

Example of raw command to send and receive btrfs snapshots:

```bash
btrfs send -p /btrfs/btrfs-subvolumes/root-backup/2025-07-06-unifi-stuff-works/ /btrfs/btrfs-subvolumes/root-backup/2025-08-11-backup/ | pv | btrfs receive /root/western-digital-red-backup/btrfs-subvolumes/root-backup/
```

Example of current snapshots:
```bash
ls /btrfs/btrfs-subvolumes/root-backup/
2025-05-18-after-btrfs-subvol-reorg  2025-05-18-pre-upgrade  2025-07-06-post-upgrade  2025-07-06-unifi-stuff-works
2025-05-18-pre-subvolume-reorg       2025-05-29-pre-upgrade  2025-07-06-pre-upgrade   2025-08-11-backup
```

Example command used to create current snapshots:
```bash
btrfs subvolume snapshot -r / /btrfs/btrfs-subvolumes/root-backup/$(printf '%(%F)T\n' -1)-post-upgrade
```

# Detailed operation

The script will scan the source and target folder for snapshots and identify snapshots on each.

Then depending on mode it will either remove old snapshots or send them from source to target.

