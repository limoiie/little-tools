import re


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


def str_to_int(string: str):
    if string.startswith('0x'):
        return int(string, 16)
    if string.startswith('0'):
        return int(string, 8)
    return int(string)


def intersect_with_equal(val1, op2, val2):
    if op2 == '=':
        return val1 == val2
    if op2 == '!':
        return val1 != val2
    if op2 == '<':
        return val1 < val2
    if op2 == '>':
        return val1 > val2
    if op2 == '&':
        return val1 & val2 == val2
    if op2 == '^':
        return val1 ^ val2 & val2 == val2


def intersect_with_no_equal(val1, op2, val2):
    if op2 == '!':
        return True
    if op2 == '<':
        return True
    if op2 == '>':
        return True
    if op2 == '&':
        return True
    if op2 == '^':
        return True


def intersect_with_lt(val1, op2, val2, val_type):
    if op2 == '<':
        return True
    if op2 == '>':
        if 'double' in val_type or 'float' in val_type or 'string' in val_type:
            return val1 > val2
        return str_to_int(val1) > str_to_int(val2) + 1
    if op2 == '&':
        return True
    if op2 == '^':
        return True


def intersect_with_gt(val1, op2, val2):
    if op2 == '>':
        return True
    if op2 == '&':
        return True
    if op2 == '^':
        return True


def intersect_with_bit_and(val1, op2, val2):
    val1 = str_to_int(val1)
    val2 = str_to_int(val2)

    if op2 == '&':
        return True
    if op2 == '^':
        return val1 & val2 == 0


def intersect_with_bit_xor(val1, op2, val2):
    if op2 == '^':
        return True


def are_intersect(test1, test2, val_type):
    if test1.op == '=':
        return intersect_with_equal(test1.val, test2.op, test2.val)
    if test1.op == '!':
        return intersect_with_no_equal(test1.val, test2.op, test2.val)
    if test1.op == '<':
        return intersect_with_lt(test1.val, test2.op, test2.val, val_type)
    if test1.op == '>':
        return intersect_with_gt(test1.val, test2.op, test2.val)
    if test1.op == '&':
        return intersect_with_bit_and(test1.val, test2.op, test2.val)
    if test1.op == '^':
        return intersect_with_bit_xor(test1.val, test2.op, test2.val)


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
        elif seq[0].isalpha():
            self.op = r'='
            self.val = seq
        else:
            self.op = seq[0]
            self.val = seq[1:]
        return self

    def intersect(self, other, val_type):
        priory = {'=':5, '!':4, '<':3, '>':2, '&':1, '^':0}
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

    def __str__(self):
        return '[%s], [%s], [%s], [%s], [%s]' % (
            r'>' * self.level, self.offset, self.type, self.tests, self.desc
        )

    def parse(self, line: str):
        line = line + ' '  # add a blank to help regex
        match_obj = re.match(r'^(>*)([^\s]+)[\s]+([^\s]+)\s+(.*?[^\s\\])[\s]+(.*)', line)
        self.level = len(match_obj.group(1))
        self.offset = match_obj.group(2)
        self.type = Type().parse(match_obj.group(3))
        self.tests = [Test().parse(match_obj.group(4))]
        self.desc = match_obj.group(5)[:-1]
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
            for curr_test in self.tests:
                if not prev_test.intersect(curr_test, self.type):
                    return False
        return True


class TreeNode:

    val: Magic

    def __init__(self, val):
        self.val = val
        self.children = []
        self.father = None

    def add_child(self, child):
        self.children.append(child)
        child.father = self


def dump(node: TreeNode):
    magic = node.val

    string = magic.desc
    for child in node.children:
        string += ' ' + dump(child)

    empty_desc = 0 == len(magic.desc)
    if empty_desc:
        return string[1:]

    for sub_test in magic.tests:
        if not magic.tests.always_true():
            return '[%s]' % string

    # always true
    return string


class MagicTree:

    root: TreeNode

    def __init__(self, root):
        self.root = root

    def print(self):
        print(dump(self.root))


class MagicTreeBuilder:

    father_node: TreeNode

    def __init__(self):
        self.__root_node = None
        self.__father_node = None

    def feed_magic(self, magic: Magic):
        if self.__father_node is None:
            assert 0 == magic.level
            self.__father_node = TreeNode(magic)
            self.__root_node = self.__father_node
        else:
            assert 0 < magic.level
            curr_level = self.__curr_level()
            if curr_level == magic.level:
                self.__father_node.add_child(TreeNode(magic))
            elif curr_level < magic.level:
                assert curr_level + 1 == magic.level
                assert 0 < len(self.__father_node.children)
                self.__father_node = self.__father_node.children[-1]
                self.__father_node.add_child(TreeNode(magic))
            else:  # curr_level > magic.level
                self.__pop_till(magic.level)
                self.__father_node.add_child(TreeNode(magic))

    def build(self):
        if self.__father_node is None:
            return
        while self.__father_node.father is not None:
            self.__father_node = self.__father_node.father
        return MagicTree(self.__root_node)

    def __curr_level(self):
        return self.__father_node.val.level + 1

    def __pop_till(self, level):
        assert level <= self.__curr_level()
        while True:
            curr_level = self.__curr_level()
            if curr_level == level:
                return

            self.__father_node = self.__father_node.father


class Fragment:

    magic_tree: MagicTree

    def __init__(self):
        self.magic_tree_builder = MagicTreeBuilder()
        self.magic_tree = None

    def finish(self):
        self.magic_tree = self.magic_tree_builder.build()

    def handle_magic(self, magic):
        self.magic_tree_builder.feed_magic(magic)

    def print(self):
        self.magic_tree.print()


class MagicFragmentHandler:

    fragment: Fragment

    def __init__(self):
        self.fragment = None

    def process_line(self, line: str):
        if line.startswith('#'):
            self.__process_comment_line(line)
        elif line.startswith('!'):
            self.__process_attr_line(line)
        elif 0 < len(line):
            self.__process_magic_line(line)
        else:
            print()

    def finish(self):
        if self.fragment is not None:
            self.fragment.finish()

    def print(self):
        self.fragment.print()

    def __process_comment_line(self, line: str):
        pass

    def __process_attr_line(self, line: str):
        pass

    def __process_magic_line(self, line: str):
        magic = Magic().parse(line)
        if 0 == magic.level:
            if self.fragment is not None:
                self.fragment.finish()
            self.fragment = Fragment()
        self.fragment.handle_magic(magic)


def parse_magic_fragment_file(magic_fragment_file: str):
    handler = MagicFragmentHandler()
    with open(magic_fragment_file, 'r') as file:
        for line in file.readlines():
            handler.process_line(line[:-1])
        handler.finish()
    return handler


def main():
    handler = parse_magic_fragment_file(r'E:\projects\cpp\file-ret-type\magic\Magdir\adi')
    handler.print()


if __name__ == '__main__':
    main()
