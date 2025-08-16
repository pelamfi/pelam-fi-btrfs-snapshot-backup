"""Integration tests for main operations using reference-based testing."""

from __future__ import annotations

import sys
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
