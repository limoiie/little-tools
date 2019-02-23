import abc
import re
from typing import List, Dict

from file.fragment import MagicTreeBuilder, TreeNode, MagicTree
from file.magic import Magic, parse_magic, have_same_test_method, join_magic_desc, Test
from file.op_intersect import are_mutex, is_lhv_contain_rhv, str_to_int
from file.type_record import TypeDatabase, print_all_info


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
                if magic.test.always_true() or prev_magic.test.always_true():
                    continue
                if magic.type.type == prev_magic.type.type == 'string':
                    continue
                if magic.test.op == '=' and prev_magic.test.op == '=':
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

    @staticmethod
    def build():
        return None


class Fragment(abc.ABC):

    def __init__(self):
        self.file_name = ''

    @abc.abstractmethod
    def finish(self):
        pass

    @abc.abstractmethod
    def handle_magic(self, magic):
        pass

    @abc.abstractmethod
    def is_name_fragment(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def get_name(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def print(self):
        pass

    @abc.abstractmethod
    def root(self):
        pass

    def set_file_name(self, file_name: str):
        self.file_name = file_name

    def get_file_name(self):
        return self.file_name


class TestFragment(Fragment):

    def __init__(self):
        super().__init__()
        self.feature_extractor = FeatureExtractor()

    def finish(self):
        self.feature_extractor.build()

    def handle_magic(self, magic):
        self.feature_extractor.feed_magic(magic)

    def is_name_fragment(self):
        raise NotImplementedError()

    def get_name(self):
        pass

    def print(self):
        pass

    def root(self):
        return None


class FilterFragment(Fragment):

    valid_count = 0
    other_count = 0

    def __init__(self):
        super().__init__()
        self.lines = []
        self.prev_level = -1
        self.peak_num = 0

    def finish(self):
        if self.peak_num > 2:
            FilterFragment.valid_count += 1
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

    def is_name_fragment(self):
        raise NotImplementedError()

    def get_name(self):
        pass

    def print(self):
        if self.peak_num > 2:
            for line in self.lines:
                print(line)
            print()
            print()
        pass

    def root(self):
        return None


def magic_mutex(magic: Magic, prev: Magic):
    # print('test mutex', magic, prev)
    if magic.type.is_default():
        return True

    if prev.type.is_functional() or \
            magic.type.is_functional():
        return False

    if prev.test.always_true() or \
            magic.test.always_true():
        return False

    if not have_same_test_method(magic, prev):
        return False

    if magic.type.is_text() and prev.type.is_text():
        return down_cast_to_byte(magic.test, magic.type, prev.test, prev.type, are_mutex)

    return are_mutex(prev.test, magic.test, magic.type)


def down_cast_to_byte(test1, type1, test2, type2, func):
    if (type1.is_string() and type2.is_string()) or \
            (type1.is_byte() and type2.is_byte()):
        return func(test1, test2, type1)

    if type1.is_string() and type2.is_byte():
        magic_type_c = test1.val[0]
        prev_type_c = chr(str_to_int(test2.val))
    else:
        magic_type_c = chr(str_to_int(test1.val))
        prev_type_c = test2.val[0]

    magic_byte_test = Test()
    magic_byte_test.op = test1.op
    magic_byte_test.val = magic_type_c

    prev_byte_test = Test()
    prev_byte_test.op = test2.op
    prev_byte_test.val = prev_type_c

    return func(magic_byte_test, prev_byte_test, type1)


class PrintNameFragment(Fragment):

    count = 0
    all_type = set()

    def __init__(self):
        super().__init__()
        self.name = ''
        self.is_name = False
        self.magic_tree_builder = MagicTreeBuilder()
        self.magic_tree = None
        self.lines = []
        self.prev_level = -1
        self.peak_num = 0

    def finish(self):
        self.magic_tree = self.magic_tree_builder.build()
        reduce_magic_tree(self.magic_tree)

        if self.is_name:
            PrintNameFragment.count += 1

    def handle_magic(self, magic):
        if not self.is_name and magic.is_name():
            self.name = magic.get_name()
            self.is_name = True

        self.magic_tree_builder.feed_magic(magic)

        has_peak = magic.level < self.prev_level
        if has_peak:
            self.peak_num += 1
        self.lines.append(magic.line)
        self.prev_level = magic.level

    def is_name_fragment(self):
        return self.is_name

    def get_name(self):
        return self.name

    def print(self):
        print_magic_tree(self.root())
        print()
        print()
        pass

    def root(self):
        return self.magic_tree.root


class PrintFragment(Fragment):

    magic_tree: MagicTree

    valid_count = 0
    other_count = 0

    def __init__(self):
        super().__init__()
        self.magic_tree_builder = MagicTreeBuilder()
        self.magic_tree = None
        self.lines = []
        self.prev_level = -1
        self.peak_num = 0

    def finish(self):
        self.magic_tree = self.magic_tree_builder.build()

        if self.peak_num > 2:
            PrintFragment.valid_count += 1
        else:
            PrintFragment.other_count += 1

    def handle_magic(self, magic):
        self.magic_tree_builder.feed_magic(magic)

        has_peak = magic.level < self.prev_level
        if has_peak:
            self.peak_num += 1
        self.lines.append(magic.line)
        self.prev_level = magic.level

    def is_name_fragment(self):
        return self.magic_tree.root.val.is_name()

    def get_name(self):
        return self.magic_tree.root.val.get_name()

    def print(self):
        if self.peak_num > 2:
            if self.magic_tree.root.val.is_name():
                print('name case:', self.magic_tree.root.val)
            else:
                print_magic_tree(self.root())
                print()
                print()
        # if self.peak_num < 3:
        #     return
        # if self.magic_tree.root.val.type.is_name():
        #     print('name case:', self.magic_tree.root.val)
        # else:
        #     print_magic_tree(self.magic_tree)
        #     print()
        #     print()

    def root(self):
        return self.magic_tree.root


class TestFragmentHandler:

    fragment: Fragment
    fragments: List[Fragment]
    name_fragments: Dict[str, Fragment]
    normal_fragments: List[Fragment]

    def __init__(self):
        self.file_name = ''
        self.fragment = None
        self.fragments = []
        self.name_fragments = dict()
        self.normal_fragments = []

    def process_line(self, file_name, line: str, line_no: int):
        if line.startswith('#'):
            # print()
            pass
        elif line.startswith('!'):
            # print()
            pass
        elif 0 < len(line):
            self.__process_magic_line(file_name, line, line_no)
        else:
            # print(line)
            pass

    def __process_magic_line(self, file_name: str, line: str, line_no: int):
        magic = parse_line_to_magic(line, line_no)
        if 0 == magic.level:
            self.__finish_fragment_and_append()
            self.__create_new_fragment(file_name)
        magic.file_name = self.fragment.get_file_name()
        self.fragment.handle_magic(magic)

    def __create_new_fragment(self, file_name: str):
        self.fragment = PrintNameFragment()
        self.fragment.set_file_name(file_name)

    def finish(self):
        self.__finish_fragment_and_append()
        self.__pick_out_name_fragments()
        for fragment in self.fragments:
            self.__render_node_recursively(fragment.root())

    def __finish_fragment_and_append(self):
        if self.fragment is not None:
            self.fragment.finish()
            self.fragments.append(self.fragment)

    def __pick_out_name_fragments(self):
        self.name_fragments.clear()
        self.normal_fragments.clear()

        for fragment in self.fragments:
            if fragment.is_name_fragment():
                self.name_fragments[fragment.get_name()] = fragment
            else:
                self.normal_fragments.append(fragment)

    def __render_node_recursively(self, node: TreeNode):
        magic = node.val
        if magic.is_use():
            name_fragment = self.name_fragments[magic.get_name()]
            node.children.insert(0, name_fragment.root())
        else:
            for child in node.children:
                self.__render_node_recursively(child)

    def print(self):
        for fragment in self.normal_fragments:
            fragment.print()

        print()
        PrintNameFragment.all_type = sorted(PrintNameFragment.all_type)
        print('NUM OF ALL TYPE: ', len(PrintNameFragment.all_type))
        for candidate_type in PrintNameFragment.all_type:
            print(candidate_type)

        print_all_info()
        TypeDatabase.instance.dump()


def parse_line_to_magic(line: str, line_no):
    magic = parse_magic(line)
    magic.line_no = line_no
    return magic


def print_magic_tree(tree_root: TreeNode):
    explorer_and_print('', tree_root, set())


def reduce_magic_tree(tree_root: MagicTree):
    reduce_node(tree_root.root)


def reduce_node(node: TreeNode):
    if len(node.children) > 1:
        if not node.children[0].val.test.always_true():
            if does_first_child_contain_remainder(node.children):
                merge_first_child_with_each_child(node.children)

    for child in node.children:
        if have_same_test_method(child.val, node.val) and \
                is_lhv_contain_rhv(child.val.test, node.val.test, node.val.type):
            child.val.test.set_always_true()

        reduce_node(child)


def merge_first_child_with_each_child(children: List[TreeNode]):
        desc = children[0].val.desc
        # children[0].val.desc = ''
        children[0].val.test.set_always_true()

        for child in children[1:]:
            child.val.desc = join_magic_desc(desc, child.val.desc) + '; @reduced@'


def does_first_child_contain_remainder(children: List):
    first_child = children[0]

    if first_child.val.test.always_true():
        return True

    for child in children[1:]:
        if child.children:
            # child should have no child (simplify problem)
            return False

        if child.val.test.always_true():
            return False

        if not have_same_test_method(child.val, first_child.val):
            return False

        if first_child.val.type.is_text() and child.val.type.is_text():
            if not down_cast_to_byte(first_child.val.test, first_child.val.type,
                                     child.val.test, child.val.type,
                                     is_lhv_contain_rhv):
                return False
        elif not is_lhv_contain_rhv(first_child.val.test, child.val.test, child.val.type):
            return False
    return True


def explorer_and_print(prefix: str, node: TreeNode, use_history: set):
    is_use, is_already_visited = visit_if_call_use(node, use_history)
    if is_already_visited:
        return

    prefix = join_magic_desc(prefix, node.val.desc)
    # print(node.val.line, ' ' * 20, '\t\t', prefix, 'explorer', always_true_n, len(node.children))
    print(node.val.line, ' ' * 20, '\t\t', '@%s@' % prefix, '$explorer$')

    if len(prefix) > 1 and prefix != '&&':
        # PrintNameFragment.all_type.add(prefix + ' `%s`: %d' % (fragment.file_name, node.val.line_no))
        PrintNameFragment.all_type.add(prefix)
        record = TypeDatabase.new_record(
            node.val.file_name, node.val.line_no, prefix)
        TypeDatabase.instance.put_record(record)

    always_true_n = count_always_true_in_front(node.children)
    is_mutual_exclude, idx_block_end = \
        find_max_mutual_exclusion_block(node.children, always_true_n)

    mutual_exclude_switch_string = ''
    if is_mutual_exclude:
        if idx_block_end + 1 < len(node.children):
            # last_magic_in_block: Magic = node.children[idx_block_end-1].val
            magic_next_block: Magic = node.children[idx_block_end].val
            if magic_next_block.test.always_true():
                if can_desc_follow_behind_mutual_block(prefix, magic_next_block):
                    # if not prefix:
                    #     prefix = '&ignored&'
                    merge_always_true_tail_into_prev_mutual_block(
                        node.children[always_true_n:idx_block_end], magic_next_block)

        for i in range(always_true_n, idx_block_end):
            mutual_exclude_switch_string += node.children[i].val.desc
    mutual_exclude_switch_string = '&%s&' % ''

    # if no switch in curr level, and if the first child looks like a title
    # use it as the prefix
    if len(node.children) > 1 and not is_mutual_exclude and not prefix:
        possible_type = node.children[0].val.desc
        if most_like_a_type(possible_type):
            prefix = possible_type

    if is_use:
        print('[')

    followed_trivial = False
    for i, child in enumerate(node.children):
        is_trivial = followed_trivial or trivial_desc(prefix, child.val)
        if not is_trivial:
            use_fragment_most_likely_be_addition = \
                child.val.is_use() and (len(prefix) > 15 or (is_mutual_exclude and i >= idx_block_end))

            if not use_fragment_most_likely_be_addition:
                printed = False
                if (is_mutual_exclude and i < idx_block_end) or not prefix:
                    # print('explorer caused: ', i, idx_block_end, prefix)
                    explorer_and_print(prefix, child, use_history)
                    printed = True

                # if there is no prefix, take the desc of front always true node as
                # default prefix
                if not prefix:
                    if i < always_true_n:
                        prefix = join_magic_desc(prefix, node.children[i].val.desc)
                    elif i + 1 == idx_block_end:
                        last_magic: Magic = node.children[i].val
                        if last_magic.is_default():
                            prefix = '&&'

                if printed:
                    continue
        else:
            if i >= idx_block_end:
                followed_trivial = True

        # print('just caused: ', prefix, is_mutual_exclude, i, idx_block_end, is_trivial)
        if is_mutual_exclude and i >= idx_block_end:
            just_print(mutual_exclude_switch_string, child, use_history)
        else:
            just_print(prefix, child, use_history)
    pass

    if is_use:
        print(']')


def just_print(string: str, node: TreeNode, use_history: set):
    is_use, is_already_visited = visit_if_call_use(node, use_history)
    if is_use:
        print('JUMP OUT USE SINCE WE ARE JUST', node.val.get_name())
        return

    print(node.val.line, ' ' * 20, '\t\t', '@%s@' % string, '$just$')
    # print(node.val.line, ' ' * 20, '\t\t', string)

    if len(string) > 1 and string != '&&':
        # PrintNameFragment.all_type.add(string + ' `%s`: %d' % (fragment.file_name, node.val.line_no))
        PrintNameFragment.all_type.add(string)
        record = TypeDatabase.new_record(
            node.val.file_name, node.val.line_no, string)
        TypeDatabase.instance.put_record(record)

    if is_use:
        print('[')
    for child in node.children:
        just_print(string, child, use_history)

    if is_use:
        print(']')


def visit_if_call_use(node: TreeNode, use_history: set):
    is_use = False
    is_already_visited = False

    if node.val.is_use():
        is_use = True
        print('USE ', node.val.get_name())
        if node.val.get_name() in use_history:
            is_already_visited = True
        else:
            is_already_visited = False
            use_history.add(node.val.get_name())
    return is_use, is_already_visited


def count_always_true_in_front(children: List):
    for i, child in enumerate(children):
        if child.val.test.always_true():
            continue
        return i
    return len(children)


def find_max_mutual_exclusion_block(children: List, start: int):
    children_num = len(children)

    if children_num - start == 1:
        return True, 1

    end = start-1
    for i in range(start + 1, children_num):
        for j in range(start, i):
            if not magic_mutex(children[i].val, children[j].val):
                break
        else:
            end = i
            continue
        break

    end += 1

    if children_num - start == 2:
        is_mutual_exclude = (end == start + 2)
    else:
        is_mutual_exclude = end >= start + 2
    return is_mutual_exclude, end


def merge_always_true_tail_into_prev_mutual_block(mutual_block, always_true_tail):
    desc = always_true_tail.desc
    for node in mutual_block:
        magic = node.val
        magic.desc = join_magic_desc(magic.desc, desc)
    always_true_tail.desc = ''
    pass


def can_desc_follow_behind_mutual_block(prefix, magic_next_block):
    desc = magic_next_block.desc
    is_trivial = trivial_desc(prefix, magic_next_block)
    if not is_trivial:
        if '%' in desc and ':' in desc:
            return False
        return True
    return False


def trivial_desc(prefix: str, magic: Magic):
    desc = magic.desc

    if not desc:
        return False

    desc_source_len = len(desc)
    prefix_len = len(prefix)

    if 0 == prefix_len:
        if desc.startswith(r'\b, ') or desc[0] in r',;':
            return True
        if desc[0] == r'(' and desc[-1] == r')':
            return True
    #     if '%' in desc:
    #         return True

    # if desc_source_len > prefix_len:
    #     return False

    desc = desc.lower()

    if '%' in desc:
        if desc.startswith(r'\b, ') or desc[0] in r',;':
            return True

        desc = desc.replace(r'version', '')
        desc = desc.replace(r'level', '')
        desc = desc.replace(r'from', '')
        desc = desc.replace(r'size', '')
        desc = desc.replace(r'name', '')
        desc = desc.replace(r'byte', '')
        desc = desc.replace(r'title', '')
        desc = desc.replace(r'theme', '')
        desc = desc.replace(r'for', '')
        desc = desc.replace(r'length', '')
        # desc = desc.replace(r'format', '')
        desc = desc.replace(r'bit', '')
        desc = desc.replace(r'dpi', '')
        desc = desc.replace(r'inodes', '')
        desc = desc.replace(r'blocks', '')
        desc = desc.replace(r'pixels', '')
        desc = desc.replace(r'date', '')
        desc = desc.replace(r'unused', '')

    desc = desc.replace(r': ', '')
    desc = desc.replace(r'.', '')
    desc = desc.replace(r',', '')
    desc = desc.replace(r'=', '')

    matched = re.search(r'(%-?[\d]*\.*[\d]*\w)', desc)
    if matched:
        desc = desc.replace(matched.group(1), '')

    # print(magic, 'desc: ', desc)

    desc_reduce_len = len(desc)
    return desc_reduce_len * 1.5 < desc_source_len


def most_like_a_type(string: str):
    if not string or not string[0].isalpha():
        return False
    if r'%' not in string:
        return len(string) > 5
    return len(string) > 10
