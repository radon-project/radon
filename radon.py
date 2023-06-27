#!/usr/bin/python3.11
# By: Md. Almas Ali

import argparse

import core as base_core


def shell():
    print('Radon 0.0.1\nPress Ctrl+C to exit()')
    while True:
        try:
            text = input('radon > ')
            if text.strip() == "":
                continue
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
args = parser.parse_args()

if args.source:
    result, error, should_exit = base_core.run('<stdin>', f'require("{args.source}")')

    if error:
        print(error.as_string())
    elif result:
        if len(result.elements) == 1:
            print(repr(result.elements[0]))
        else:
            print(repr(result))

    if should_exit:
        exit()

else:
    shell()
