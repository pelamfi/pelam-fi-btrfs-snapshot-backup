# Personal Server BTRFS Backup Script

Features and specs:

- Python 3 stand alone script
- No packaging, used straight from git repo
- When invoked with --snapshot option takes snapshots with a timestamp format and optional comment
- When invoked with --backup option uses BTFS send/receive to incrementally (BTRFS parent `-p`) back up existing snapshots
- When invoked with --purge option removes old snapshots according to schedule
  - Configuration defines number of snapshots and number of days to keep for both source and target
    - Larger number of snapshots is kept
- Reads a config file describing the locations and their schedules
  - Supports multiple pairs of source and target folders (eg one for `/home` and one for `/`)

- Nice command line interface

- Maximal safety with clear error messages and halting operation if something goes wrong

- Default no news is good news type operation, but `-v` option supported

- Current snapshot names are of format YYY-MM-DD-some-text, but new ones will be YYYY-MM-DDTHH:MM:SS-some-text to support accurate parenting.


NOTE: Snapshots must maintain strict order because btrfs-send maintains block reuse / CoW properties if the parenting relationship of snapshots is correct.

# Tools used

- Minimal dependencies
- Strict python type hints
- `ruff` for formatting linting
- `uv` for virtual environment, dependencies etc
- `pytest` for tests
- `build.sh` gets possible dependencies and runs all checks and tests

## Raw examples for inspiration

Not actual output for this program, but stored here to help initial dev:

Example of raw command to send and receive btrfs snapshots:

```bash
btrfs send -p /btrfs/btrfs-subvolumes/root-backup/2025-07-06-unifi-stuff-works/ /btrfs/btrfs-subvolumes/root-backup/2025-08-11-backup/ | pv | btrfs receive /root/western-digital-red-backup/btrfs-subvolumes/root-backup/
```

Example of current snapshots
```bash
ls /btrfs/btrfs-subvolumes/root-backup/
2025-05-18-after-btrfs-subvol-reorg  2025-05-18-pre-upgrade  2025-07-06-post-upgrade  2025-07-06-unifi-stuff-works
2025-05-18-pre-subvolume-reorg       2025-05-29-pre-upgrade  2025-07-06-pre-upgrade   2025-08-11-backup
```


# Detailed operation

The script will scan the source and target folder for snapshots and identify snapshots on each.

Then depending on mode it will either remove old snapshots or send them from source to target.

