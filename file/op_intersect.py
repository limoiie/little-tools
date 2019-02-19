def str_to_int(string):
    if isinstance(string, int):
        return string
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
        val1 = str_to_int(val1)
        val2 = str_to_int(val2)
        return val1 > val2 + 1
    if op2 == '&':
        val1 = str_to_int(val1)
        val2 = str_to_int(val2)
        return val1 > val2
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


def test_intersect_equal():
    assert intersect_with_equal(10, '<', 9) is False
    assert intersect_with_equal(10, '<', 10) is False
    assert intersect_with_equal(10, '<', 11) is True

    assert intersect_with_equal(10, '!', 9) is True
    assert intersect_with_equal(10, '!', 10) is False
    assert intersect_with_equal(10, '!', 11) is True

    assert intersect_with_equal(10, '>', 9) is True
    assert intersect_with_equal(10, '>', 10) is False
    assert intersect_with_equal(10, '>', 11) is False

    assert intersect_with_equal(11, '&', 12) is False
    assert intersect_with_equal(11, '&', 10) is True
    assert intersect_with_equal(11, '&', 11) is True


def test_intersect_lt():
    assert intersect_with_lt(10, '>', 8, 'uint') is True
    assert intersect_with_lt(10, '>', 9, 'uint') is False
    assert intersect_with_lt(10, '>', 10, 'uint') is False
    assert intersect_with_lt(10, '>', 11, 'uint') is False

    assert intersect_with_lt(10, '&', 8, 'uint') is True
    assert intersect_with_lt(10, '&', 9, 'uint') is True
    assert intersect_with_lt(10, '&', 10, 'uint') is False
    assert intersect_with_lt(10, '&', 11, 'uint') is False


if __name__ == '__main__':
    test_intersect_equal()
    test_intersect_lt()
