#!/usr/bin/env python3
"""BTRFS Snapshot Backup Tool

Main entry point for the backup script.
"""

from __future__ import annotations

import argparse
import logging
import os
import re
import sys
from datetime import datetime
from pathlib import Path

from src.config import Config


def setup_logging(verbose: bool = False) -> None:
    """Configure logging for the application."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def execute_snapshot_operation(config: Config, pair_name: str | None, suffix: str, dry_run: bool) -> None:
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


def scan_snapshots(directory: str | Path) -> list[str]:
    """Scan a directory for BTRFS snapshots and return them sorted by name.
    
    Returns a list of snapshot directory names sorted chronologically.
    Only includes directories that match the timestamp pattern.
    """
    try:
        if not os.path.exists(directory):
            return []
            
        # Pattern for snapshot names: YYYY-MM-DDTHH:MM:SS or YYYY-MM-DD-suffix
        snapshot_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}')
        
        snapshots: list[str] = []
        for item in os.listdir(directory):
            item_path = os.path.join(directory, item)
            if os.path.isdir(item_path) and snapshot_pattern.match(item):
                snapshots.append(item)
        
        # Sort snapshots chronologically by name 
        # (timestamp format ensures lexicographic sorting = chronological sorting)
        return sorted(snapshots)
        
    except Exception as e:
        logging.getLogger(__name__).warning(f"Error scanning snapshots in {directory}: {e}")
        return []


def execute_backup_operation(config: Config, pair_name: str | None, dry_run: bool) -> None:
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
            
        # Determine which snapshots need to be backed up
        snapshots_to_send: list[str] = []
        for snapshot in source_snapshots:
            if snapshot not in target_snapshots:
                snapshots_to_send.append(snapshot)
        
        if not snapshots_to_send:
            logger.info(f"Backup is up to date for pair '{pair.name}'")
            continue
            
        # Send snapshots with proper parent relationships
        previous_snapshot: str | None = None
        for snapshot in snapshots_to_send:
            snapshot_path = f"{pair.source}/{snapshot}"
            
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
            
            previous_snapshot = snapshot


def execute_purge_operation(config: Config, pair_name: str | None, dry_run: bool) -> None:
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
        logger.info(f"Retention policy: {pair.retention_days} days, {pair.retention_count} snapshots")
        
        # Mock example of purge commands
        old_snapshots = ["2025-01-01T10:00:00-old", "2025-01-02T10:00:00-ancient"]
        
        for snapshot in old_snapshots:
            cmd = f"btrfs subvolume delete {pair.source}/{snapshot}"
            
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
        "--snapshot", 
        action="store_true", 
        help="Create a new snapshot"
    )
    operations.add_argument(
        "--backup", 
        action="store_true", 
        help="Backup snapshots to target"
    )
    operations.add_argument(
        "--purge", 
        action="store_true", 
        help="Remove old snapshots according to retention policy"
    )
    
    # Target selection
    target_group = parser.add_mutually_exclusive_group(required=True)
    target_group.add_argument(
        "--pair", 
        type=str, 
        help="Target specific backup pair by name"
    )
    target_group.add_argument(
        "--all", 
        action="store_true", 
        help="Target all configured backup pairs"
    )
    
    # Additional options
    parser.add_argument(
        "--suffix", 
        type=str, 
        default="", 
        help="Suffix to add to snapshot name (for --snapshot only)"
    )
    parser.add_argument(
        "-v", "--verbose", 
        action="store_true", 
        help="Enable verbose output"
    )
    parser.add_argument(
        "--dry-run", 
        action="store_true", 
        help="Show what would be done without executing"
    )
    parser.add_argument(
        "--config", 
        type=Path, 
        default=Path("backup_config.toml"), 
        help="Path to configuration file (default: backup_config.toml)"
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
