from typing import List

from file.fragment import MagicTree, MagicTreeBuilder, TreeNode, MagicTree
from file.magic import Magic, parse_magic, have_same_test_method
from file.op_intersect import are_mutex, is_lhv_contain_rhv


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
        prev_magics.reverse()

        # if not magic.desc:
        #     print(magic, magic.line_no)
        # else:
        for i, prev_magic in enumerate(prev_magics):
            # if prev_magics and not prev_magics[0].desc:
            #     print(magic, magic.line_no)
            #     break
            # if prev_magic.offset == magic.offset and \
            #         prev_magic.type == magic.type:
            #
            #     if abs(prev_magic.level-magic.level) > 1:
            #         if not magic.can_after(prev_magic):
            #             print(prev_magic, prev_magic.line_no)
            #             print(magic, magic.line_no)
            #             print()
            #     break
            if '&' in prev_magic.offset or '&' in magic.offset:
                continue

            if prev_magic.offset == magic.offset and \
                    prev_magic.type != magic.type:
                if magic.type.is_functional() or prev_magic.type.is_functional():
                    continue
                if magic.tests[0].always_true() or prev_magic.tests[0].always_true():
                    continue
                if magic.type.type == prev_magic.type.type == 'string':
                    continue
                if magic.tests[0].op == '=' and prev_magic.tests[0].op == '=':
                    if magic.type.type != 'regex' and prev_magic.type.type != 'regex':
                        continue

                if not magic.type.op and not prev_magic.type.op:
                    # consider it as must excluded
                    continue

                if magic.level > prev_magic.level:
                    for k in range(i):
                        if prev_magics[k].level <= prev_magic.level:
                            break
                    else:
                        continue

                print(prev_magic, prev_magic.line_no)
                print(magic, magic.line_no)
                print()
        # else:
        #     print()

        self.magic_queue.push(magic)

    def build(self):
        return None


class TestFragment:

    def __init__(self):
        self.feature_extractor = FeatureExtractor()

    def finish(self):
        self.feature_extractor.build()

    def handle_magic(self, magic):
        self.feature_extractor.feed_magic(magic)

    def print(self):
        pass


class FilterFragment:

    valid_count = 0
    other_count = 0

    def __init__(self):
        self.lines = []
        self.prev_level = -1
        self.peak_num = 0

    def finish(self):
        if self.peak_num > 2:
            FilterFragment.valid_count += 1
            for line in self.lines:
                print(line)
            print()
            print()
        else:
            FilterFragment.other_count += 1

        # print('valid: %d, other: %d, peak_num: %d' %
        #       (FilterFragment.valid_count, FilterFragment.other_count, self.peak_num))

    def handle_magic(self, magic):
        has_peak = magic.level < self.prev_level
        if has_peak:
            self.peak_num += 1
        self.lines.append(magic.line)
        self.prev_level = magic.level

    def print(self):
        pass


def can_after(magic, prev):
    if magic.type.is_default():
        return False

    if prev.type.is_functional() or \
            magic.type.is_functional():
        return True

    if not have_same_test_method(magic, prev):
        return True

    for prev_test in prev.tests:
        if prev_test.always_true():
            continue
        for curr_test in magic.tests:
            if curr_test.always_true():
                continue
            if are_mutex(prev_test, curr_test, magic.type):
                return False
    return True


def just_print(string: str, node: TreeNode):
    print(node.val.line, ' ' * 20, '\t\t', string)
    for child in node.children:
        just_print(string, child)


def explorer_and_print(prefix: str, node: TreeNode):
    prefix += ' ' + node.val.desc

    print(node.val.line, ' ' * 20, '\t\t', prefix)
    is_mutual_exclude = True
    children_num = len(node.children)
    for i in range(children_num):
        j = i + 1
        while j < children_num:
            if node.children[i].val.can_after(node.children[j].val):
                is_mutual_exclude = False
                break
            j += 1

    for child in node.children:
        if is_mutual_exclude or not node.val.desc:
            explorer_and_print(prefix, child)
        else:
            just_print(prefix, child)
    pass


def print_magic_tree(tree_root: MagicTree):
    reduce_magic_tree(tree_root)
    explorer_and_print('', tree_root.root)


def reduce_node(node: TreeNode):
    if node.val.tests[0].val == '0x29':
        x = 10
    for child in node.children:
        if have_same_test_method(child.val, node.val):
            if is_lhv_contain_rhv(node.val.tests[0], child.val.tests[0], node.val.type):
                child.val.tests[0].op = 'x'
                child.val.tests[0].val = ''

        reduce_node(child)


def reduce_magic_tree(tree_root: MagicTree):
    reduce_node(tree_root.root)


class PrintFragment:

    magic_tree: MagicTree

    valid_count = 0
    other_count = 0

    def __init__(self):
        self.magic_tree_builder = MagicTreeBuilder()
        self.magic_tree = None
        self.lines = []
        self.prev_level = -1
        self.peak_num = 0

    def finish(self):
        self.magic_tree = self.magic_tree_builder.build()

        if self.peak_num > 2:
            PrintFragment.valid_count += 1

            if self.magic_tree.root.val.type.is_name():
                print('name case:', self.magic_tree.root.val)
            else:
                print_magic_tree(self.magic_tree)
                print()
                print()
        else:
            PrintFragment.other_count += 1

    def handle_magic(self, magic):
        self.magic_tree_builder.feed_magic(magic)

        has_peak = magic.level < self.prev_level
        if has_peak:
            self.peak_num += 1
        self.lines.append(magic.line)
        self.prev_level = magic.level

    def print(self):
        pass
        # if self.peak_num < 3:
        #     return
        # if self.magic_tree.root.val.type.is_name():
        #     print('name case:', self.magic_tree.root.val)
        # else:
        #     print_magic_tree(self.magic_tree)
        #     print()
        #     print()


class TestFragmentHandler:

    fragment: TestFragment

    def __init__(self):
        self.fragment = None

    def process_line(self, line: str, line_no: int):
        if line.startswith('#'):
            # print()
            pass
        elif line.startswith('!'):
            # print()
            pass
        elif 0 < len(line):
            self.__process_magic_line(line, line_no)
        else:
            # print(line)
            pass

    def finish(self):
        if self.fragment is not None:
            self.fragment.finish()

    def print(self):
        if self.fragment is not None:
            self.fragment.print()

    def __process_magic_line(self, line: str, line_no: int):
        magic = parse_magic(line)
        magic.line_no = line_no
        magic.line = line
        if 0 == magic.level:
            if self.fragment is not None:
                self.fragment.finish()
            self.fragment = PrintFragment()
        self.fragment.handle_magic(magic)
