"""Snapshot utilities for BTRFS backup tool."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class Snapshot:
    """Represents a BTRFS snapshot with parsed metadata."""

    name: str
    timestamp: datetime
    suffix: str | None = None

    @classmethod
    def from_name(cls, name: str) -> Snapshot | None:
        """Parse a snapshot name into a Snapshot object.

        Supports both formats:
        - YYYY-MM-DDTHH:MM:SS or YYYY-MM-DDTHH:MM:SS-suffix
        - YYYY-MM-DD or YYYY-MM-DD-suffix (legacy format)

        Returns None if the name doesn't match expected patterns.
        """
        # Pattern for snapshot names: YYYY-MM-DDTHH:MM:SS or YYYY-MM-DD
        snapshot_pattern = re.compile(r"^(\d{4}-\d{2}-\d{2}(?:T\d{2}:\d{2}:\d{2})?)(?:-(.+))?$")

        match = snapshot_pattern.match(name)
        if not match:
            return None

        timestamp_str, suffix = match.groups()

        try:
            # Try to parse as full timestamp first
            if "T" in timestamp_str:
                timestamp = datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%S")
            else:
                # Legacy format - treat as midnight
                timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d")
        except ValueError:
            return None

        return cls(name=name, timestamp=timestamp, suffix=suffix)

    def __lt__(self, other: Snapshot) -> bool:
        """Enable sorting by timestamp."""
        return self.timestamp < other.timestamp

    def __eq__(self, other: object) -> bool:
        """Enable equality comparison by name."""
        if not isinstance(other, Snapshot):
            return NotImplemented
        return self.name == other.name

    def __hash__(self) -> int:
        """Enable use in sets and as dict keys."""
        return hash(self.name)


def scan_snapshots(directory: str | Path) -> list[Snapshot]:
    """Scan a directory for BTRFS snapshots and return them sorted by timestamp.

    Returns a list of Snapshot objects sorted chronologically.
    Only includes directories that match the timestamp pattern.
    """
    logger = logging.getLogger(__name__)

    try:
        directory = Path(directory)
        if not directory.exists():
            return []

        snapshots: list[Snapshot] = []
        for item in directory.iterdir():
            if item.is_dir():
                snapshot = Snapshot.from_name(item.name)
                if snapshot is not None:
                    snapshots.append(snapshot)

        # Sort snapshots chronologically by timestamp
        return sorted(snapshots)

    except Exception as e:
        logger.warning(f"Error scanning snapshots in {directory}: {e}")
        return []


def get_snapshot_names(snapshots: list[Snapshot]) -> list[str]:
    """Extract snapshot names from a list of Snapshot objects."""
    return [snapshot.name for snapshot in snapshots]
