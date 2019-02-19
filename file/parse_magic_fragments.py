import re
from typing import List

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
        elif seq[0].isalpha():
            self.op = r'='
            self.val = seq
        else:
            self.op = seq[0]
            self.val = seq[1:]
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


def reduce():
    pass


def dump(node: TreeNode):
    magic = node.val

    string = magic.desc
    for child in node.children:
        string += ' ' + dump(child)

    empty_desc = 0 == len(magic.desc)
    if empty_desc:
        return string[1:]

    for sub_test in magic.tests:
        if not sub_test.always_true():
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


class SimpleQueue:

    container: List[Magic]

    def __init__(self, max_size=5):
        self.max_size = max_size
        self.cursor = 0
        self.size = 0
        self.container = [None] * max_size

    def push(self, item):
        self.container[self.cursor] = item
        self.cursor = (self.cursor + 1) % self.max_size
        self.size = min(self.size + 1, self.max_size)

    def snapshot(self):
        if self.size < self.max_size:
            return self.container[:self.cursor]
        return self.container[self.cursor:] + self.container[:self.cursor]


class FeatureExtractor:

    def __init__(self):
        self.magic_queue = SimpleQueue(max_size=5)

    def feed_magic(self, magic):
        prev_magics = self.magic_queue.snapshot()
        for i, prev_magic in enumerate(prev_magics):
            if prev_magic.offset == magic.offset and \
                    prev_magic.type == magic.type:
                print(magic, i)
                break
        else:
            print()

        self.magic_queue.push(magic)

    def build(self):
        return None


class Fragment:

    magic_tree: MagicTree

    def __init__(self):
        self.feature_extractor = FeatureExtractor()
        # self.magic_tree_builder = MagicTreeBuilder()
        self.magic_tree = None

    def finish(self):
        # self.magic_tree = self.magic_tree_builder.build()
        self.feature_extractor.build()

    def handle_magic(self, magic):
        # self.magic_tree_builder.feed_magic(magic)
        self.feature_extractor.feed_magic(magic)

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
