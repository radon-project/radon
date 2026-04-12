# Copilot Instructions

## Testing

1. For tests, use `assert` statements, not `print` statements.
2. After every coding session, always run the test suite before ending your work.
3. Validate that tests are 100% passing before submitting changes.
4. Do not ask for human review unless all tests pass.

## How To Run Tests

### Basic Test Commands
1. Run all tests with: `python .\test.py run`
2. Run a specific test file with: `python .\test.py run .\tests\lang\raise.rn`
3. Record test output for a test file with: `python .\test.py record .\tests\lang\raise.rn`
4. Record all tests with: `python .\test.py record`
5. Show diff between expected and actual output with: `python .\test.py diff .\tests\lang\raise.rn`
6. Get help on test subcommands with: `python .\test.py help`

### Full Test Suite with Checks
1. Run tests + mypy (strict) + ruff checks with: `python .\test.py full`

## Linting and Type Checking

### Direct Commands
1. Run mypy type checks with: `mypy .`
2. Run mypy with strict mode: `mypy --strict .`
3. Run ruff code checks with: `ruff check .`
4. Fix ruff issues automatically with: `ruff check --fix .`
5. Run ruff format checks with: `ruff format --check .`
6. Format code with ruff (fix formatting issues): `ruff format .`
7. Format and organize imports with isort: `isort .`
8. Run all checks (mypy + ruff) with: `mypy . && ruff check .`
9. Run all checks and fixes with: `mypy . && ruff check --fix .`

### Using Make Targets (Convenience)
1. Format code with: `make format`
2. Run lint checks (format + style) with: `make lint`
3. Run type checks with: `make typecheck`
4. Run full test suite with: `make test`
5. Record tests with: `make test-record`
6. Show test diff with: `make test-diff [FILE]`
