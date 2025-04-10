#!/usr/bin/env python3

import json
import os
import subprocess
import sys
from difflib import unified_diff  # Rule 34 of Python: If it exists, it's in the standard library
from typing import IO, NamedTuple


class Output(NamedTuple):
    code: int
    # TODO: handle non-UTF-8 output
    stdout: str
    stderr: str

    @classmethod
    def from_file(cls, path: str) -> "Output":
        with open(path, "r") as f:
            d = json.load(f)
        return cls(**d)

    def dump(self, path: str) -> None:
        with open(path, "w") as f:
            json.dump({"code": self.code, "stdout": self.stdout, "stderr": self.stderr}, f)


def run_test(test: str) -> Output:
    proc = subprocess.run(
        [sys.executable, "radon.py", "-s", test, "-A"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    # Normalize path separators in output to forward slashes
    stdout = proc.stdout.decode("utf-8").replace("\r\n", "\n")
    stderr = proc.stderr.decode("utf-8").replace("\r\n", "\n")

    # Replace Windows-style paths with Unix-style paths for consistent comparison
    if os.name == "nt":  # Windows
        stdout = stdout.replace("\\", "/")
        stderr = stderr.replace("\\", "/")

    return Output(proc.returncode, stdout, stderr)


def run_tests_rec(tests: str, failed_tests: list[str]) -> None:
    if os.path.isdir(tests):
        for test in os.listdir(tests):
            run_tests_rec(os.path.join(tests, test), failed_tests)
    elif os.path.isfile(tests):
        json_file = f"{tests}.json"
        if not tests.endswith(".rn"):
            return
        if not os.path.isfile(json_file):
            print(f"WARNING: file {json_file!r} not found, skipping...")
            print("NOTE: to create this file, run the `record` subcommand")
            return

        print(f"Running test {tests!r}...", end="", flush=True)
        output = run_test(tests)
        expected_output = Output.from_file(json_file)

        if output != expected_output:
            print(f"\rTest {tests!r} failed!" + " " * 20)
            print(f"Expected: {expected_output!r}")
            print(f"Got:      {output!r}")
            print(f"NOTE: run `{sys.argv[0]} diff {tests}` for more information")
            failed_tests.append(tests)
        else:
            print(f"\rTest {tests!r} passed!" + " " * 20)
    else:
        assert False, "unreachable"


def run_tests(tests: str = "tests") -> int:
    failed_tests: list[str] = []
    run_tests_rec(tests, failed_tests)

    print()
    print("TEST SUMMARY:")
    if len(failed_tests) == 0:
        print("All tests passed!")
        return 0
    else:
        print(f"{len(failed_tests)} tests failed:")
        for test in failed_tests:
            print(f"    {test!r}")
        return 1


def record_tests(tests: str = "tests") -> int:
    if os.path.isdir(tests):
        for test in os.listdir(tests):
            ret = record_tests(os.path.join(tests, test))
            if ret != 0:
                return ret
        return 0
    elif os.path.isfile(tests):
        if not tests.endswith(".rn"):
            return 0
        print(f"Recording {tests!r}...", end="", flush=True)
        output = run_test(tests)
        cwd = os.getcwd().replace("\\", "/")

        # Check if normalized path is in output
        if cwd in (output.stdout + output.stderr):
            print(f"\nERROR: test {tests!r} accidentally depends on current directory")
            return 1

        json_file = f"{tests}.json"
        output.dump(json_file)
        print(f"\rRecorded {tests!r}" + " " * 20)
        return 0
    else:
        assert False, "Unreachable"


def usage(program_name: str, stream: IO[str]) -> None:
    print(
        f"""Usage: {program_name} <subcommand> [args]
SUBCOMMANDS:
    help           - Print this help message to stdout and exit successfully
    run [tests]    - Run tests in directory [tests] (default: "tests/"). Can also be used to run only a single test
    record [tests] - Record output of tests in directory [tests] (default: "tests/"). Can also be used to record only a single test
    diff <test.rn> - Show diff between expected and actual output
    full           - Same as `{program_name} run` + `make lint`
""",
        file=stream,
    )


def main(argv: list[str]) -> int:
    program_name = argv.pop(0)
    if len(argv) == 0:
        usage(program_name, sys.stderr)
        print("ERROR: no subcommand provided", file=sys.stderr)
        return 1

    subcommand = argv.pop(0)
    match subcommand:
        case "help":
            usage(program_name, sys.stdout)
            return 0

        case "run":
            if len(argv) > 0:
                tests_to_run = argv.pop(0)
            else:
                tests_to_run = "tests"
            return run_tests(tests_to_run)

        case "record":
            if len(argv) > 0:
                tests_to_record = argv.pop(0)
            else:
                tests_to_record = "tests"
            return record_tests(tests_to_record)

        case "full":
            env = dict(**os.environ, FORCE_COLOR="1")
            ruff_format = subprocess.Popen(
                ["ruff", "format", "--check", "."], stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env
            )
            ruff_check = subprocess.Popen(
                ["ruff", "check", "."], stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env
            )
            mypy = subprocess.Popen(
                ["mypy", ".", "--strict"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=dict(**os.environ, MYPY_FORCE_COLOR="1"),
            )

            test_returncode = run_tests("tests")

            print("----------------------")
            print("    mypy . --strict   ")
            print("----------------------")

            mypy_ret = mypy.wait()

            assert mypy.stdout is not None
            assert mypy.stderr is not None

            sys.stdout.buffer.write(mypy.stdout.read())
            sys.stderr.buffer.write(mypy.stderr.read())

            print("---------------------")
            print("ruff format --check .")
            print("---------------------")

            format_ret = ruff_format.wait()
            check_ret = ruff_check.wait()

            assert ruff_format.stdout is not None and ruff_format.stderr is not None

            sys.stdout.buffer.write(ruff_format.stdout.read())
            sys.stderr.buffer.write(ruff_format.stderr.read())

            print("---------------------")
            print("     ruff check .    ")
            print("---------------------")

            assert ruff_check.stdout is not None and ruff_check.stderr is not None

            sys.stdout.buffer.write(ruff_check.stdout.read())
            sys.stderr.buffer.write(ruff_check.stderr.read())

            if test_returncode == 0 and format_ret == 0 and check_ret == 0 and mypy_ret == 0:
                print("Full test succeeded with no errors!")
                return 0
            else:
                if format_ret != 0:
                    print("ERROR: ruff format failed", file=sys.stderr)
                if check_ret != 0:
                    print("ERROR: ruff check failed", file=sys.stderr)
                if mypy_ret != 0:
                    print("ERROR: mypy failed", file=sys.stderr)
                return 1

        case "diff":
            if len(argv) < 1:
                usage(program_name, sys.stderr)
                print("ERROR: no test to diff provided", file=sys.stderr)
                return 1
            test = argv.pop(0)
            try:
                actual_output = run_test(f"{test}")
            except FileNotFoundError:
                print(f"ERROR: test {test!r} not found", file=sys.stderr)
                return 1
            try:
                expected_output = Output.from_file(f"{test}.json")
            except FileNotFoundError:
                print(f"ERROR: test {test!r} has no expected output", file=sys.stderr)
                return 1
            if actual_output == expected_output:
                print(f"Test {test!r} passes!")
                return 0

            print("STDOUT DIFF")
            print("-----------")
            print(
                "\n".join(
                    unified_diff(
                        expected_output.stdout.splitlines(), actual_output.stdout.splitlines(), "expected", "actual"
                    )
                )
            )
            print()
            print("STDERR DIFF")
            print("-----------")
            print("\n".join(unified_diff(expected_output.stderr.splitlines(), actual_output.stderr.splitlines())))
            return 0

        case unknown:
            usage(program_name, sys.stderr)
            print(f"ERROR: unknown subcommand '{unknown}'", file=sys.stderr)
            return 1


if __name__ == "__main__":
    exit(main(sys.argv[:]))
