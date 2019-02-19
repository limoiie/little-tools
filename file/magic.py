import re
from file.op_intersect import are_intersect


class Type:

    def __init__(self):
        self.type = None
        self.subtype = None

    def __str__(self):
        return self.type + self.subtype

    def __eq__(self, other):
        return self.type == other.type

    def parse(self, seq: str):
        parts = seq.split('/')
        if 1 == len(parts):
            parts = seq.split('&')
        self.type = parts[0]
        self.subtype = parts[1] if 2 == len(parts) else ''
        return self

    def is_default(self):
        return self.type == 'default'

    def is_clear(self):
        return self.type == 'clear'

    def is_string(self):
        return 'string' in self.type

    def is_float(self):
        return 'double' in self.type or 'float' in self.type

    def is_functional(self):
        return self.type == 'indirect' or \
               self.type == 'default' or \
               self.type == 'search' or \
               self.type == 'regex' or \
               self.type == 'clear' or \
               self.type == 'name' or \
               self.type == 'use'


class Test:

    def __init__(self):
        self.op = None
        self.val = None

    def __str__(self):
        return self.op + self.val

    def always_true(self):
        return 'x' == self.op and '' == self.val

    def parse(self, seq: str):
        if 'x' == seq:
            self.op = 'x'
            self.val = ''
        elif seq[0] in '=!<>&^':
            self.op = seq[0]
            self.val = seq[1:]
        else:
            self.op = r'='
            self.val = seq
        return self

    def intersect(self, other, val_type):
        priory = {'=': 5, '!': 4, '<': 3, '>': 2, '&': 1, '^': 0}
        if priory[self.op] > priory[other.op]:
            return are_intersect(self, other, val_type)
        return are_intersect(other, self, val_type)


class Magic:

    def __init__(self):
        self.level = None
        self.offset = None
        self.type = None
        self.tests = None
        self.desc = None
        self.line_no = 0

    def __str__(self):
        def print_list(objs):
            return ','.join([str(obj) for obj in objs])

        return '[%s], [%s], [%s], [%s], [%s]' % (
            r'>' * self.level, self.offset, self.type, print_list(self.tests), self.desc
        )

    def parse(self, line: str, line_no: int):
        line = line + ' '  # add a blank to help regex
        # match_obj = re.match(r'^(>*)([^\s]+)[\s]+([^\s]+)\s+(.*?[^\s\\])[\s]+(.*)', line)
        match_obj = re.match(r'^(>*)([^\s]+)[\s]+([^\s]+)\s+(.*[^\\])[\s]+(.*)', line)
        if match_obj is None:
            print('failed to parse in line %d: ~%s~' % (line_no, line))
            return None

        self.level = len(match_obj.group(1))
        self.offset = match_obj.group(2)
        self.type = Type().parse(match_obj.group(3))
        self.tests = [Test().parse(match_obj.group(4))]
        self.desc = match_obj.group(5)[:-1]
        self.line_no = line_no
        return self

    def can_after(self, prev):
        if self.type.is_default():
            return False

        if prev.type.is_functional() or \
                self.type.is_functional():
            return True

        if prev.type != self.type or \
                prev.offset != self.offset:
            return True

        for prev_test in prev.tests:
            if prev_test.always_true():
                continue
            for curr_test in self.tests:
                if curr_test.always_true():
                    continue
                if not prev_test.intersect(curr_test, self.type):
                    return False
        return True
