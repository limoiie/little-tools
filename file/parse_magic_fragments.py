import sys
from os import listdir
from typing import List

sys.path.append(r'..')

from file.fragment import MagicFragmentHandler
from file.fragment_test import TestFragmentHandler


def parse_magic_fragment_file(magic_fragment_file: str, handlers: List):
    with open(magic_fragment_file, 'r') as file:
        line_cnt = 0
        for line in file.readlines():
            line_cnt += 1
            for handler in handlers:
                handler.process_line(magic_fragment_file, line[:-1], line_cnt)


def main():
    handlers = [
        # MagicFragmentHandler(),
        TestFragmentHandler()
    ]

    # file = r'magic\archive'
    for file in listdir('./magic'):
        file = './magic/' + file
        print('process %s' % file)
        parse_magic_fragment_file(file, handlers)

    for handler in handlers:
        handler.finish()
        handler.print()


if __name__ == '__main__':
    main()
