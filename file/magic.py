from typing import List

from file.op_intersect import are_intersect


class Type:

    all_ops = '/&+-*'

    def __init__(self):
        self.type = None
        self.op = ''
        self.subtype = ''

    def __str__(self):
        return self.type + self.op + self.subtype

    def __eq__(self, other):
        return self.type == other.type \
               # and self.subtype == other.subtype

    def is_default(self):
        return self.type == 'default'

    def is_clear(self):
        return self.type == 'clear'

    def is_text(self):
        return 'string' in self.type or 'byte' in self.type

    def is_string(self):
        return 'string' in self.type

    def is_byte(self):
        return 'byte' in self.type

    def is_float(self):
        return 'double' in self.type or 'float' in self.type

    def is_name(self):
        return 'name' in self.type

    def is_functional(self):
        return self.type == 'indirect' or \
               self.type == 'default' or \
               self.type == 'clear' or \
               self.type == 'name' or \
               self.type == 'use'

    def is_use(self):
        return 'use' in self.type


def parse_type(seq: str):
    tp = Type()
    for op in Type.all_ops:
        parts = seq.split(op)
        if 1 == len(parts):
            continue
        tp.type = parts[0]
        tp.op = op
        tp.subtype = parts[1]
        return tp

    tp.type = seq
    return tp


class Test:

    all_ops = '=!<>&^'

    def __init__(self):
        self.op = None
        self.val = None
        self.__always_true = False

    def __str__(self):
        return self.op + self.val

    def always_true(self):
        if self.__always_true:
            return True
        return 'x' == self.op and '' == self.val

    def set_always_true(self):
        self.__always_true = True

    def intersect(self, other, val_type: Type):
        return are_intersect(other, self, val_type)


def parse_test(seq: str, magic_type: Type):
    test = Test()
    if r'x' == seq:
        test.set_always_true()
        test.op, test.val = r'x', ''
    elif seq[0] in Test.all_ops:
        test.op, test.val = seq[0], seq[1:]
    else:
        test.op, test.val = r'=', seq

    # 'string/W val' will be replaced with string 'string/w \sval'
    if 'string' in magic_type.type and '/' == magic_type.op:
        magic_type.op = ''
        magic_type.subtype = ''
        test.val = ' ' + test.val
    return test


class Magic:

    level: int
    offset: str
    type: Type
    test: Test
    desc: str
    file_name: str

    def __init__(self):
        self.level = None
        self.offset = None
        self.type = None
        self.test = None
        self.desc = None
        self.line_no = 0
        self.line = None
        self.file_name = None

    def __str__(self):
        def print_list(objs):
            return ','.join([str(obj) for obj in objs])

        return '[%s], [%s], [%s], [%s], [%s]' % (
            r'>' * self.level, self.offset, self.type, self.test, self.desc
        )

    def is_name(self):
        return self.type.is_name()
    
    def is_use(self):
        return self.type.is_use()

    def is_default(self):
        return self.type.is_default()

    def is_functional(self):
        return self.type.is_functional()

    def get_name(self):
        if self.is_name() or self.is_use():
            return self.test.val
        return ''

    def can_after(self, prev):
        if self.type.is_default():
            return False

        if prev.type.is_functional() or \
                self.type.is_functional():
            return True

        if not have_same_test_method(self, prev):
            return True

        if not prev.test.always_true() and not self.test.always_true():
            if not prev.test.intersect(self.test, self.type):
                return False
        return True


def have_same_test_method(lhv: Magic, rhv: Magic):
    same_type = lhv.type == rhv.type or \
                lhv.type.is_text() and rhv.type.is_text()

    return same_type and lhv.offset == rhv.offset


def parse_magic(line: str):
    magic = Magic()
    magic.line = line
    magic.level, i = extract_level(line, 0)
    magic.offset, i = extract_offset(line, i)
    magic.type, i = extract_type(line, i)
    magic.test, i = extract_test(line, i, magic.type)
    magic.desc, i = extract_desc(line, i)

    if magic.is_functional():
        magic.test.set_always_true()

    if magic.type.is_text():
        format_magic_desc_if_possible(magic)

    if magic.is_use():
        if magic.test.val.startswith(r'\^'):
            magic.test.val = magic.test.val[2:]
    return magic


def jump_blank(line: str, idx: int):
    while idx < len(line):
        if line[idx] != '\t' and line[idx] != ' ':
            break
        idx += 1
    return idx


def get_sequence(line: str, start: int):
    start = idx = jump_blank(line, start)
    while idx < len(line):
        if line[idx] == '\t' or line[idx] == ' ':
            if start < idx and line[idx-1] != '\\':
                break
        idx += 1
    return line[start:idx], idx


def get_remainder(line: str, start: int):
    start = jump_blank(line, start)
    remainder = line[start:]
    remainder = remainder.strip('\r\n\t ')
    return remainder, len(line)


def extract_level(line: str, idx: int):
    level = 0
    while idx < len(line):
        if line[idx] != '>':
            break
        level += 1
        idx += 1
    return level, idx


def extract_offset(line: str, start: int):
    return get_sequence(line, start)


def extract_type(line: str, start: int):
    string, idx = get_sequence(line, start)
    return parse_type(string), idx


def extract_test(line: str, start: int, magic_type: Type):
    start = jump_blank(line, start)
    op = line[start]
    if op in Test.all_ops:
        string, idx = get_sequence(line, start + 1)
        string = op + string
    else:
        string, idx = get_sequence(line, start)
    return parse_test(string, magic_type), idx


def extract_desc(line: str, start: int):
    return get_remainder(line, start)


def join_magic_desc(prefix: str, magic_desc: str):
    if not magic_desc:
        return prefix

    if magic_desc.startswith(r'\b'):
        return prefix + magic_desc[2:]

    if not prefix:
        return magic_desc
    return prefix + ' ' + magic_desc


def format_magic_desc_if_possible(magic: Magic):
    test = magic.test
    if r'=' == test.op and r'%s' in magic.desc:
        parsed_desc = clear_escape_char(test.val)
        magic.desc = magic.desc.replace(r'%s', parsed_desc)


def clear_escape_char(string: str):
    return string.replace(r'\ ', r' ')
