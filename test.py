#!/usr/bin/python3.12

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
        [sys.executable, "radon.py", "-s", test, "-aall"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    return Output(
        proc.returncode,
        proc.stdout.decode("utf-8").replace("\r\n", "\n"),
        proc.stderr.decode("utf-8").replace("\r\n", "\n"),
    )


def run_tests(directory: str = "tests") -> int:
    mypy = subprocess.Popen(
        ["mypy", ".", "--strict"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=dict(**os.environ, MYPY_FORCE_COLOR="1"),
    )

    failed_tests: list[str] = []
    for test in os.listdir(directory):
        json_file = f"{directory}/{test}.json"
        if not test.endswith(".rn"):
            continue
        if not os.path.isfile(json_file):
            print(f"WARNING: file {json_file!r} not found, skipping...")
            print("NOTE: to create this file, run the `record` subcommand")
            continue

        print(f"Running test {test!r}...", end="", flush=True)
        output = run_test(f"{directory}/{test}")
        expected_output = Output.from_file(json_file)
        if output != expected_output:
            print(f"\rTest {test!r} failed!" + " " * 20)
            print(f"Expected: {expected_output!r}")
            print(f"Got:      {output!r}")
            failed_tests.append(test)
        else:
            print(f"\rTest {test!r} passed!" + " " * 20)

    print()
    print("TEST SUMMARY:")
    if len(failed_tests) == 0:
        print("All tests passed!")
    else:
        print(f"{len(failed_tests)} tests failed:")
        for test in failed_tests:
            print(f"    {test!r}")

    print("--------------")
    print("    mypy .    ")
    print("--------------")
    mypy.wait()
    assert mypy.stdout is not None
    assert mypy.stderr is not None
    sys.stdout.buffer.write(mypy.stdout.read())
    sys.stderr.buffer.write(mypy.stderr.read())

    if mypy.returncode == 0 and len(failed_tests) == 0:
        return 0
    else:
        return 1


def record_tests(directory: str = "tests") -> int:
    for test in os.listdir(directory):
        if not test.endswith(".rn"):
            continue
        print(f"Recording {test!r}...", end="", flush=True)
        output = run_test(f"{directory}/{test}")
        if os.getcwd() in (output.stdout + output.stderr):
            print(f"\nERROR: test {test!r} accidentally depends on current directory")
            return 1
        json_file = f"{directory}/{test}.json"
        output.dump(json_file)
        print(f"\rRecorded {test!r}" + " " * 20)
    return 0


def usage(program_name: str, stream: IO[str]) -> None:
    print(
        f"""Usage: {program_name} <subcommand> [args]
SUBCOMMANDS:
    help           - Print this help message to stdout and exit successfully
    run            - Run tests
    record         - Record output of tests
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
            return run_tests()
        case "record":
            return record_tests()
        case "full":
            env = dict(**os.environ, FORCE_COLOR="1")
            ruff_format = subprocess.Popen(
                ["ruff", "format", "--check", "."], stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env
            )
            ruff_check = subprocess.Popen(
                ["ruff", "check", "."], stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env
            )

            test_returncode = run_tests()

            format_ret = ruff_format.wait()
            check_ret = ruff_check.wait()

            print("---------------------")
            print("ruff format --check .")
            print("---------------------")
            assert ruff_format.stdout is not None and ruff_format.stderr is not None
            sys.stdout.buffer.write(ruff_format.stdout.read())
            sys.stderr.buffer.write(ruff_format.stderr.read())
            print("---------------------")
            print("     ruff check .    ")
            print("---------------------")
            assert ruff_check.stdout is not None and ruff_check.stderr is not None
            sys.stdout.buffer.write(ruff_check.stdout.read())
            sys.stderr.buffer.write(ruff_check.stderr.read())

            if test_returncode == 0 and format_ret == 0 and check_ret == 0:
                print("Full test succeeded with no errors!")
                return 0
            else:
                if format_ret != 0:
                    print("ERROR: ruff format failed", file=sys.stderr)
                if check_ret != 0:
                    print("ERROR: ruff check failed", file=sys.stderr)
                return 1
        case "diff":
            if len(argv) < 1:
                usage(program_name, sys.stderr)
                print("ERROR: no test to diff provided", file=sys.stderr)
                return 1
            test = argv.pop(0)
            try:
                actual_output = run_test(f"tests/{test}")
            except FileNotFoundError:
                print(f"ERROR: test {test!r} not found", file=sys.stderr)
                return 1
            try:
                expected_output = Output.from_file(f"tests/{test}.json")
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
    exit(main(sys.argv))
