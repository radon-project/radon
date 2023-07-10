#!/usr/bin/python3.11
# By: Md. Almas Ali

import argparse

import core as base_core


def shell():
    print('Radon 0.0.1\nPress Ctrl+C to exit()')
    brace_count = 0

    while True:
        try:
            text = input('>>> ')
            if text.strip() == "":
                continue

            if text.strip()[-1] == '{':
                brace_count += 1
                while True:
                    text += '\n' + input('... ')
                    if text.strip()[-1] == '{':
                        brace_count += 1
                    elif text.strip()[-1] == '}' or \
                            text.strip()[0] == '}':
                        brace_count -= 1

                    if brace_count == 0:
                        break

            result, error, should_exit = base_core.run('<stdin>', text)

            if error:
                print(error.as_string())
            elif result:
                if len(result.elements) == 1:
                    print(repr(result.elements[0]))
                else:
                    print(repr(result))

            if should_exit:
                break
        except KeyboardInterrupt:
            print('KeyboardInterrupt')


parser = argparse.ArgumentParser(description='Radon programming language')
parser.add_argument('-s', '--source', type=str, help='Radon source file')
parser.add_argument('-c', '--command', type=str,
                    help='Command to execute as string')
parser.add_argument('-v', '--version', help='Version info',
                    action='store_true')
args = parser.parse_args()

if args.source:
    result, error, should_exit = base_core.run(
        '<stdin>', f'require("{args.source}")')

    if error:
        print(error.as_string())
    elif result:
        if len(result.elements) == 1:
            print(repr(result.elements[0]))
        else:
            print(repr(result))

    if should_exit:
        exit()

elif args.command:
    result, error, should_exit = base_core.run('<stdin>', args.command)

    if error:
        print(error.as_string())
    elif result:
        if len(result.elements) == 1:
            print(repr(result.elements[0]))
        else:
            print(repr(result))

elif args.version:
    print(base_core.__version__)

else:
    shell()
