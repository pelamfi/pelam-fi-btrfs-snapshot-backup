"""Test utilities for reference-based testing."""

from __future__ import annotations

import logging
import re
import tempfile
import time
from collections.abc import Callable
from io import StringIO
from pathlib import Path
from types import TracebackType
from typing import Any, Literal


class MockableFormatter(logging.Formatter):
    """A logging formatter that allows mocking the time function.

    This is useful for deterministic tests.
    """

    def __init__(
        self,
        fmt: str | None = None,
        datefmt: str | None = None,
        style: Literal["%", "{", "$"] = "%",
        validate: bool = True,
        *,
        defaults: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(fmt, datefmt, style, validate, defaults=defaults)
        # Use a mockable time function
        self._time_func: Callable[[], float] = time.time

    def formatTime(self, record: logging.LogRecord, datefmt: str | None = None) -> str:
        """Format the time using our mockable time function."""
        ct = self.converter(self._time_func())
        if datefmt:
            s = time.strftime(datefmt, ct)
        else:
            s = time.strftime(self.default_time_format, ct)
            if self.default_msec_format:
                s = self.default_msec_format % (s, record.msecs)
        return s

    def set_time_func(self, time_func: Callable[[], float]) -> None:
        """Set a custom time function (useful for testing)."""
        self._time_func = time_func


class LogCapture:
    """Context manager to capture logging output for testing."""

    def __init__(self, logger_name: str | None = None, level: int = logging.DEBUG):
        self.logger_name = logger_name
        self.level = level
        self.stream = StringIO()
        self.handler = logging.StreamHandler(self.stream)
        self.handler.setLevel(level)
        self.formatter = MockableFormatter(
            "%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
        self.handler.setFormatter(self.formatter)

    def set_time_func(self, time_func: Callable[[], float]) -> None:
        """Set a custom time function for deterministic timestamps."""
        self.formatter.set_time_func(time_func)

    def __enter__(self) -> LogCapture:
        if self.logger_name:
            self.logger = logging.getLogger(self.logger_name)
        else:
            self.logger = logging.getLogger()

        # Store original settings
        self.original_level = self.logger.level
        self.original_handlers = self.logger.handlers[:]

        # Configure for capture
        self.logger.setLevel(self.level)
        self.logger.handlers.clear()
        self.logger.addHandler(self.handler)

        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        # Restore original settings
        self.logger.handlers.clear()
        self.logger.handlers.extend(self.original_handlers)
        self.logger.setLevel(self.original_level)

    def get_output(self) -> str:
        """Get the captured log output."""
        return self.stream.getvalue()


def create_temp_config(backup_pairs: list[dict[str, Any]]) -> Path:
    """Create a temporary configuration file."""
    config_content = "[global]\ndefault_verbose = false\ndry_run = false\n\n"

    for pair in backup_pairs:
        config_content += f"""[[backup_pairs]]
name = "{pair["name"]}"
source = "{pair["source"]}"
target = "{pair["target"]}"
retention_days = {pair.get("retention_days", 30)}
retention_count = {pair.get("retention_count", 10)}
target_retention_days = {pair.get("target_retention_days", 90)}
target_retention_count = {pair.get("target_retention_count", 20)}

"""

    temp_file = tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False)
    temp_file.write(config_content)
    temp_file.flush()

    return Path(temp_file.name)


def normalize_temp_paths(output: str, temp_base_paths: list[str]) -> str:
    """Replace temporary directory paths in output with normalized placeholders.

    Args:
        output: The raw output string
        temp_base_paths: List of temporary base paths to normalize (e.g., ["/tmp/tmpXXXXXX"])

    Returns:
        Output with temp paths replaced by [TEMP_FOLDER]
    """

    normalized = output
    for temp_path in temp_base_paths:
        # Replace the temp path with placeholder
        # Use re.escape to handle any special regex characters in the path
        pattern = re.escape(temp_path)
        normalized = re.sub(pattern, "[TEMP_FOLDER]", normalized)

    return normalized


def compare_with_reference(
    test_name: str,
    actual_output: str,
    test_dir: Path,
    temp_paths_to_normalize: list[str] | None = None,
) -> None:
    """Compare actual output with reference file, creating it if it doesn't exist.

    Args:
        test_name: Name of the test for the reference file
        actual_output: The actual output to compare
        test_dir: Directory containing the references folder
        temp_paths_to_normalize: Optional list of temporary paths to replace with [TEMP_FOLDER]
    """
    reference_file = test_dir / "references" / f"{test_name}.txt"

    # Create references directory if it doesn't exist
    reference_file.parent.mkdir(exist_ok=True)

    # Normalize temporary paths if provided
    normalized_output = actual_output
    if temp_paths_to_normalize:
        normalized_output = normalize_temp_paths(actual_output, temp_paths_to_normalize)

    if not reference_file.exists():
        # Create the reference file with normalized output
        reference_file.write_text(normalized_output)
        print(f"Created reference file: {reference_file}")
        return

    # Compare with existing reference
    expected_output = reference_file.read_text()

    if normalized_output != expected_output:
        # Write actual output for debugging (normalized)
        actual_file = test_dir / "references" / f"{test_name}.actual.txt"
        actual_file.write_text(normalized_output)

        raise AssertionError(
            f"Output differs from reference file {reference_file}\n"
            f"Actual output written to: {actual_file}\n"
            f"To update reference: mv {actual_file} {reference_file}"
        )
