import getopt
import json
import logging
import sys
from typing import Dict, Any

from file.init_logging import init_log


class TypeRecord:

    def __init__(self, unique_id: int, file_name: str, line_number: int, type_desc: str):
        self.unique_id = unique_id
        self.file_name = file_name
        self.line_number = line_number
        self.type_desc = type_desc

    def __str__(self):
        return str(TypeRecordCoder().default(self))

    def __copy__(self):
        return TypeRecord(self.unique_id, self.file_name,
                          self.line_number, self.type_desc)


class TypeRecordCoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, TypeRecord):
            return {
                '__type_record__': True,
                'unique_id': obj.unique_id,
                'file_name': obj.file_name,
                'line_number': obj.line_number,
                'type_desc': obj.type_desc
            }
        return super().default(self, obj)

    @staticmethod
    def decode(dct):
        if '__type_record__' in dct:
            return TypeRecord(dct['unique_id'],
                              dct['file_name'],
                              dct['line_number'],
                              dct['type_desc'])
        return dct


# def decode_type_record(obj):
#     if isinstance(obj, dict) and 'treenode_name' in obj:
#         new_obj = TreeNode(obj['treenode_name'])
#         for name, sub_obj in obj.get('child', {}).items():
#             new_obj.add_child(name, decode_type_record(sub_obj))
#         return new_obj
#     return obj
#
#
class TypeDatabase:
    instance = None
    type_id_map: Dict[Any, Any] = dict()
    id_base = 0

    container: Dict[str, Dict[int, TypeRecord]]

    def __init__(self, db_file: str):
        self.db_file = db_file
        self.container = None
        self.load()

    def load(self):
        try:
            with open(self.db_file, 'r') as file:
                self.container = json.load(file, object_hook=TypeRecordCoder.decode)
        except FileNotFoundError:
            self.container = dict()
            logging.warning(f'Not found database file: `{self.db_file}`')
        except json.decoder.JSONDecodeError:
            self.container = dict()
            logging.warning(f'Failed to parse json from file: `{self.db_file}`, ignored the content')

        self.__update_line_number_type()
        self.__update_id_base()

    def __update_id_base(self):
        id_base = 0
        for file_container in self.container.values():
            for record in file_container.values():
                TypeDatabase.type_id_map[record.type_desc] = record.unique_id
                id_base = max(id_base, record.unique_id)
        TypeDatabase.id_base = id_base + 1

    def dump(self):
        with open(self.db_file, 'w+') as file:
            json.dump(self.container, fp=file, cls=TypeRecordCoder, indent=4, sort_keys=False)

    def __update_line_number_type(self):
        new_container = dict()
        for file_name, file_container in self.container.items():
            new_file_container = dict()
            for line_num_str, record in file_container.items():
                new_file_container[int(line_num_str)] = record
            new_container[file_name] = new_file_container
        self.container = new_container

    @staticmethod
    def new_record(file_name, line_number, desc):
        generated_unique_id = TypeDatabase.__generate_unique_id(desc)
        record = TypeRecord(generated_unique_id, file_name, line_number, desc)
        return record

    @staticmethod
    def __generate_unique_id(desc):
        if desc in TypeDatabase.type_id_map:
            return TypeDatabase.type_id_map[desc]

        new_unique_id = TypeDatabase.id_base
        TypeDatabase.id_base += 1
        TypeDatabase.type_id_map[desc] = new_unique_id
        return new_unique_id

    def put_record(self, record: TypeRecord):
        if record.file_name not in self.container:
            self.container[record.file_name] = dict()
        self.container[record.file_name][record.line_number] = record

    def get_all(self):
        return self.container.copy()

    def get_records_by_file_name(self, file_name: str):
        if file_name not in self.container:
            return None
        return self.container[file_name].copy()

    def get_record_by_file_and_line(self, file_name: str, line_number: int):
        records = self.get_records_by_file_name(file_name)
        if records:
            if line_number in records:
                return records[line_number]
        return None

    def get_records_by_id(self, unique_id: int):
        records = dict()
        for file_name, file_container in self.container.items():
            for line_no, record in file_container.items():
                if record.unique_id == unique_id:
                    if file_name not in records:
                        records[file_name] = dict()
                    records[file_name][line_no] = record
        return records

    def pop_record_by_id(self, unique_id):
        for file_container in self.container.values():
            for record in file_container.values():
                if record.unique_id == unique_id:
                    return file_container.pop(record.line_number)

    def clear_all(self):
        self.container.clear()


TypeDatabase.instance: TypeDatabase = TypeDatabase('types-database.json')


def test():
    test_db: TypeDatabase = TypeDatabase.instance

    for file_name, file_container in test_db.get_all().items():
        print('ACCESS ', file_name)
        for record in file_container.values():
            print(record)
        print()


def parse_and_exec_command(command_string: str):
    argv = command_string.split(' ')
    try:
        opts, args = getopt.getopt(argv, "hai:f:l:", ['help', 'all', 'id=', 'file=', 'line='])
    except getopt.GetoptError:
        print_help()
        # sys.exit(2)
        return

    file = None
    line = None

    for opt, arg in opts:
        if opt == '-h':
            print_help()
        elif opt in ('-a', '--all'):
            print_all_info()
        elif opt in ('-i', '--id'):
            try:
                print_types_by_id(int(arg))
                return
            except ValueError:
                print(f'id should be int, get val of {type(arg)}')
                print_help()
                return
        elif opt in ('-f', '--file'):
            file = './magic/%s' % arg
        elif opt in ('-l', '--line'):
            try:
                line = int(arg)
            except ValueError:
                print(f'line should be int, get val of {type(arg)}')
                print_help()
                return

    if file:
        if line:
            print_type_by_file_and_line(file, line)
            return
        else:
            print_types_by_file(file)
            return

    print_help()


def print_help():
    print('USAGE: -i <type id> -f <file name> -line <line number> ')
    # sys.exit(ret_code)


def print_all_info():
    all_data: dict = TypeDatabase.instance.get_all()
    print(f'there is {len(all_data.keys())} files in total,')

    records_list = []
    types_set = set()
    for file_container in all_data.values():
        for record in file_container.values():
            records_list.append(record)
            types_set.add(record.type_desc)

    print(f'\tand {len(records_list)} records in total')
    print(f'\tand {len(types_set)} types in total')
    print()
    pass


def print_types_by_id(type_id: int):
    print(f'type records with id {type_id}:')
    records = TypeDatabase.instance.get_records_by_id(type_id)
    for file_name, file_container in records.items():
        print_records_in_file(file_name, file_container)
    else:
        print(f'None with id {type_id}')
    print()


def print_type_by_file_and_line(file: str, line: int):
    print(f'type record at line {line} in file `{file}`:')
    record = TypeDatabase.instance.get_record_by_file_and_line(file, line)
    print(record)
    print()


def print_types_by_file(file: str):
    print(f'type records in file `{file}`:')
    records = TypeDatabase.instance.get_records_by_file_name(file)
    print_records_in_file(file, records)
    print()


def print_records_in_file(file_name, records_in_file):
    if not records_in_file:
        print(f'None in {file_name}')
        return

    print(f'{file_name} contains {len(records_in_file)} records:')
    for i, record in enumerate(records_in_file.values()):
        print(f'\t{i}:', record)


def main():
    while True:
        x = input('please input command: ')
        if x == 'exit':
            print('exit')
            exit(0)
        parse_and_exec_command(x)


if __name__ == '__main__':
    init_log()
    main()
