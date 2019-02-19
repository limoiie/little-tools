import re
import codecs
import sys
import getopt
from typing import Optional, Match

list_file_path = r'./list'
encoding = 'utf-8'


def print_help():
    print('Usage: -c <count>')


def process_lines(handler):
    with codecs.open(list_file_path, 'r', encoding=encoding) as file:
        for line in file.readlines():
            if line.startswith('Strength'):
                line = line[:-2]
                handler(line)


def count_lines():
    with codecs.open(list_file_path, 'r', encoding=encoding) as file:
        count = 0
        for line in file.readlines():
            line = line[:-1]
            if line.startswith('Strength'):
                count += 1
        print('%d lines in total' % count)


def show_lines(line: str):
    matched = re.search(r'(>+)', line, re.M | re.I)
    if len(matched.group()) == 1:
        print('\n', '-'*10)
    print(line)


def show_desc(line: str):
    left_quota, right_quota = line.find('`'), line.rfind('`')
    ext = line[left_quota + 1:right_quota]
    if ext:
        print('%-50s\t%s' % (ext, line))


def show_ext(line: str):
    left_quota, right_quota = line.rfind('['), line.rfind(']')
    ext = line[left_quota + 1:right_quota]
    if ext:
        print('%s\t%s' % (ext, line))


def show_apple(line: str):
    matched = re.search(r'\[(.*)\], \[(.*)\], \[(.*)\]', line, re.M | re.I)
    apple = matched.group(2)
    if apple:
        print('%s\t%s' % (apple, line))


def show_lineno_desc(line: str):
    matched = re.search(r'@([\d]*): `(.*)`', line, re.M | re.I)
    print('%-10s%s' % (matched.group(1), matched.group(2)))


def main(argv):
    try:
        opts, args = getopt.getopt(argv, 'hfcsedal',
                                   ['file', 'count', 'show', 'ext', 'desc', 'apple', 'linedesc'])
    except getopt.GetoptError:
        print_help()
        sys.exit(-1)

    for opt, arg in opts:
        if opt == '-h':
            print_help()
            sys.exit(0)
        elif opt in ('-f', '--file'):
            global list_file_path
            list_file_path = opt
        elif opt in ('-c', '--count'):
            count_lines()
        elif opt in ('-s', '--show'):
            process_lines(show_lines)
        elif opt in ('-e', '--ext'):
            process_lines(show_ext)
        elif opt in ('-d', '--desc'):
            process_lines(show_desc)
        elif opt in ('-a', '--apple'):
            process_lines(show_apple)
        elif opt in ('-l', '--linedesc'):
            process_lines(show_lineno_desc)


if __name__ == '__main__':
    main(sys.argv[1:])
