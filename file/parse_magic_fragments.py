import sys
from os import listdir

sys.path.append(r'E:\projects\pycharm\little-tools')

from file.fragment import MagicFragmentHandler
from file.fragment_test import TestFragmentHandler


def parse_magic_fragment_file(magic_fragment_file: str):
    handlers = [
        # MagicFragmentHandler(),
        TestFragmentHandler()
    ]

    with open(magic_fragment_file, 'r') as file:
        line_cnt = 0
        for line in file.readlines():
            line_cnt += 1
            for handler in handlers:
                handler.process_line(line[:-1], line_cnt)

        for handler in handlers:
            handler.finish()

    return handlers


def main():
    # file = r'magic\archive'
    for file in listdir('./magic'):
        file = './magic/' + file
        print('process %s' % file)
        handlers = parse_magic_fragment_file(file)
        for handler in handlers:
            handler.print()


if __name__ == '__main__':
    main()
