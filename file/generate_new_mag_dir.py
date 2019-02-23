import logging
import os

from file.init_logging import init_log
from file.magic import parse_magic
from file.type_record import TypeDatabase


def generate_new_magic_file(source_file: str, target_file: str):
    with open(source_file, 'r') as source:
        with open(target_file, 'w+') as target:
            for line_no, line in enumerate(source.readlines()):
                line_no += 1

                if not line.startswith('#') and not line.startswith('!'):
                    magic_line = line[:-1]
                    if magic_line:
                        magic = parse_magic(magic_line)
                        if magic.desc:
                            record = find_record(source_file, line_no)
                            if record:
                                line_string = line.rstrip(' \r\n\t')
                                # line_end = line[len(line_string):]
                                extra_info = '|%d' % record.unique_id
                                line = line_string + extra_info + '\n'

                target.write(line)


def find_record(file: str, line_no: int):
    db: TypeDatabase = TypeDatabase.instance
    return db.get_record_by_file_and_line(file, line_no)


def main():
    init_log()

    source_dir = './magic'
    target_dir = './new-magic'

    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    # file = r'archive'
    # if file:
    for file in os.listdir('./magic'):
        source_file = source_dir + '/' + file
        target_file = target_dir + '/' + file
        logging.info(f'process {source_file} to {target_file}')
        generate_new_magic_file(source_file, target_file)


if __name__ == '__main__':
    main()
