#!/usr/bin/python3.12
# By: Md. Almas Ali

import argparse
import pathlib
import sys

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


def shell():
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


def main(argv: list[str]) -> None:
    parser = argparse.ArgumentParser(description="Radon programming language")
    parser.add_argument(
        "-p",
        "--hide-file-paths",
        help="Don't show file paths in error messages [NOT CURRENTLY WORKING]",
        action="store_true",
    )
    parser.add_argument("-s", "--source", type=str, help="Radon source file", nargs="*")
    parser.add_argument("-c", "--command", type=str, help="Command to execute as string")
    parser.add_argument("-v", "--version", help="Version info", action="store_true")
    args = parser.parse_args()
    
    if args.source:
        source = pathlib.Path(args.source[0]).read_text()
        (result, error, should_exit) = base_core.run(
            args.source[0], source, hide_paths=args.hide_file_paths
        )
    
        if error:
            print(error.as_string())
            exit(1)
    
        if should_exit:
            exit()
    
    
    elif args.command:
        (result, error, should_exit) = base_core.run("<stdin>", args.command)
    
        if error:
            print(error.as_string())
    
    elif args.version:
        print(base_core.__version__)
    
    else:
        shell()

if __name__ == "__main__":
    main(sys.argv[1:])

