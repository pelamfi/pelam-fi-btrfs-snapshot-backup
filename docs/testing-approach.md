# Testing Approach

## Reference-Based Integration Testing
The project uses a reference-based testing approach that captures the complete dry-run output of operations and compares it against stored reference files. This approach provides:

- **Complete integration testing** - Tests the full command-line interface and logging output
- **Deterministic results** - Fixed timestamps ensure consistent test output  
- **Easy verification** - Human-readable reference files show exactly what the tool does in each test scenario
- **Simple maintenance** - Reference files can be updated when behavior changes intentionally

## How Reference Testing Works

1. **Test setup**: Creates temporary configuration pointing to test directories
2. **Execution**: Runs the main program with `--dry-run --verbose` options
3. **Capture**: Logs all output including the exact commands that would be executed
4. **Compare**: Diffs the captured output against a stored reference file
5. **Auto-create**: If no reference exists, creates it automatically for review

## Test Structure

```bash
tests/
├── test_integration.py     # Reference-based integration tests
├── test_config.py         # Unit tests for configuration parsing
├── test_utils.py          # Testing utilities and log capture
└── references/           # Reference files (git-tracked)
    ├── snapshot_single_pair.txt
    ├── snapshot_all_pairs.txt
    └── *.actual.txt      # Generated on failures (git-ignored)
```

## Running and Updating Tests

```bash
# Run all tests, linting etc
./build.sh

# Run all tests
uv run pytest tests/ -v

# Run specific integration test
uv run pytest tests/test_integration.py::TestMainOperations::test_snapshot_operation_single_pair -v

# To update test references run interactively
./update-test-references.sh

# Or simply update immediately
./update-test-references.sh -y

```

This testing approach ensures that any changes to command generation, logging format, or program behavior are immediately visible and must be explicitly approved by updating the reference files.
