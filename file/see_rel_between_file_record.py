import logging
from typing import Dict

from file.init_logging import init_log
from file.type_record import TypeDatabase


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


def see_rel_between_file_and_record():
    all_records = get_all_records()
    all_records = sort_by_id(all_records)

    pre_file_name = ''
    for record in all_records.values():
        if record.file_name != pre_file_name:
            print(record.file_name)
            pre_file_name = record.file_name
    pass


def main():
    see_rel_between_file_and_record()
    pass


if __name__ == '__main__':
    init_log()
    main()
