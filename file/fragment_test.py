from typing import List

from file.magic import Magic


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
        for i, prev_magic in enumerate(prev_magics):
            if prev_magic.offset == magic.offset and \
                    prev_magic.type == magic.type:

                if abs(prev_magic.level-magic.level) > 1:
                    if not magic.can_after(prev_magic):
                        print(prev_magic, prev_magic.line_no)
                        print(magic, magic.line_no)
                        print()
                break
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
        magic = Magic().parse(line, line_no)
        if 0 == magic.level:
            if self.fragment is not None:
                self.fragment.finish()
            self.fragment = TestFragment()
        self.fragment.handle_magic(magic)
