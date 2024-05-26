#!/usr/bin/python3.12
# By: Md. Almas Ali

import sys
import os
from typing import IO

try:
    import readline

    # Enable arrow key support
    readline.parse_and_bind(r'"\e[A": history-search-backward')
    readline.parse_and_bind(r'"\e[B": history-search-forward')
    readline.parse_and_bind(r'"\e[C": forward-char')
    readline.parse_and_bind(r'"\e[D": backward-char')
except ImportError:
    pass

import core as base_core
from core.parser import Context
from core.lexer import Position


def shell() -> None:
    print(f"Radon {base_core.__version__}\nType to exit()")
    brace_count = 0

    while True:
        try:
            text = input(">>> ")
            if text.strip() == "":
                continue

            if text.strip()[-1] == "{":
                brace_count += 1
                while True:
                    text += "\n" + input("... ")
                    if text.strip()[-1] == "{":
                        brace_count += 1
                    elif text.strip()[-1] == "}" or text.strip()[0] == "}":
                        brace_count -= 1

                    if brace_count == 0:
                        break

            (result, error, should_exit) = base_core.run("<stdin>", text)

            if error:
                print(error.as_string())
            else:
                if result:
                    if len(result) == 1:
                        result = result[0]
                    print(repr(result))

            if should_exit:
                break
        except KeyboardInterrupt:
            print("KeyboardInterrupt")


def usage(program_name: str, stream: IO[str]) -> None:
    print(
        f"Usage: {program_name} [--source | -s] [--command | -c] [source_file] [--version | -v] [--help | -h]",
        file=stream,
    )
    print(
        """
Options and arguments:
    --source | -s    Run a source file
    --command | -c   Run a command
    --version | -v   Print the version
    --help | -h      Print this help message

    If no arguments are provided, the program will run in shell mode.

Example:
    radon --source source_file.rn
    radon --command 'print("Hello, World!")'
    radon --version
    radon --help

The Radon Programming Language.
        """
    )


def main(argv: list[str]) -> None:
    program_name = argv.pop(0)
    source_file = None
    command = None
    while len(argv) > 0:
        arg = argv.pop(0)
        match arg:
            case "--help" | "-h":
                usage(program_name, sys.stdout)
                exit(0)
            case "--source" | "-s":
                if len(argv) == 0:
                    usage(program_name, sys.stderr)
                    print(f"ERROR: {arg} requires an argument", file=sys.stderr)
                    exit(1)
                source_file = argv[0]
                break  # allow program to use remaining args
            case "--version" | "-v":
                print(base_core.__version__)
                exit(0)
            case "--command" | "-c":
                if len(argv) == 0:
                    usage(program_name, sys.stderr)
                    print(f"ERROR: {arg} requires an argument", file=sys.stderr)
                    exit(1)
                command = argv[0]
                break  # allow program to use remaining args
            case _:
                usage(program_name, sys.stderr)
                print(f"ERROR: Unknown argument '{arg}'", file=sys.stderr)
                exit(1)

    pos = Position(0, 0, 0, "<argv>", "<argv>")
    base_core.global_symbol_table.set("argv", base_core.radonify(argv, pos, pos, Context("<global>")))
    if source_file is not None:
        head, tail = os.path.split(source_file)
        os.chdir(head)
        with open(tail, "r") as f:
            source = f.read()
        (result, error, should_exit) = base_core.run(source_file, source)

        if error:
            print(error.as_string())
            exit(1)

        if should_exit:
            exit()

    elif command is not None:
        (result, error, should_exit) = base_core.run("<cli>", command)

        if error:
            print(error.as_string())

    else:
        shell()


if __name__ == "__main__":
    main(sys.argv)
