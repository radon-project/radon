#!/usr/bin/python3.12
# By: Md. Almas Ali

import os
import platform
import sys
from typing import IO, Optional

from core.datatypes import Value
from core.errors import Error, RTError

try:
    import readline

    # Enable arrow key support
    readline.parse_and_bind(r'"\e[A": history-search-backward')  # type: ignore
    readline.parse_and_bind(r'"\e[B": history-search-forward')  # type: ignore
    readline.parse_and_bind(r'"\e[C": forward-char')  # type: ignore
    readline.parse_and_bind(r'"\e[D": backward-char')  # type: ignore
except ImportError:
    pass

import core as base_core
from core.colortools import Log
from core.parser import Context
from core.tokens import Position

documentation_link = "https://radon-project.github.io/docs/"


def start_text() -> None:
    print(
        f"\033[1;34mRadon {base_core.__version__} on {platform.machine()} {platform.system()} ({sys.platform})\033[0m"
    )
    print(f"\033[1;33mDocumentation:\033[0m {documentation_link}")
    print("\033[1;32mType \033[1;31mhelp(obj), copyright(), credits(), license()\033[1;32m for more info\033[0m")
    print("\033[1;32mType \033[1;31mexit\033[1;32m to quit the shell.\033[0m")


def shell() -> None:
    start_text()
    brace_count = 0

    while True:
        try:
            text = input(">>> ")
            if text.strip() == "":
                continue

            if text.strip() == "exit":
                break

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

            result: list[Optional[Value]]
            error: Error | RTError | None
            should_exit: Optional[bool]
            (result, error, should_exit) = base_core.run("<stdin>", text, import_cwd=os.getcwd())  # type: ignore

            if error:
                print(error.as_string())
            else:
                if result:
                    if len(result) == 1:
                        # result = result[0]
                        print(repr(result[0]))
                    else:
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

Permission Modes (for testing purposes only):
    --allow-all | -A     Allow all permissions (disk, Python API, and network access)
    --allow-disk | -D    Allow disk access
    --allow-py | -P      Allow Python API access
    --allow-network | -W Allow network access

Example:
    radon --source source_file.rn
    radon --command 'print("Hello, World!")'
    radon --version
    radon --help

The Radon Programming Language. \
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
                source_file = argv.pop(0)
            case "--version" | "-v":
                print(base_core.__version__)
                exit(0)
            case "--command" | "-c":
                if len(argv) == 0:
                    usage(program_name, sys.stderr)
                    print(f"ERROR: {arg} requires an argument", file=sys.stderr)
                    exit(1)
                command = argv.pop(0)
            # These flags starting with --allow should only be used for testing, and not be allowed to be set by a user
            case "--allow-all" | "-A":
                base_core.security.allow_all_permissions()
            case "--allow-disk" | "-D":
                base_core.security.allowed["disk_access"] = True
            case "--allow-py" | "-P":
                base_core.security.allowed["pyapi_access"] = True
            case "--allow-network" | "-W":
                base_core.security.allowed["network_access"] = True
            case _:
                usage(program_name, sys.stderr)
                print(f"ERROR: Unknown argument '{arg}'", file=sys.stderr)
                exit(1)

    pos = Position(0, 0, 0, "<argv>", "<argv>")
    base_core.global_symbol_table.set("argv", base_core.radonify(argv, pos, pos, Context("<global>")))
    if source_file is not None:
        head, _ = os.path.split(source_file)
        try:
            with open(source_file, "r") as f:
                source = f.read()
        except FileNotFoundError:
            print(Log.deep_error(f"[!] FileNotFound: {Log.deep_error(source_file, bold=True)}"))
            exit(1)

        error: Error | RTError | None
        should_exit: Optional[bool]
        (_, error, should_exit) = base_core.run(source_file, source, import_cwd=head)  # type: ignore

        if error:
            print(error.as_string())
            exit(1)

        if should_exit:
            exit()

    elif command is not None:
        (_, error, should_exit) = base_core.run("<cli>", command)  # type: ignore

        if error:
            print(error.as_string())

    else:
        shell()


if __name__ == "__main__":
    main(sys.argv)
