import logging
import re
from typing import Dict

from file.init_logging import init_log
from file.type_record import TypeDatabase


def main():
    all_records = get_all_records()
    all_records = sort_by_id(all_records)

    logging.info('all info:')

    with open('file_type.h', 'w+') as file:
        file.write('typedef enum {\n')

        line_prefix = '\t'
        count = 1
        for type_id, record in all_records.items():
            var_name = convert_desc_to_var_name(record.type_desc)
            file.write(line_prefix + '// category: %s\n' % record.file_name[len('./magic/'):])
            file.write(line_prefix + '// description: %s\n' % record.type_desc)
            file.write(line_prefix + '%s = %d,\n' % (var_name, type_id))
            file.write('\n')
            # logging.info('i: %04d, id: %04d, desc: %s' % (count, type_id, type_desc))
            # logging.info('i: %04d, id: %04d, name: %s' % (count, type_id, var_name))
            logging.info('')
            count += 1

        file.write('} file_type_e;\n')

    logging.info('exit')


def get_all_records():
    db: TypeDatabase = TypeDatabase.instance
    all_types: Dict[int, str] = dict()
    for file_container in db.get_all().values():
        for record in file_container.values():
            all_types[record.unique_id] = record

    logging.debug(f'Get {len(all_types)} types in total')
    return all_types


def sort_by_id(all_types: dict):
    sorted_all_types = dict()
    for type_id in sorted(all_types.keys()):
        sorted_all_types[type_id] = all_types[type_id]
    return sorted_all_types


def convert_desc_to_var_name(desc: str):
    desc = replace_format_tmpl_with_upper_type(desc)
    desc = replace_non_alpha_non_digit_with_space(desc)
    non_empty_sub_string = split_to_non_empty_sub_strings(desc)
    candidate_name = '_'.join(non_empty_sub_string)
    return insert_an_a_if_start_with_number(candidate_name)


def replace_format_tmpl_with_upper_type(desc: str):
    matched = re.search(r'(%-?[\d]*\.*[\d]*\w)', desc)
    if matched:
        tmpl = matched.group(1)
        type_name = tmpl[-1].upper() * 2
        desc = desc.replace(tmpl, type_name)
    return desc


def replace_non_alpha_non_digit_with_space(desc: str):
    var_name = ''
    for c in desc:
        if c.isalpha():
            var_name += c.upper()
        elif c.isdigit():
            var_name += c
        else:
            var_name += ' '
    return var_name


def split_to_non_empty_sub_strings(string: str):
    sub_strings = string.split(' ')
    non_empty_sub_strings = []
    for string in sub_strings:
        if string:
            non_empty_sub_strings.append(string)
    return non_empty_sub_strings


def insert_an_a_if_start_with_number(string: str):
    if string[0].isdigit():
        return 'A_' + string
    return string


if __name__ == '__main__':
    init_log(logging.ERROR)
    main()
    pass
