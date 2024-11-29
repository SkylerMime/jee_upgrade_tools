import pathlib

# Reformat the given file according to my rules
def reformat_file(file_path: str):
    file_data = ""

    with open(file_path, encoding="UTF-8") as old_file:
        file_data = old_file.read()
        if file_path.endswith(".xhtml"):
            file_data = ui_g_to_p_grid(file_data)
        elif file_path.endswith(".java"):
            file_data = resolve_object_util_deprecation(file_data)
        
    file_to_rem = pathlib.Path(file_path)
    file_to_rem.unlink()

    with open(file_path, mode="x", encoding="UTF-8") as old_file:
        old_file.write(file_data)


# Replace old ui-g style classes
def ui_g_to_p_grid(old_file: str):
    """
    >>> ui_g_to_p_grid('    <div class="ui-g-12 ui-sm-12 ui-md-8 ui-lg-6 ui-xl-3">')
    '    <div class="p-col-12 p-sm-12 p-md-8 p-lg-6 p-xl-3">'
    """
    last_change = old_file
    result = last_change
    while result is not None:
        last_change = result
        result = _replace_ui_g_element(last_change)
    result = last_change
    while result is not None:
        last_change = result
        result = _replace_ui_num_element(last_change)
    return last_change

def _replace_ui_g_element(old_file: str):
    """
    >>> _replace_ui_g_element('<div class="ui-g-8 ui-md-6">')
    '<div class="p-col-8 ui-md-6">'
    """
    first_part, _, last_part = old_file.partition("ui-g")
    if last_part == "":
        return None
    elif last_part[0] == '-':
        # This is a length element like ui-g-12, not the grid definition ui-g.
        return f'{first_part}p-col{last_part}'
    else:
        return f'{first_part}p-grid{last_part}'
    
def _replace_ui_num_element(old_file: str):
    """
    >>> _replace_ui_num_element('<div class="ui-lg-5">')
    '<div class="p-lg-5">'
    """
    first_part, _, last_part = old_file.partition("ui-")
    if last_part == "":
        return None
    return f'{first_part}p-{last_part}'


# Replace ObjectUtils with Objects
def resolve_object_util_deprecation(old_file: str):
    last_change = old_file
    result = last_change
    while result is not None:
        last_change = result
        result = _replace_object_util_call(last_change)
    result = last_change
    while result is not None:
        last_change = result
        result = _replace_object_util_import(last_change)
    return last_change

def _replace_object_util_import(old_file: str):
    first_part, _, last_part = old_file.partition("org.apache.commons.lang3.ObjectUtils")
    if last_part == "":
        return None
    return f'{first_part}java.util.Objects{last_part}'

def _replace_object_util_call(old_file: str):
    """
    >>> _replace_object_util_call('test.add("First " + ObjectUtils.toString(exampleVariable.method()));')
    'test.add("First " + Objects.toString(exampleVariable.method(), ""));'
    """
    first_part, _, last_part = old_file.partition("org.apache.commons.lang3.ObjectUtils.toString")
    if last_part == "":
        first_part, _, last_part = old_file.partition("ObjectUtils.toString")
        if last_part == "":
            return None
    after_objects_before_close, last_close = _split_at_close_parentheses(last_part)
    return f'{first_part}Objects.toString{after_objects_before_close}, ""{last_close}'

def _split_at_close_parentheses(parentheses_string: str):
    """
    >>> _split_at_close_parentheses("(example()).extra()")
    ('(example()', ').extra()')
    """
    assert parentheses_string[0] == "("
    uncanceled_parentheses = 1
    last_right_parenthesis_index = -1
    for index, char in enumerate(parentheses_string[1:]):
        if char == "(":
            uncanceled_parentheses += 1
        elif char == ")":
            uncanceled_parentheses -= 1
            last_right_parenthesis_index = index

        if uncanceled_parentheses == 0:
            return parentheses_string[:last_right_parenthesis_index + 1], parentheses_string[last_right_parenthesis_index + 1:]
    
    raise AssertionError("Balanced parentheses not found")
