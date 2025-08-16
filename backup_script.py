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
            
        # TODO: Scan for existing snapshots and determine parent relationships
        # For now, just log what would happen
        
        logger.info(f"Processing backup for pair '{pair.name}'")
        logger.info(f"Source: {pair.source} -> Target: {pair.target}")
        
        # Mock example of incremental backup command
        cmd = f"btrfs send -p {pair.source}/previous-snapshot {pair.source}/latest-snapshot | btrfs receive {pair.target}/"
        
        if dry_run:
            logger.info(f"[DRY-RUN] Would execute: {cmd}")
        else:
            logger.info(f"Executing: {cmd}")
            # TODO: Actually execute the command


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
