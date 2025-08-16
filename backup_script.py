#!/usr/bin/env python3
"""BTRFS Snapshot Backup Tool

Main entry point for the backup script.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.config import Config


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
    
    # Load configuration
    try:
        config = Config.load_from_file(args.config)
    except FileNotFoundError:
        print(f"Error: Configuration file not found: {args.config}")
        return 1
    except Exception as e:
        print(f"Error loading configuration: {e}")
        return 1
    
    # TODO: Implement actual operations
    print(f"Operation: {'snapshot' if args.snapshot else 'backup' if args.backup else 'purge'}")
    print(f"Target: {'all pairs' if args.all else f'pair: {args.pair}'}")
    if args.snapshot and args.suffix:
        print(f"Suffix: {args.suffix}")
    print(f"Verbose: {args.verbose}")
    print(f"Dry run: {args.dry_run}")
    print(f"Config: {args.config}")
    print(f"Loaded {len(config.backup_pairs)} backup pairs")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
