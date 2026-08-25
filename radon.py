#!/usr/bin/env python3
# By: Md. Almas Ali

import os
import platform
import sys
from typing import IO, TYPE_CHECKING, Optional

from core.datatypes import Value
from core.errors import Error, RTError

# Enable ANSI colors on Windows
if sys.platform == "win32":
    try:
        import ctypes

        kernel32 = ctypes.windll.kernel32
        # Enable Virtual Terminal Processing for stdout and stderr
        for handle_id in (-11, -12):  # STD_OUTPUT_HANDLE, STD_ERROR_HANDLE
            handle = kernel32.GetStdHandle(handle_id)
            mode = ctypes.c_ulong()
            kernel32.GetConsoleMode(handle, ctypes.byref(mode))
            # ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
            kernel32.SetConsoleMode(handle, mode.value | 0x0004)
    except Exception:
        pass

if sys.platform != "win32" and not TYPE_CHECKING:
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
from core.colortools import ForegroundColor, Log, Style, Text
from core.parser import Context
from core.tokens import Position
from core.syntax import pt_input


documentation_link = "https://radon-project.github.io/docs/"


def start_text() -> None:
    Text(
        f"Radon {base_core.__version__} on {platform.machine()} {platform.system()} ({sys.platform})",
        ForegroundColor.BLUE,
        styles=[Style.BOLD],
    ).print()

    Text("Documentation:", ForegroundColor.YELLOW, styles=[Style.BOLD]).print(end=" ")
    Text(f"{documentation_link}").print()

    Text("Type ", ForegroundColor.GREEN, styles=[Style.BOLD]).print(end="")
    Text("help(obj), copyright(), credits(), license()", ForegroundColor.RED, styles=[Style.BOLD]).print(end="")
    Text(" for more info", ForegroundColor.GREEN, styles=[Style.BOLD]).print()

    Text("Type", ForegroundColor.GREEN, styles=[Style.BOLD]).print(end=" ")
    Text("exit", ForegroundColor.RED, styles=[Style.BOLD]).print(end=" ")
    Text("to quit the shell.", ForegroundColor.GREEN, styles=[Style.BOLD]).print()


def count_braces(line: str) -> int:
    """Count unmatched braces in a line, ignoring braces inside strings and comments.

    Returns the net brace count change for this line:
    - Positive value means more opening braces than closing braces
    - Negative value means more closing braces than opening braces
    - Zero means braces are balanced
    """
    count = 0
    in_string = False
    escape_next = False
    i = 0

    while i < len(line):
        char = line[i]

        if escape_next:
            escape_next = False
            i += 1
            continue

        if char == "\\":
            escape_next = True
            i += 1
            continue

        if char == '"':
            in_string = not in_string
            i += 1
            continue

        if in_string:
            i += 1
            continue

        # Check for comments (# to end of line)
        if char == "#":
            break

        if char == "{":
            count += 1
        elif char == "}":
            count -= 1

        i += 1

    return count


# Keywords that can start a block with braces
BLOCK_KEYWORDS = {"fun", "class", "if", "elif", "else", "while", "for", "try", "catch", "switch", "case", "default"}


def expects_block(text: str) -> bool:
    """Check if the text looks like it expects a block (has a block keyword but no opening brace).

    This handles cases like:
    - fun anything()   (no brace yet, expects block)
    - if condition     (no brace yet, expects block)
    - else             (no brace yet, expects block)
    """
    # Remove comments first
    comment_idx = -1
    in_string = False
    escape_next = False
    for i, char in enumerate(text):
        if escape_next:
            escape_next = False
            continue
        if char == "\\":
            escape_next = True
            continue
        if char == '"':
            in_string = not in_string
            continue
        if not in_string and char == "#":
            comment_idx = i
            break

    if comment_idx >= 0:
        text = text[:comment_idx]

    stripped = text.strip()
    if not stripped:
        return False

    # Check if there are ANY braces in the line (outside strings)
    # If there's at least one opening brace, the block has started
    has_opening_brace = False
    in_string = False
    escape_next = False
    for char in text:
        if escape_next:
            escape_next = False
            continue
        if char == "\\":
            escape_next = True
            continue
        if char == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if char == "{":
            has_opening_brace = True
            break

    # If there's already an opening brace, the block has started - don't expect more
    if has_opening_brace:
        return False

    # Check if the line contains a block keyword
    # We need to find actual keywords, not parts of identifiers
    words = []
    current_word = ""
    in_string = False
    escape_next = False

    for char in stripped:
        if escape_next:
            escape_next = False
            continue
        if char == "\\":
            escape_next = True
            continue
        if char == '"':
            in_string = not in_string
            current_word = ""
            continue
        if in_string:
            continue

        if char.isalnum() or char == "_":
            current_word += char
        else:
            if current_word:
                words.append(current_word)
            current_word = ""

    if current_word:
        words.append(current_word)

    # Check if any word is a block keyword
    has_block_keyword = any(word in BLOCK_KEYWORDS for word in words)

    return has_block_keyword


def shell() -> None:
    start_text()

    while True:
        try:
            text = pt_input(">>> ")
            if text.strip() == "":
                continue

            if text.strip() == "exit":
                break

            # Count braces in the initial line
            brace_count = count_braces(text)

            # Check if the line expects a block but doesn't have one
            # This handles cases like "fun anything()" on its own line
            awaiting_block = brace_count == 0 and expects_block(text)

            # Continue reading lines while braces are unbalanced or we're awaiting a block
            while brace_count > 0 or awaiting_block:
                new_line = pt_input("... ")
                text += "\n" + new_line
                line_brace_count = count_braces(new_line)
                brace_count += line_brace_count

                # If we were awaiting a block and got any braces, we're no longer awaiting
                # (either we got the opening brace we expected, or a closing brace which will cause an error)
                if awaiting_block and line_brace_count != 0:
                    awaiting_block = False
                # If no braces found on this line and we're still awaiting, check if user wants to stop
                elif awaiting_block and line_brace_count == 0:
                    # Stop awaiting if user entered an empty line (to allow them to submit incomplete code for error)
                    if new_line.strip() == "":
                        awaiting_block = False

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
    print(f"Usage: {program_name} [source_file] [--command | -c <cmd>] [--version | -v] [--help | -h]", file=stream)
    print(
        """
Options and arguments:
    source_file      Run a source file
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
    radon source_file.rn
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
                sys.exit(0)
            case "--version" | "-v":
                print(base_core.__version__)
                sys.exit(0)
            case "--command" | "-c":
                if len(argv) == 0:
                    usage(program_name, sys.stderr)
                    print(f"ERROR: {arg} requires an argument", file=sys.stderr)
                    sys.exit(1)
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
                if source_file is None and command is None and not arg.startswith("-"):
                    source_file = arg
                    break
                usage(program_name, sys.stderr)
                print(f"ERROR: Unknown argument '{arg}'", file=sys.stderr)
                sys.exit(1)

    pos = Position(0, 0, 0, "<argv>", "<argv>")
    base_core.global_symbol_table.set("argv", base_core.radonify(argv, pos, pos, Context("<global>")))
    if source_file is not None:
        head, _ = os.path.split(source_file)
        try:
            with open(source_file, "r") as f:
                source = f.read()
        except FileNotFoundError:
            print(Log.deep_error(f"[!] FileNotFound: {Log.deep_error(source_file, bold=True)}"))
            sys.exit(1)

        error: Error | RTError | None
        should_exit: Optional[bool]
        (_, error, should_exit) = base_core.run(source_file, source, import_cwd=head)  # type: ignore

        if error:
            print(error.as_string())
            sys.exit(1)

        if should_exit:
            sys.exit()

    elif command is not None:
        (_, error, should_exit) = base_core.run("<cli>", command)  # type: ignore

        if error:
            print(error.as_string())

    else:
        shell()


if __name__ == "__main__":
    main(sys.argv)
