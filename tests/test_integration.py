"""Integration tests for main operations using reference-based testing."""

from src.config import BackupPair
from tests.test_utils import run_integration_test, setup_test_dirs


class TestMainOperations:
    """Test main operations using dry-run output and reference files."""

    def test_snapshot_operation_single_pair(self):
        backup_pairs = [
            BackupPair(
                name="test_root",
                source="/tmp/test/source/root",
                target="/tmp/test/target/root",
                retention_days=30,
                retention_count=10,
                target_retention_days=90,
                target_retention_count=20,
            )
        ]

        run_integration_test(
            "snapshot_single_pair",
            backup_pairs,
            "snapshot",
            "test_root",
            "test-snapshot",
        )

    def test_snapshot_operation_all_pairs(self):
        backup_pairs = [
            BackupPair(
                name="test_root",
                source="/tmp/test/source/root",
                target="/tmp/test/target/root",
                retention_days=30,
                retention_count=10,
                target_retention_days=90,
                target_retention_count=20,
            ),
            BackupPair(
                name="test_home",
                source="/tmp/test/source/home",
                target="/tmp/test/target/home",
                retention_days=14,
                retention_count=15,
                target_retention_days=90,
                target_retention_count=20,
            ),
        ]

        run_integration_test(
            "snapshot_all_pairs",
            backup_pairs,
            "snapshot",
            "all",
            "weekly-backup",
        )

    def test_backup_no_snapshots_folder(self):
        backup_pairs = [
            BackupPair(
                name="test_root",
                source="/tmp/nonexistent/source/root",
                target="/tmp/nonexistent/target/root",
                retention_days=30,
                retention_count=10,
                target_retention_days=90,
                target_retention_count=20,
            )
        ]

        run_integration_test(
            "backup_no_snapshots_folder",
            backup_pairs,
            "backup",
            expected_result=None,  # Don't check return code for error cases
        )

    def test_backup_no_snapshots_in_either(self):
        source_path, target_path = setup_test_dirs([], [])

        backup_pairs = [
            BackupPair(
                name="test_root",
                source=str(source_path),
                target=str(target_path),
                retention_days=30,
                retention_count=10,
                target_retention_days=90,
                target_retention_count=20,
            )
        ]

        run_integration_test(
            "backup_no_snapshots_in_either",
            backup_pairs,
            "backup",
            temp_paths_to_normalize=[str(source_path.parent)],
        )

    def test_backup_single_snapshot_in_source_none_in_target(self):
        source_path, target_path = setup_test_dirs(["2025-08-16T10:00:00"], [])

        backup_pairs = [
            BackupPair(
                name="test_root",
                source=str(source_path),
                target=str(target_path),
                retention_days=30,
                retention_count=10,
                target_retention_days=90,
                target_retention_count=20,
            )
        ]

        run_integration_test(
            "backup_single_snapshot_source_none_target",
            backup_pairs,
            "backup",
            temp_paths_to_normalize=[str(source_path.parent)],
        )

    def test_backup_single_snapshot_in_both(self):
        source_path, target_path = setup_test_dirs(["2025-08-16T10:00:00"], ["2025-08-16T10:00:00"])

        backup_pairs = [
            BackupPair(
                name="test_root",
                source=str(source_path),
                target=str(target_path),
                retention_days=30,
                retention_count=10,
                target_retention_days=90,
                target_retention_count=20,
            )
        ]

        run_integration_test(
            "backup_single_snapshot_in_both",
            backup_pairs,
            "backup",
            temp_paths_to_normalize=[str(source_path.parent)],
        )

    def test_backup_two_snapshots_in_source_none_in_target(self):
        source_path, target_path = setup_test_dirs(["2025-08-16T10:00:00", "2025-08-16T11:00:00"], [])

        backup_pairs = [
            BackupPair(
                name="test_root",
                source=str(source_path),
                target=str(target_path),
                retention_days=30,
                retention_count=10,
                target_retention_days=90,
                target_retention_count=20,
            )
        ]

        run_integration_test(
            "backup_two_snapshots_source_none_target",
            backup_pairs,
            "backup",
            temp_paths_to_normalize=[str(source_path.parent)],
        )

    def test_backup_three_snapshots_source_one_in_target(self):
        source_path, target_path = setup_test_dirs(
            [
                "2025-08-16T12:00:00-foo-bar",
                "2025-08-16T11:00:00-foo",
                "2025-08-16T10:00:00",
            ],
            ["2025-08-16T10:00:00"],
        )

        backup_pairs = [
            BackupPair(
                name="test_root",
                source=str(source_path),
                target=str(target_path),
                retention_days=30,
                retention_count=10,
                target_retention_days=90,
                target_retention_count=20,
            )
        ]

        run_integration_test(
            "backup_three_snapshots_source_one_target",
            backup_pairs,
            "backup",
            temp_paths_to_normalize=[str(source_path.parent)],
        )

    def test_purge_no_snapshots_folder(self):
        backup_pairs = [
            BackupPair(
                name="test_root",
                source="/tmp/nonexistent/source/root",
                target="/tmp/nonexistent/target/root",
                retention_days=7,
                retention_count=2,
                target_retention_days=30,
                target_retention_count=5,
            )
        ]

        run_integration_test(
            "purge_no_snapshots_folder",
            backup_pairs,
            "purge",
            expected_result=None,
        )

    def test_purge_no_snapshots_in_either(self):
        source_path, target_path = setup_test_dirs([], [])

        backup_pairs = [
            BackupPair(
                name="test_root",
                source=str(source_path),
                target=str(target_path),
                retention_days=7,
                retention_count=2,
                target_retention_days=30,
                target_retention_count=5,
            )
        ]

        run_integration_test(
            "purge_no_snapshots_in_either",
            backup_pairs,
            "purge",
            temp_paths_to_normalize=[str(source_path.parent)],
        )

    def test_purge_single_old_snapshot_protected_by_count(self):
        old_snapshot = "2025-07-17T10:00:00-old-snapshot"
        source_path, target_path = setup_test_dirs([old_snapshot], [old_snapshot])

        backup_pairs = [
            BackupPair(
                name="test_root",
                source=str(source_path),
                target=str(target_path),
                retention_days=7,
                retention_count=1,
                target_retention_days=30,
                target_retention_count=1,
            )
        ]

        run_integration_test(
            "purge_single_old_snapshot_protected_by_count",
            backup_pairs,
            "purge",
            temp_paths_to_normalize=[str(source_path.parent)],
        )

    def test_purge_three_old_snapshots_one_removed(self):
        old_snapshots = [
            "2025-07-09T10:00:00-oldest",
            "2025-07-10T11:00:00-middle",
            "2025-07-11T12:00:00-newest",
        ]
        source_path, target_path = setup_test_dirs(old_snapshots, old_snapshots)

        backup_pairs = [
            BackupPair(
                name="test_root",
                source=str(source_path),
                target=str(target_path),
                retention_days=7,
                retention_count=2,
                target_retention_days=30,
                target_retention_count=2,
            )
        ]

        run_integration_test(
            "purge_three_old_snapshots_one_removed",
            backup_pairs,
            "purge",
            temp_paths_to_normalize=[str(source_path.parent)],
        )

    def test_purge_mixed_age_snapshots_only_old_removed(self):
        mixed_snapshots = [
            "2025-07-01T10:00:00-very-old",
            "2025-07-02T10:00:00-old",
            "2025-08-15T10:00:00-recent",
            "2025-08-16T10:00:00-newest",
        ]
        source_path, target_path = setup_test_dirs(mixed_snapshots, mixed_snapshots)

        backup_pairs = [
            BackupPair(
                name="test_root",
                source=str(source_path),
                target=str(target_path),
                retention_days=7,
                retention_count=1,
                target_retention_days=30,
                target_retention_count=1,
            )
        ]

        run_integration_test(
            "purge_mixed_age_snapshots_only_old_removed",
            backup_pairs,
            "purge",
            temp_paths_to_normalize=[str(source_path.parent)],
        )
