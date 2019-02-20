from typing import List, Any

from file.magic import Magic, parse_magic


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
        if not sub_test.always_true():
            return '[%s]' % string

    # always true
    return string


def print_tree(node: TreeNode):
    print(node.val)

    for child in node.children:
        print_tree(child)


class MagicTree:

    root: TreeNode

    def __init__(self, root):
        self.root = root

    def print(self):
        # print(dump(self.root))
        # print_tree(self.root)
        pass


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

    def process_line(self, line: str, line_no: int):
        if line.startswith('#'):
            self.__process_comment_line(line)
        elif line.startswith('!'):
            self.__process_attr_line(line)
        elif 0 < len(line):
            self.__process_magic_line(line, line_no)
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

    def __process_magic_line(self, line: str, line_no: int):
        magic = parse_magic(line)
        magic.line_no = line_no
        print(magic)
        print(line)
        print()
        if 0 == magic.level:
            if self.fragment is not None:
                self.fragment.finish()
            self.fragment = Fragment()
        self.fragment.handle_magic(magic)
