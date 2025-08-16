#!/usr/bin/env python3
"""BTRFS Snapshot Backup Tool

Main entry point for the backup script.
"""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

from src.config import Config
from src.snapshots import Snapshot, scan_snapshots


def setup_logging(verbose: bool = False) -> None:
    """Configure logging for the application."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def execute_snapshot_operation(
    config: Config, pair_name: str | None, suffix: str, dry_run: bool
) -> None:
    """Execute snapshot creation operation."""
    logger = logging.getLogger(__name__)

    if pair_name:
        pairs = [config.get_backup_pair(pair_name)]
        if pairs[0] is None:
            logger.error(f"Backup pair '{pair_name}' not found in configuration")
            return
    else:
        pairs = config.backup_pairs

    for pair in pairs:
        if pair is None:
            continue

        # Generate timestamp (will be mocked in tests)
        timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

        # Build snapshot name
        snapshot_name = f"{timestamp}"
        if suffix:
            snapshot_name += f"-{suffix}"

        snapshot_path = f"{pair.source}/{snapshot_name}"

        # Build the btrfs command
        cmd = f"btrfs subvolume snapshot -r {pair.source} {snapshot_path}"

        if dry_run:
            logger.info(f"[DRY-RUN] Would execute: {cmd}")
        else:
            logger.info(f"Executing: {cmd}")
            # TODO: Actually execute the command

        logger.info(f"Created snapshot for pair '{pair.name}': {snapshot_path}")


def execute_backup_operation(
    config: Config, pair_name: str | None, dry_run: bool
) -> None:
    """Execute backup operation."""
    logger = logging.getLogger(__name__)

    if pair_name:
        pairs = [config.get_backup_pair(pair_name)]
        if pairs[0] is None:
            logger.error(f"Backup pair '{pair_name}' not found in configuration")
            return
    else:
        pairs = config.backup_pairs

    for pair in pairs:
        if pair is None:
            continue

        logger.info(f"Processing backup for pair '{pair.name}'")
        logger.info(f"Source: {pair.source} -> Target: {pair.target}")

        # Scan for snapshots in source and target
        source_snapshots = scan_snapshots(pair.source)
        target_snapshots = scan_snapshots(pair.target)

        if not source_snapshots:
            logger.info(f"No snapshots found in source: {pair.source}")
            continue

        # Convert to sets for efficient lookup
        target_snapshot_names = {snap.name for snap in target_snapshots}

        # Determine which snapshots need to be backed up
        snapshots_to_send: list[Snapshot] = []
        for snapshot in source_snapshots:
            if snapshot.name not in target_snapshot_names:
                snapshots_to_send.append(snapshot)

        if not snapshots_to_send:
            logger.info(f"Backup is up to date for pair '{pair.name}'")
            continue

        # Send snapshots with proper parent relationships
        previous_snapshot: str | None = None
        for snapshot in snapshots_to_send:
            snapshot_path = f"{pair.source}/{snapshot.name}"

            if previous_snapshot is None:
                # First snapshot or initial backup - no parent
                cmd = f"btrfs send {snapshot_path} | btrfs receive {pair.target}/"
            else:
                # Use previous snapshot as parent
                parent_path = f"{pair.source}/{previous_snapshot}"
                cmd = f"btrfs send -p {parent_path} {snapshot_path} | btrfs receive {pair.target}/"

            if dry_run:
                logger.info(f"[DRY-RUN] Would execute: {cmd}")
            else:
                logger.info(f"Executing: {cmd}")
                # TODO: Actually execute the command

            previous_snapshot = snapshot.name


def execute_purge_operation(
    config: Config, pair_name: str | None, dry_run: bool
) -> None:
    """Execute purge operation."""
    logger = logging.getLogger(__name__)

    if pair_name:
        pairs = [config.get_backup_pair(pair_name)]
        if pairs[0] is None:
            logger.error(f"Backup pair '{pair_name}' not found in configuration")
            return
    else:
        pairs = config.backup_pairs

    for pair in pairs:
        if pair is None:
            continue

        logger.info(f"Processing purge for pair '{pair.name}'")
        logger.info(
            f"Retention policy: {pair.retention_days} days, {pair.retention_count} snapshots"
        )

        # Purge both source and target
        _purge_location(
            pair.source, pair.retention_days, pair.retention_count, dry_run, logger
        )
        _purge_location(
            pair.target,
            pair.target_retention_days,
            pair.target_retention_count,
            dry_run,
            logger,
        )


def _purge_location(
    location: str,
    retention_days: int,
    retention_count: int,
    dry_run: bool,
    logger: logging.Logger,
) -> None:
    """Purge old snapshots from a specific location based on retention policy."""
    from datetime import datetime, timedelta

    # Scan for snapshots
    snapshots = scan_snapshots(location)

    if not snapshots:
        logger.info(f"No snapshots found in {location}")
        return

    # Sort snapshots by timestamp (newest first)
    snapshots_by_age = sorted(snapshots, reverse=True)

    # Protect the newest N snapshots (retention_count)
    # protected_snapshots = snapshots_by_age[:retention_count]
    candidate_snapshots = snapshots_by_age[retention_count:]

    if not candidate_snapshots:
        logger.info(
            f"All snapshots in {location} are protected by retention count ({retention_count})"
        )
        return

    # Calculate cutoff date for age-based deletion
    cutoff_date = datetime.now() - timedelta(days=retention_days)

    # From the unprotected snapshots, delete those older than retention_days
    snapshots_to_delete: list[Snapshot] = []
    for snapshot in candidate_snapshots:
        if snapshot.timestamp < cutoff_date:
            snapshots_to_delete.append(snapshot)

    if not snapshots_to_delete:
        logger.info(
            f"No snapshots in {location} are old enough to delete (older than {retention_days} days)"
        )
        return

    # Delete the snapshots
    for snapshot in snapshots_to_delete:
        cmd = f"btrfs subvolume delete {location}/{snapshot.name}"

        if dry_run:
            logger.info(f"[DRY-RUN] Would execute: {cmd}")
        else:
            logger.info(f"Executing: {cmd}")
            # TODO: Actually execute the command


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        description="BTRFS Snapshot Backup Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Main operations (mutually exclusive)
    operations = parser.add_mutually_exclusive_group(required=True)
    operations.add_argument(
        "--snapshot", action="store_true", help="Create a new snapshot"
    )
    operations.add_argument(
        "--backup", action="store_true", help="Backup snapshots to target"
    )
    operations.add_argument(
        "--purge",
        action="store_true",
        help="Remove old snapshots according to retention policy",
    )

    # Target selection
    target_group = parser.add_mutually_exclusive_group(required=True)
    target_group.add_argument(
        "--pair", type=str, help="Target specific backup pair by name"
    )
    target_group.add_argument(
        "--all", action="store_true", help="Target all configured backup pairs"
    )

    # Additional options
    parser.add_argument(
        "--suffix",
        type=str,
        default="",
        help="Suffix to add to snapshot name (for --snapshot only)",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose output"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without executing",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("backup_config.toml"),
        help="Path to configuration file (default: backup_config.toml)",
    )

    return parser


def main() -> int:
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()

    # Setup logging
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)

    # Load configuration
    try:
        config = Config.load_from_file(args.config)
    except FileNotFoundError:
        logger.error(f"Configuration file not found: {args.config}")
        return 1
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        return 1

    logger.info(f"Loaded configuration with {len(config.backup_pairs)} backup pairs")

    # Determine target pair
    target_pair = None if args.all else args.pair

    # Execute the requested operation
    try:
        if args.snapshot:
            execute_snapshot_operation(config, target_pair, args.suffix, args.dry_run)
        elif args.backup:
            execute_backup_operation(config, target_pair, args.dry_run)
        elif args.purge:
            execute_purge_operation(config, target_pair, args.dry_run)
    except Exception as e:
        logger.error(f"Operation failed: {e}")
        return 1

    logger.info("Operation completed successfully")
    return 0


if __name__ == "__main__":
    sys.exit(main())
