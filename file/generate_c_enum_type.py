import logging
import re
from typing import Dict

from file.init_logging import init_log
from file.type_record import TypeDatabase
from file.utils import convert_desc_to_var_name


def main():
    all_records = get_all_records()
    all_records = sort_by_id(all_records)

    logging.info('all info:')

    with open('file_type.h', 'w+') as file:
        file.write('#ifndef FILE_TYPE_H\n')
        file.write('#define FILE_TYPE_H\n')
        file.write('\n')
        file.write('enum file_type_e {\n')
        file.write('\tBINARY_DATA = 0,\n')
        file.write('\n')

        line_prefix = '\t'
        count = 1
        for type_id, record in all_records.items():
            var_name = convert_desc_to_var_name(record.type_desc)
            file.write(line_prefix + '/* category: %s */\n' % record.file_name[len('./magic/'):])
            file.write(line_prefix + '/* description: %s */\n' % record.type_desc)
            file.write(line_prefix + '%s = %d,\n' % (var_name, type_id))
            file.write('\n')
            # logging.info('i: %04d, id: %04d, desc: %s' % (count, type_id, type_desc))
            # logging.info('i: %04d, id: %04d, name: %s' % (count, type_id, var_name))
            logging.info('')
            count += 1

        file.write('};\n')
        file.write('\n')
        file.write('#endif /* FILE_TYPE_H */\n')
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


if __name__ == '__main__':
    init_log(logging.ERROR)
    main()
    pass
