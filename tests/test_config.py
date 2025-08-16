"""Tests for the configuration module."""

from __future__ import annotations

import tempfile
from pathlib import Path

from src.config import BackupPair, Config, GlobalConfig


def test_backup_pair_creation():
    """Test BackupPair creation."""
    pair = BackupPair(
        name="test",
        source="/source",
        target="/target",
        retention_days=30,
        retention_count=10,
        target_retention_days=90,
        target_retention_count=20,
    )
    assert pair.name == "test"
    assert pair.source == "/source"
    assert pair.target == "/target"


def test_global_config_defaults():
    """Test GlobalConfig default values."""
    config = GlobalConfig()
    assert config.default_verbose is False
    assert config.dry_run is False


def test_config_load_from_file():
    """Test loading configuration from TOML file."""
    toml_content = """
[global]
default_verbose = true
dry_run = false

[[backup_pairs]]
name = "test_pair"
source = "/test/source"
target = "/test/target"
retention_days = 15
retention_count = 5
target_retention_days = 45
target_retention_count = 15
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write(toml_content)
        f.flush()

        config = Config.load_from_file(Path(f.name))

        assert config.global_config.default_verbose is True
        assert config.global_config.dry_run is False
        assert len(config.backup_pairs) == 1

        pair = config.backup_pairs[0]
        assert pair.name == "test_pair"
        assert pair.source == "/test/source"
        assert pair.retention_days == 15


def test_get_backup_pair():
    """Test getting backup pair by name."""
    pair1 = BackupPair("pair1", "/src1", "/tgt1", 30, 10, 90, 20)
    pair2 = BackupPair("pair2", "/src2", "/tgt2", 15, 5, 45, 15)

    config = Config(GlobalConfig(), [pair1, pair2])

    found_pair = config.get_backup_pair("pair1")
    assert found_pair is not None
    assert found_pair.name == "pair1"

    not_found = config.get_backup_pair("nonexistent")
    assert not_found is None
