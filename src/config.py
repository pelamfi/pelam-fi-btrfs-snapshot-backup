"""Configuration management for BTRFS backup tool."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass
class BackupPair:
    """Configuration for a source/target backup pair."""

    name: str
    source: str
    target: str
    retention_days: int
    retention_count: int
    target_retention_days: int
    target_retention_count: int


@dataclass
class GlobalConfig:
    """Global configuration settings."""

    default_verbose: bool = False
    dry_run: bool = False


@dataclass
class Config:
    """Complete configuration for the backup tool."""

    global_config: GlobalConfig
    backup_pairs: list[BackupPair]

    @classmethod
    def load_from_file(cls, config_path: Path) -> Config:
        """Load configuration from a TOML file."""
        with config_path.open("rb") as f:
            data = tomllib.load(f)

        global_config = GlobalConfig(**data.get("global", {}))
        
        backup_pairs = [
            BackupPair(**pair_data) 
            for pair_data in data.get("backup_pairs", [])
        ]

        return cls(global_config=global_config, backup_pairs=backup_pairs)

    def get_backup_pair(self, name: str) -> BackupPair | None:
        """Get a backup pair by name."""
        for pair in self.backup_pairs:
            if pair.name == name:
                return pair
        return None
