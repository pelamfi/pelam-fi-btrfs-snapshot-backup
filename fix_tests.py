#!/usr/bin/env python3
"""Quick script to fix the test file by adding original_volume parameter."""

import re

# Read the file
with open("tests/test_integration.py", "r") as f:
    content = f.read()

# Pattern to match BackupPair instantiations
pattern = r'(\s+)BackupPair\(\s*\n(\s+)name="([^"]+)",\s*\n(\s+)source="([^"]+)",\s*\n(\s+)target="([^"]+)",\s*\n'


def replacement(match):
    indent = match.group(1)
    name_indent = match.group(2)
    name = match.group(3)
    source_indent = match.group(4)
    source = match.group(5)
    target_indent = match.group(6)
    target = match.group(7)

    # Generate original_volume based on the source path
    original_volume = "/tmp/test/volume"

    return f"""{indent}BackupPair(
{name_indent}name="{name}",
{name_indent}original_volume="{original_volume}",
{source_indent}source="{source}",
{target_indent}target="{target}",
"""


# Apply the replacement
new_content = re.sub(pattern, replacement, content)

# Write the file back
with open("tests/test_integration.py", "w") as f:
    f.write(new_content)

print("Fixed tests/test_integration.py")
