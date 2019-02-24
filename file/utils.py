import re


def convert_desc_to_var_name(desc: str):
    desc = replace_format_tmpl_with_upper_type(desc)
    desc = replace_non_alpha_non_digit_with_space(desc)
    non_empty_sub_string = split_to_non_empty_sub_strings(desc)
    candidate_name = '_'.join(non_empty_sub_string)
    return insert_an_a_if_start_with_number(candidate_name)


def replace_format_tmpl_with_upper_type(desc: str):
    matched = re.search(r'(%-?[\d]*\.*[\d]*\w)', desc)
    if matched:
        tmpl = matched.group(1)
        type_name = tmpl[-1].upper() * 2
        desc = desc.replace(tmpl, type_name)
    return desc


def replace_non_alpha_non_digit_with_space(desc: str):
    var_name = ''
    for c in desc:
        if c.isalpha():
            var_name += c.upper()
        elif c.isdigit():
            var_name += c
        elif c == '+':
            var_name += 'P'
        else:
            var_name += ' '
    return var_name


def split_to_non_empty_sub_strings(string: str):
    sub_strings = string.split(' ')
    non_empty_sub_strings = []
    for string in sub_strings:
        if string:
            non_empty_sub_strings.append(string)
    return non_empty_sub_strings


def insert_an_a_if_start_with_number(string: str):
    if string[0].isdigit():
        return 'A_' + string
    return string