"""Integration tests for main operations using reference-based testing."""

from __future__ import annotations

import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

from tests.test_utils import LogCapture, compare_with_reference, create_temp_config

# Add the project root to Python path to import backup_script
sys.path.insert(0, str(Path(__file__).parent.parent))
import backup_script

# Fixed timestamp for deterministic tests
FIXED_TIMESTAMP = "2025-08-16T14:30:00"
FIXED_LOG_TIME = time.mktime(time.strptime("2025-08-16 14:30:00", "%Y-%m-%d %H:%M:%S"))


def create_snapshot_dirs(base_path: Path, snapshot_names: list[str]) -> None:
    """Create empty snapshot directories with given names."""
    base_path.mkdir(parents=True, exist_ok=True)
    for name in snapshot_names:
        (base_path / name).mkdir(exist_ok=True)


def setup_backup_test_dirs(
    source_snapshots: list[str], target_snapshots: list[str]
) -> tuple[Path, Path]:
    """Setup temporary directories with snapshot folders for backup testing.

    Returns tuple of (source_path, target_path).
    """
    temp_dir = Path(tempfile.mkdtemp())
    source_path = temp_dir / "source"
    target_path = temp_dir / "target"

    create_snapshot_dirs(source_path, source_snapshots)
    create_snapshot_dirs(target_path, target_snapshots)

    return source_path, target_path


def setup_purge_test_dirs(
    source_snapshots: list[str], target_snapshots: list[str]
) -> tuple[Path, Path]:
    """Setup temporary directories with snapshot folders for purge testing.

    Returns tuple of (source_path, target_path).
    """
    return setup_backup_test_dirs(source_snapshots, target_snapshots)


class TestMainOperations:
    """Test main operations using dry-run output and reference files."""

    def test_snapshot_operation_single_pair(self):
        """Test snapshot operation for a single backup pair."""
        # Setup test data
        backup_pairs: list[dict[str, str | int]] = [
            {
                "name": "test_root",
                "source": "/tmp/test/source/root",
                "target": "/tmp/test/target/root",
                "retention_days": 30,
                "retention_count": 10,
                "target_retention_days": 90,
                "target_retention_count": 20,
            }
        ]

        # Create temporary config
        config_path = create_temp_config(backup_pairs)

        try:
            # Mock datetime to get consistent timestamps
            with patch("backup_script.datetime") as mock_datetime:
                mock_datetime.now.return_value.strftime.return_value = FIXED_TIMESTAMP

                # Capture logging output with fixed timestamp
                with LogCapture() as log_capture:
                    # Set fixed time for logging
                    log_capture.set_time_func(lambda: FIXED_LOG_TIME)

                    # Mock sys.argv to simulate command line
                    test_args = [
                        "backup_script.py",
                        "--snapshot",
                        "--pair=test_root",
                        "--suffix=test-snapshot",
                        "--dry-run",
                        "--verbose",
                        f"--config={config_path}",
                    ]

                    with patch.object(sys, "argv", test_args):
                        result = backup_script.main()

                    assert result == 0

                    # Get the captured output
                    actual_output = log_capture.get_output()

                    # Compare with reference
                    test_dir = Path(__file__).parent
                    compare_with_reference(
                        "snapshot_single_pair", actual_output, test_dir
                    )
        finally:
            # Clean up temporary config file
            config_path.unlink()

    def test_snapshot_operation_all_pairs(self):
        """Test snapshot operation for all backup pairs."""
        # Setup test data with multiple pairs
        backup_pairs: list[dict[str, str | int]] = [
            {
                "name": "test_root",
                "source": "/tmp/test/source/root",
                "target": "/tmp/test/target/root",
            },
            {
                "name": "test_home",
                "source": "/tmp/test/source/home",
                "target": "/tmp/test/target/home",
                "retention_days": 14,
                "retention_count": 15,
            },
        ]

        # Create temporary config
        config_path = create_temp_config(backup_pairs)

        try:
            # Mock datetime to get consistent timestamps
            with patch("backup_script.datetime") as mock_datetime:
                mock_datetime.now.return_value.strftime.return_value = FIXED_TIMESTAMP

                # Capture logging output with fixed timestamp
                with LogCapture() as log_capture:
                    # Set fixed time for logging
                    log_capture.set_time_func(lambda: FIXED_LOG_TIME)

                    # Mock sys.argv to simulate command line
                    test_args = [
                        "backup_script.py",
                        "--snapshot",
                        "--all",
                        "--suffix=weekly-backup",
                        "--dry-run",
                        "--verbose",
                        f"--config={config_path}",
                    ]

                    with patch.object(sys, "argv", test_args):
                        result = backup_script.main()

                    assert result == 0

                    # Get the captured output
                    actual_output = log_capture.get_output()

                    # Compare with reference
                    test_dir = Path(__file__).parent
                    compare_with_reference(
                        "snapshot_all_pairs", actual_output, test_dir
                    )
        finally:
            # Clean up temporary config file
            config_path.unlink()

    def test_backup_no_snapshots_folder(self):
        """Test backup operation when snapshots folder doesn't exist."""
        # Expected: Error logged about missing snapshots folder
        # Setup: No directories created
        # Expected result: Error condition logged, operation fails gracefully

        backup_pairs: list[dict[str, str | int]] = [
            {
                "name": "test_root",
                "source": "/tmp/nonexistent/source/root",
                "target": "/tmp/nonexistent/target/root",
            }
        ]

        config_path = create_temp_config(backup_pairs)

        try:
            with LogCapture() as log_capture:
                log_capture.set_time_func(lambda: FIXED_LOG_TIME)

                test_args = [
                    "backup_script.py",
                    "--backup",
                    "--pair=test_root",
                    "--dry-run",
                    "--verbose",
                    f"--config={config_path}",
                ]

                with patch.object(sys, "argv", test_args):
                    # Should not crash, but log error
                    backup_script.main()

                actual_output = log_capture.get_output()
                test_dir = Path(__file__).parent
                compare_with_reference(
                    "backup_no_snapshots_folder", actual_output, test_dir
                )
        finally:
            config_path.unlink()

    def test_backup_no_snapshots_in_either(self):
        """Test backup operation when both source and target have no snapshots."""
        # Expected: Info logged about no snapshots found, not an error
        # Setup: Empty source and target directories
        # Expected result: Informational message, successful completion

        source_path, target_path = setup_backup_test_dirs([], [])

        backup_pairs: list[dict[str, str | int]] = [
            {
                "name": "test_root",
                "source": str(source_path),
                "target": str(target_path),
            }
        ]

        config_path = create_temp_config(backup_pairs)

        try:
            with LogCapture() as log_capture:
                log_capture.set_time_func(lambda: FIXED_LOG_TIME)

                test_args = [
                    "backup_script.py",
                    "--backup",
                    "--pair=test_root",
                    "--dry-run",
                    "--verbose",
                    f"--config={config_path}",
                ]

                with patch.object(sys, "argv", test_args):
                    result = backup_script.main()

                assert result == 0
                actual_output = log_capture.get_output()
                test_dir = Path(__file__).parent
                # Normalize the temp directory path for consistent testing
                temp_base = str(source_path.parent)
                compare_with_reference(
                    "backup_no_snapshots_in_either",
                    actual_output,
                    test_dir,
                    [temp_base],
                )
        finally:
            config_path.unlink()

    def test_backup_single_snapshot_in_source_none_in_target(self):
        """Test backup operation with one snapshot in source, none in target."""
        # Expected: Single snapshot sent without parent (initial backup)
        # Setup: One snapshot in source, empty target
        # Expected result: btrfs send without -p flag to target

        source_path, target_path = setup_backup_test_dirs(["2025-08-16T10:00:00"], [])

        backup_pairs: list[dict[str, str | int]] = [
            {
                "name": "test_root",
                "source": str(source_path),
                "target": str(target_path),
            }
        ]

        config_path = create_temp_config(backup_pairs)

        try:
            with LogCapture() as log_capture:
                log_capture.set_time_func(lambda: FIXED_LOG_TIME)

                test_args = [
                    "backup_script.py",
                    "--backup",
                    "--pair=test_root",
                    "--dry-run",
                    "--verbose",
                    f"--config={config_path}",
                ]

                with patch.object(sys, "argv", test_args):
                    result = backup_script.main()

                assert result == 0
                actual_output = log_capture.get_output()
                test_dir = Path(__file__).parent
                # Normalize the temp directory path for consistent testing
                temp_base = str(source_path.parent)
                compare_with_reference(
                    "backup_single_snapshot_source_none_target",
                    actual_output,
                    test_dir,
                    [temp_base],
                )
        finally:
            config_path.unlink()

    def test_backup_single_snapshot_in_both(self):
        """Test backup operation with same snapshot in both source and target."""
        # Expected: No operation needed, everything up to date
        # Setup: Same snapshot in both source and target
        # Expected result: Log message indicating backup is up to date

        source_path, target_path = setup_backup_test_dirs(
            ["2025-08-16T10:00:00"], ["2025-08-16T10:00:00"]
        )

        backup_pairs: list[dict[str, str | int]] = [
            {
                "name": "test_root",
                "source": str(source_path),
                "target": str(target_path),
            }
        ]

        config_path = create_temp_config(backup_pairs)

        try:
            with LogCapture() as log_capture:
                log_capture.set_time_func(lambda: FIXED_LOG_TIME)

                test_args = [
                    "backup_script.py",
                    "--backup",
                    "--pair=test_root",
                    "--dry-run",
                    "--verbose",
                    f"--config={config_path}",
                ]

                with patch.object(sys, "argv", test_args):
                    result = backup_script.main()

                assert result == 0
                actual_output = log_capture.get_output()
                test_dir = Path(__file__).parent
                # Normalize the temp directory path for consistent testing
                temp_base = str(source_path.parent)
                compare_with_reference(
                    "backup_single_snapshot_in_both",
                    actual_output,
                    test_dir,
                    [temp_base],
                )
        finally:
            config_path.unlink()

    def test_backup_two_snapshots_in_source_none_in_target(self):
        """Test backup operation with two snapshots in source, none in target."""
        # Expected: First snapshot sent without parent, second sent with first as parent
        # Setup: Two snapshots in source (chronological order), empty target
        # Expected result: Two btrfs send commands, second using -p flag with first as parent

        source_path, target_path = setup_backup_test_dirs(
            ["2025-08-16T10:00:00", "2025-08-16T11:00:00"], []
        )

        backup_pairs: list[dict[str, str | int]] = [
            {
                "name": "test_root",
                "source": str(source_path),
                "target": str(target_path),
            }
        ]

        config_path = create_temp_config(backup_pairs)

        try:
            with LogCapture() as log_capture:
                log_capture.set_time_func(lambda: FIXED_LOG_TIME)

                test_args = [
                    "backup_script.py",
                    "--backup",
                    "--pair=test_root",
                    "--dry-run",
                    "--verbose",
                    f"--config={config_path}",
                ]

                with patch.object(sys, "argv", test_args):
                    result = backup_script.main()

                assert result == 0
                actual_output = log_capture.get_output()
                test_dir = Path(__file__).parent
                # Normalize the temp directory path for consistent testing
                temp_base = str(source_path.parent)
                compare_with_reference(
                    "backup_two_snapshots_source_none_target",
                    actual_output,
                    test_dir,
                    [temp_base],
                )
        finally:
            config_path.unlink()

    def test_backup_three_snapshots_source_one_in_target(self):
        """Test backup operation with three snapshots in source, one in target."""
        # Expected: Two newer snapshots sent with appropriate parenting
        # Setup: Three snapshots in source, first one already in target
        # Expected result: Second snapshot sent with first as parent, third sent with second as parent

        source_path, target_path = setup_backup_test_dirs(
            [
                "2025-08-16T12:00:00-foo-bar",
                "2025-08-16T11:00:00-foo",
                "2025-08-16T10:00:00",
            ],
            ["2025-08-16T10:00:00"],
        )

        backup_pairs: list[dict[str, str | int]] = [
            {
                "name": "test_root",
                "source": str(source_path),
                "target": str(target_path),
            }
        ]

        config_path = create_temp_config(backup_pairs)

        try:
            with LogCapture() as log_capture:
                log_capture.set_time_func(lambda: FIXED_LOG_TIME)

                test_args = [
                    "backup_script.py",
                    "--backup",
                    "--pair=test_root",
                    "--dry-run",
                    "--verbose",
                    f"--config={config_path}",
                ]

                with patch.object(sys, "argv", test_args):
                    result = backup_script.main()

                assert result == 0
                actual_output = log_capture.get_output()
                test_dir = Path(__file__).parent
                # Normalize the temp directory path for consistent testing
                temp_base = str(source_path.parent)
                compare_with_reference(
                    "backup_three_snapshots_source_one_target",
                    actual_output,
                    test_dir,
                    [temp_base],
                )
        finally:
            config_path.unlink()

    def test_purge_no_snapshots_folder(self):
        """Test purge operation when snapshots folder doesn't exist."""
        # Expected: Error logged about missing snapshots folder
        # Setup: No directories created
        # Expected result: Error condition logged, operation continues gracefully

        backup_pairs: list[dict[str, str | int]] = [
            {
                "name": "test_root",
                "source": "/tmp/nonexistent/source/root",
                "target": "/tmp/nonexistent/target/root",
                "retention_days": 7,
                "retention_count": 2,
                "target_retention_days": 30,
                "target_retention_count": 5,
            }
        ]

        config_path = create_temp_config(backup_pairs)

        try:
            with LogCapture() as log_capture:
                log_capture.set_time_func(lambda: FIXED_LOG_TIME)

                test_args = [
                    "backup_script.py",
                    "--purge",
                    "--pair=test_root",
                    "--dry-run",
                    "--verbose",
                    f"--config={config_path}",
                ]

                with patch.object(sys, "argv", test_args):
                    # Should not crash, but log error
                    backup_script.main()

                actual_output = log_capture.get_output()
                test_dir = Path(__file__).parent
                compare_with_reference(
                    "purge_no_snapshots_folder", actual_output, test_dir
                )
        finally:
            config_path.unlink()

    def test_purge_no_snapshots_in_either(self):
        """Test purge operation when both source and target have no snapshots."""
        # Expected: Info logged about no snapshots found, not an error
        # Setup: Empty source and target directories
        # Expected result: Informational message, successful completion

        source_path, target_path = setup_purge_test_dirs([], [])

        backup_pairs: list[dict[str, str | int]] = [
            {
                "name": "test_root",
                "source": str(source_path),
                "target": str(target_path),
                "retention_days": 7,
                "retention_count": 2,
                "target_retention_days": 30,
                "target_retention_count": 5,
            }
        ]

        config_path = create_temp_config(backup_pairs)

        try:
            with LogCapture() as log_capture:
                log_capture.set_time_func(lambda: FIXED_LOG_TIME)

                test_args = [
                    "backup_script.py",
                    "--purge",
                    "--pair=test_root",
                    "--dry-run",
                    "--verbose",
                    f"--config={config_path}",
                ]

                with patch.object(sys, "argv", test_args):
                    result = backup_script.main()

                assert result == 0
                actual_output = log_capture.get_output()
                test_dir = Path(__file__).parent
                # Normalize the temp directory path for consistent testing
                temp_base = str(source_path.parent)
                compare_with_reference(
                    "purge_no_snapshots_in_either",
                    actual_output,
                    test_dir,
                    [temp_base],
                )
        finally:
            config_path.unlink()

    def test_purge_single_old_snapshot_protected_by_count(self):
        """Test purge operation with single old snapshot protected by retention count."""
        # Expected: Snapshot is old enough but protected by retention_count=1
        # Setup: One old snapshot in both source and target
        # Expected result: No deletion commands, snapshot protected by count

        # Create snapshots that are 30 days old (older than retention_days=7)
        old_snapshot = "2025-07-17T10:00:00-old-snapshot"
        source_path, target_path = setup_purge_test_dirs([old_snapshot], [old_snapshot])

        backup_pairs: list[dict[str, str | int]] = [
            {
                "name": "test_root",
                "source": str(source_path),
                "target": str(target_path),
                "retention_days": 7,
                "retention_count": 1,  # Protects the single snapshot
                "target_retention_days": 30,
                "target_retention_count": 1,  # Protects the single snapshot
            }
        ]

        config_path = create_temp_config(backup_pairs)

        try:
            with LogCapture() as log_capture:
                log_capture.set_time_func(lambda: FIXED_LOG_TIME)

                test_args = [
                    "backup_script.py",
                    "--purge",
                    "--pair=test_root",
                    "--dry-run",
                    "--verbose",
                    f"--config={config_path}",
                ]

                with patch.object(sys, "argv", test_args):
                    result = backup_script.main()

                assert result == 0
                actual_output = log_capture.get_output()
                test_dir = Path(__file__).parent
                # Normalize the temp directory path for consistent testing
                temp_base = str(source_path.parent)
                compare_with_reference(
                    "purge_single_old_snapshot_protected_by_count",
                    actual_output,
                    test_dir,
                    [temp_base],
                )
        finally:
            config_path.unlink()

    def test_purge_three_old_snapshots_one_removed(self):
        """Test purge operation with three old snapshots where oldest gets removed."""
        # Expected: Three old snapshots, retention_count=2 so oldest 1 gets removed
        # Setup: Three old snapshots in both source and target
        # Expected result: Oldest snapshot deleted from both source and target

        # Create snapshots that are all older than retention_days=7
        old_snapshots = [
            "2025-07-09T10:00:00-oldest",  # Will be removed
            "2025-07-10T11:00:00-middle",  # Will be kept
            "2025-07-11T12:00:00-newest",  # Will be kept
        ]
        source_path, target_path = setup_purge_test_dirs(old_snapshots, old_snapshots)

        backup_pairs: list[dict[str, str | int]] = [
            {
                "name": "test_root",
                "source": str(source_path),
                "target": str(target_path),
                "retention_days": 7,
                "retention_count": 2,  # Keep 2 newest, remove 1 oldest
                "target_retention_days": 30,
                "target_retention_count": 2,  # Keep 2 newest, remove 1 oldest
            }
        ]

        config_path = create_temp_config(backup_pairs)

        try:
            with LogCapture() as log_capture:
                log_capture.set_time_func(lambda: FIXED_LOG_TIME)

                test_args = [
                    "backup_script.py",
                    "--purge",
                    "--pair=test_root",
                    "--dry-run",
                    "--verbose",
                    f"--config={config_path}",
                ]

                with patch.object(sys, "argv", test_args):
                    result = backup_script.main()

                assert result == 0
                actual_output = log_capture.get_output()
                test_dir = Path(__file__).parent
                # Normalize the temp directory path for consistent testing
                temp_base = str(source_path.parent)
                compare_with_reference(
                    "purge_three_old_snapshots_one_removed",
                    actual_output,
                    test_dir,
                    [temp_base],
                )
        finally:
            config_path.unlink()

    def test_purge_mixed_age_snapshots_only_old_removed(self):
        """Test purge operation with mixed age snapshots where only old ones are removed."""
        # Expected: Mix of old and new snapshots, only old ones eligible for removal
        # Setup: Mix of old and recent snapshots, only old ones should be considered
        # Expected result: Only old snapshots removed, recent ones protected by age

        # Mix of old and recent snapshots
        mixed_snapshots = [
            "2025-07-01T10:00:00-very-old",  # Old, will be removed
            "2025-07-02T10:00:00-old",  # Old, will be removed
            "2025-08-15T10:00:00-recent",  # Recent, protected by age
            "2025-08-16T10:00:00-newest",  # Recent, protected by age
        ]
        source_path, target_path = setup_purge_test_dirs(
            mixed_snapshots, mixed_snapshots
        )

        backup_pairs: list[dict[str, str | int]] = [
            {
                "name": "test_root",
                "source": str(source_path),
                "target": str(target_path),
                "retention_days": 7,
                "retention_count": 1,  # Keep only 1 of the old ones
                "target_retention_days": 30,
                "target_retention_count": 1,  # Keep only 1 of the old ones
            }
        ]

        config_path = create_temp_config(backup_pairs)

        try:
            with LogCapture() as log_capture:
                log_capture.set_time_func(lambda: FIXED_LOG_TIME)

                test_args = [
                    "backup_script.py",
                    "--purge",
                    "--pair=test_root",
                    "--dry-run",
                    "--verbose",
                    f"--config={config_path}",
                ]

                with patch.object(sys, "argv", test_args):
                    result = backup_script.main()

                assert result == 0
                actual_output = log_capture.get_output()
                test_dir = Path(__file__).parent
                # Normalize the temp directory path for consistent testing
                temp_base = str(source_path.parent)
                compare_with_reference(
                    "purge_mixed_age_snapshots_only_old_removed",
                    actual_output,
                    test_dir,
                    [temp_base],
                )
        finally:
            config_path.unlink()
