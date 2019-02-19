from kanren import *
from pyDatalog import pyDatalog


def test_py_data_log():
    pass


def test():
    from kanren import lany, membero
    x = var('x')
    g = lany(membero(x, (1, 2, 3)), membero(x, (2, 3, 4)))
    print(tuple(g({})))


if __name__ == '__main__':
    test_py_data_log()
