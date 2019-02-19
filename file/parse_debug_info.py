import codecs
import re

list_file_path = r'C:\Users\ligeng\Desktop\debug_info'
debug_info_z = r'E:\projects\pycharm\little-tools\file\debug_info_z'
encoding = 'utf-8'


def extract_dump_lines():
    """from debug_info to debug_info_z"""
    with codecs.open(list_file_path, 'r', encoding=encoding) as file:
        for line in file.readlines():
            line = line[:-1]
            if re.match(r'[\d]*:.*\]', line):
                print(line)
    pass


def show_lineno_desc():
    with codecs.open(debug_info_z, 'r', encoding=encoding) as file:
        for line in file.readlines():
            line = line[:-1]
            matched = re.search(r'([\d]*):.*"(.*)"', line, re.M | re.I)
            print('%-10s%s' % (matched.group(1), matched.group(2)))


def main():
    show_lineno_desc()


if __name__ == '__main__':
    main()
