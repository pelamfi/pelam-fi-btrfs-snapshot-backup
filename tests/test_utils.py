"""Test utilities for reference-based testing."""

from __future__ import annotations

import logging
import tempfile
from io import StringIO
from pathlib import Path
from types import TracebackType
from typing import Any


class LogCapture:
    """Context manager to capture logging output for testing."""
    
    def __init__(self, logger_name: str | None = None, level: int = logging.DEBUG):
        self.logger_name = logger_name
        self.level = level
        self.stream = StringIO()
        self.handler = logging.StreamHandler(self.stream)
        self.handler.setLevel(level)
        self.formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        self.handler.setFormatter(self.formatter)
        
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
        exc_tb: TracebackType | None
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
name = "{pair['name']}"
source = "{pair['source']}"
target = "{pair['target']}"
retention_days = {pair.get('retention_days', 30)}
retention_count = {pair.get('retention_count', 10)}
target_retention_days = {pair.get('target_retention_days', 90)}
target_retention_count = {pair.get('target_retention_count', 20)}

"""
    
    temp_file = tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False)
    temp_file.write(config_content)
    temp_file.flush()
    
    return Path(temp_file.name)


def compare_with_reference(test_name: str, actual_output: str, test_dir: Path) -> None:
    """Compare actual output with reference file, creating it if it doesn't exist."""
    reference_file = test_dir / "references" / f"{test_name}.txt"
    
    # Create references directory if it doesn't exist
    reference_file.parent.mkdir(exist_ok=True)
    
    if not reference_file.exists():
        # Create the reference file
        reference_file.write_text(actual_output)
        print(f"Created reference file: {reference_file}")
        return
    
    # Compare with existing reference
    expected_output = reference_file.read_text()
    
    if actual_output != expected_output:
        # Write actual output for debugging
        actual_file = test_dir / "references" / f"{test_name}.actual.txt"
        actual_file.write_text(actual_output)
        
        raise AssertionError(
            f"Output differs from reference file {reference_file}\n"
            f"Actual output written to: {actual_file}\n"
            f"To update reference: mv {actual_file} {reference_file}"
        )
