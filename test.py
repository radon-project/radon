#!/usr/bin/env python3
import sys
import os
import subprocess
import json

from typing import NamedTuple

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
            json.dump({
                "code": self.code,
                "stdout": self.stdout,
                "stderr": self.stderr,
            }, f)

def run_test(test: str) -> Output:
    proc = subprocess.run([sys.executable, "radon.py", "-s", test], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return Output(proc.returncode, proc.stdout.decode("utf-8"), proc.stderr.decode("utf-8"))

def run_tests(directory="tests") -> int:
    failed_tests = []
    for test in os.listdir(directory):
        json_file = f"{directory}/{test}.json"
        if not test.endswith(".rn"): continue
        if not os.path.isfile(json_file):
            print(f"WARNING: file {json_file!r} not found, skipping...")
            print(f"NOTE: to create this file, run the `record` subcommand")
            continue

        print(f"Running test {test!r}...", end="", flush=True)
        output = run_test(f"{directory}/{test}")
        expected_output = Output.from_file(json_file)
        if output != expected_output:
            print(f"\rTest {test!r} failed!" + " "*20)
            print(f"Expected: {expected_output!r}")
            print(f"Got:      {output!r}")
            failed_tests.append(test)
        else:
            print(f"\rTest {test!r} passed!" + " "*20)

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

def record_tests(directory="tests") -> int:
    for test in os.listdir(directory):
        if not test.endswith(".rn"): continue
        print("Recording {test!r}...", end="", flush=True)
        output = run_test(f"{directory}/{test}")
        json_file = f"{directory}/{test}.json"
        output.dump(json_file)
        print(f"\rRecorded {test!r}" + " "*20)
    return 0

def usage(program_name: str, stream: any) -> None:
    print(f"""Usage: {program_name} <subcommand> [args]
SUBCOMMANDS:
    help   - Print this help message to stdout and exit successfully
    run    - Run tests
    record - Record output of tests
""", file=stream)

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
        case unknown:
            usage(program_name, sys.stderr)
            print(f"ERROR: unknown subcommand '{unknown}'", file=sys.stderr)
            return 1

if __name__ == '__main__':
    exit(main(sys.argv))
