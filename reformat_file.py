import sys
from pathlib import Path
from collections.abc import Callable
from typing import List, Self
import re


class HtmlElement:
    def __init__(self, full: str) -> None:
        self.full = full

    def noWhitespace(self) -> str:
        """
        >>> newElem = HtmlElement("  \t   <first>")
        >>> newElem.noWhitespace()
        '<first>'
        """
        return self.full.strip("\n\t\r ")

    def close(self) -> str:
        """
        >>> newElem = HtmlElement("<first>")
        >>> newElem.close()
        '<first />'
        """
        first, _, _ = self.full.partition(">")
        return f"{first} />"

    def isOpen(self) -> bool:
        return not self.isClose()

    def isClose(self) -> bool:
        """
        >>> newElem = HtmlElement("<first>")
        >>> newElem.isClose()
        False
        >>> newElem = HtmlElement("</second>")
        >>> newElem.isClose()
        True
        """
        return self.noWhitespace().startswith("</")

    def name(self) -> str:
        """
        >>> newElem = HtmlElement("<test class='Hello'>")
        >>> newElem.name()
        'test'

        >>> newElem = HtmlElement("</test>")
        >>> newElem.name()
        'test'
        """
        _, _, last = self.noWhitespace().partition("<")
        if last[0] == "/":
            last = last[1:]
        end_of_name_index = min(last.find(" "), last.find(">"))
        return last[:end_of_name_index]

    def pairs_with(self, other: Self) -> bool:
        """
        >>> firstElem = HtmlElement("<test class='Hello'>")
        >>> secondElem = HtmlElement("</test>")
        >>> firstElem.pairs_with(secondElem)
        True
        """
        return self.name() == other.name() and self.isOpen() and other.isClose()


# Run the reformatter on the given file
def main():
    if len(sys.argv) > 1:
        file_path = Path(sys.argv[1])
        full_mode = False
        if len(sys.argv) > 2:
            full_mode = sys.argv[2] == "-f" or sys.argv[2] == "--full"
        print(f"Reformatting file {file_path}.")
        try:
            reformat_file(file_path, full_mode)
            print("Done.")
        except FileNotFoundError:
            print(f"fatal: File {file_path} not found.")
    else:
        print("Usage: python reformat_file.py file_path [-f | --full].")
        print("fatal: Missing argument 'file_path'.")


# Reformat the given file according to my rules
def reformat_file(file_path: Path, full_mode: bool = False):
    file_to_reformat: Path = Path(file_path)
    if file_to_reformat.is_dir():
        for nested_file in file_to_reformat.iterdir():
            reformat_file(nested_file)
    elif file_to_reformat.is_file():

        file_data = ""

        with file_path.open(encoding="UTF-8") as old_file:
            file_data = old_file.read()
            if file_path.name.endswith(".xhtml"):
                if full_mode:
                    file_data = ui_g_to_p_grid(file_data)
                file_data = shorthand_close_xhtml_elements(file_data)
            elif file_path.name.endswith(".java"):
                file_data = resolve_object_util_deprecation(file_data)
                file_data = resolve_raw_tabchange(file_data)
                file_data = resolve_raw_events(file_data)
                file_data = resolve_primitive_constructors(file_data)
                file_data = resolve_bigdecimal_constants(file_data)

        file_to_rem = Path(file_path)
        file_to_rem.unlink()

        with file_path.open(mode="x", encoding="UTF-8") as old_file:
            old_file.write(file_data)
    elif not file_to_reformat.exists():
        raise FileNotFoundError()


def _replace_all(
    file_to_modify, replacement_function: Callable[[str], (str, str)]
) -> str:
    remaining = file_to_modify
    modified_file: str = ""
    while len(remaining) > 0:
        changed, remaining = replacement_function(remaining)
        modified_file += changed
    return modified_file


# Replace old ui-g style classes
def ui_g_to_p_grid(old_file: str):
    """
    >>> ui_g_to_p_grid('    <div class="ui-g-12 ui-sm-12 ui-md-8 ui-lg-6 ui-xl-3">')
    '    <div class="p-col-12 p-sm-12 p-md-8 p-lg-6 p-xl-3">'
    """

    result = _replace_all(old_file, _replace_ui_g_element)
    result = _replace_all(result, _replace_ui_num_element)
    return result


# Close any closable element pairs in one element
def shorthand_close_xhtml_elements(old_file: str):
    """
    >>> shorthand_close_xhtml_elements('<test><newElement class="test"></newElement></test>')
    '<test><newElement class="test" /></test>'
    """

    return _replace_all(old_file, _shorthand_close_xhtml_element)


def _replace_ui_g_element(old_file: str):
    first_part, _, last_part = old_file.partition("ui-g")
    if last_part == "":
        return first_part, ""
    elif last_part[0] == "-":
        # This is a length element like ui-g-12, not the grid definition ui-g.
        return f"{first_part}p-col", last_part
    else:
        return f"{first_part}p-grid", last_part


def _replace_ui_num_element(old_file: str):
    replacable_suffixes = {"sm", "md", "lg", "xl"}
    first_part, _, last_part = old_file.partition("ui-")
    if last_part == "":
        return first_part, ""
    elif last_part[:2] not in replacable_suffixes:
        # Don't replace cases like "ui-datatable-sm" and "ui-fluid"
        return f"{first_part}ui-", last_part
    else:
        return f"{first_part}p-", last_part


def _shorthand_close_xhtml_element(old_file: str):
    elements = html_elements(old_file)
    for index, element in enumerate(elements):
        if index + 1 == len(elements):
            break
        next_element = elements[index + 1]
        if element.pairs_with(next_element):
            first_part, _, last_part = old_file.partition(
                element.full + next_element.full
            )
            return f"{first_part}{element.close()}", last_part
    return old_file, ""


def html_elements(old_file: str) -> list[HtmlElement]:
    """
    >>> htmlElements = html_elements("<first></second><third>")
    >>> htmlElements[0].full
    '<first>'
    >>> htmlElements[1].full
    '</second>'
    >>> htmlElements[2].full
    '<third>'
    """
    elements = []
    while len(old_file) > 0:
        elem_end_index = old_file.find(">")
        if elem_end_index == -1:
            return elements
        next_element_str = old_file[: elem_end_index + 1]
        # next_element_str = next_element_str.strip("\t\n\r ")
        elements.append(HtmlElement(next_element_str))
        old_file = old_file[elem_end_index + 1 :]
    return elements


# Replace ObjectUtils with Objects
def resolve_object_util_deprecation(old_file: str):
    """
    >>> resolve_object_util_deprecation('test.add("First " + ObjectUtils.equals(first, second));')
    'test.add("First " + Objects.equals(first, second));'
    """
    result = _replace_all(old_file, _replace_inline_object_util_to_string_call)
    result = _replace_all(result, _replace_object_util_to_string_call)
    result = _replace_all(result, _replace_object_util_equals_call)
    result = _replace_all(result, _replace_object_util_import)
    return result


def _replace_object_util_import(old_file: str):
    first_part, _, last_part = old_file.partition(
        "org.apache.commons.lang3.ObjectUtils"
    )
    if last_part == "":
        return first_part, ""
    return f"{first_part}java.util.Objects", last_part


def _replace_object_util_equals_call(old_file: str):
    first_part, _, last_part = old_file.partition("ObjectUtils.equals")
    if last_part == "":
        return first_part, ""
    return f"{first_part}Objects.equals", last_part


def _replace_inline_object_util_to_string_call(old_file: str):
    first_part, _, last_part = old_file.partition(
        "org.apache.commons.lang3.ObjectUtils.toString"
    )
    if last_part == "":
        return first_part, ""
    after_objects_before_close, last_close = _split_at_close_parentheses(last_part)
    return f'{first_part}Objects.toString{after_objects_before_close}, ""', last_close


def _replace_object_util_to_string_call(old_file: str):
    first_part, _, last_part = old_file.partition("ObjectUtils.toString")
    if last_part == "":
        return first_part, ""
    after_objects_before_close, last_close = _split_at_close_parentheses(last_part)
    return f'{first_part}Objects.toString{after_objects_before_close}, ""', last_close


def _split_at_close_parentheses(parentheses_string: str):
    """
    >>> _split_at_close_parentheses("(example()).extra()")
    ('(example()', ').extra()')
    """
    after_parenthesis_index = _locate_close_element(parentheses_string, "(", ")")
    return (
        parentheses_string[:after_parenthesis_index],
        parentheses_string[after_parenthesis_index:],
    )


# Replace raw tabchange types with parameterized generics
def resolve_raw_tabchange(old_file: str):
    return _replace_all(old_file, _replace_raw_tabchange_with_generic)


# Any events that should be replaced with wildcards, such as "TabChangeEvent<?>"
WILDCARD_EVENT_TYPES = [
    "TabChangeEvent",
    "ScheduleEvent",
]


def _replace_raw_tabchange_with_generic(old_file: str):
    wildcard_event_options_regex = _get_regex_options_from_list(WILDCARD_EVENT_TYPES)

    # Find events that do not have a wildcard, but should
    event_finder = re.compile(
        rf"(private |public |\()({wildcard_event_options_regex})(?!<\?>)"
    )
    event_match = event_finder.search(old_file)
    if event_match is not None:
        prefix, matched_event = event_match.group(1, 2)
        end_index = event_match.end() + 1
        return (
            event_finder.sub(f"{prefix}{matched_event}<?>", old_file[:end_index], 1),
            old_file[end_index:],
        )
    else:
        return old_file, ""


def _get_regex_options_from_list(options: List[str]):
    """
    >>> _get_regex_options_from_list(["A","B","C"])
    'A|B|C'
    """
    raw_event_options_regex = ""
    first = True
    for event in options:
        if first == True:
            first = False
        else:
            raw_event_options_regex += "|"
        raw_event_options_regex += event

    return raw_event_options_regex


def resolve_raw_events(old_file: str):
    return _replace_all(old_file, _replace_raw_event_types_with_generics)


RAW_EVENT_TYPES = [
    "RowEditEvent",
    "SelectEvent",
    "UnselectEvent",
]


def _replace_raw_event_types_with_generics(old_file: str):
    replacable_file = old_file
    remaining_file = ""

    raw_event_options_regex = _get_regex_options_from_list(RAW_EVENT_TYPES)

    explicit_cast_finder = re.compile(r"\((\w*?)\) ?(\w*?).getObject\(\)")
    explicit_cast_match = explicit_cast_finder.search(old_file)
    if explicit_cast_match is not None:
        inner_type, event_var_name = explicit_cast_match.group(1, 2)

        method_heading_finder = re.compile(
            rf"(public|private|protected) void (\w*?)\(({raw_event_options_regex}) {event_var_name}\)(\s*?)\u007b"
        )

        event_match = method_heading_finder.search(old_file)
        if event_match is not None:
            access_level, method_name, event, whitespace = event_match.group(1, 2, 3, 4)
            method_heading_replacement = f"{access_level} void {method_name}({event}<{inner_type}> {event_var_name}){whitespace}\u007b"

            # Restrict the file changing area to the end of the method before replacing
            end_of_method = _end_of_method(event_match, old_file)

            replacable_file = old_file[:end_of_method]
            remaining_file = old_file[end_of_method:]

            replacable_file = method_heading_finder.sub(
                method_heading_replacement, replacable_file, 1
            )

            explicit_cast_replacement = f"{event_var_name}.getObject()"
            replacable_file = explicit_cast_finder.sub(
                explicit_cast_replacement, replacable_file
            )

    return replacable_file, remaining_file


def _end_of_method(method_heading: re.Match, old_file) -> int:
    start_of_method = method_heading.end() - 1

    return start_of_method + _locate_close_bracket(old_file[start_of_method:])


def _locate_close_bracket(bracket_string: str):
    r"""
    >>> _locate_close_bracket("{\nexample('{}', test).extra()\n}")
    30
    """
    return _locate_close_element(bracket_string, "{", "}")


def _locate_close_element(string: str, open_element: str, close_element: str):
    assert string[0] == open_element
    uncanceled_parentheses = 1
    last_right_parenthesis_index = -1
    for index, char in enumerate(string[1:]):
        if char == open_element:
            uncanceled_parentheses += 1
        elif char == close_element:
            uncanceled_parentheses -= 1
            last_right_parenthesis_index = index

        if uncanceled_parentheses == 0:
            return last_right_parenthesis_index + 1

    raise AssertionError("Balanced elements not found")


def resolve_primitive_constructors(old_file: str):
    return _replace_all(old_file, _replace_primitive_constructor)


JAVA_PRIMITIVE_WRAPPERS = ["Short", "Long", "Boolean", "Integer"]


def _replace_primitive_constructor(old_file: str):
    for primitive in JAVA_PRIMITIVE_WRAPPERS:
        primitive_finder = re.compile(rf"new {primitive}\((.*?)\)")
        primitive_match = primitive_finder.search(old_file)
        if primitive_match is not None:
            constructor_parameter = primitive_match.group(1)
            old_file = primitive_finder.sub(
                f"{primitive}.valueOf({constructor_parameter})", old_file
            )

    return old_file, ""


def resolve_bigdecimal_constants(old_file: str):
    BIG_DECIMAL_ROUNDING_MODES = [
        "ROUND_HALF_EVEN",
        "ROUND_UP",
        "ROUND_HALF_UP",
    ]

    for rounding_mode_option in BIG_DECIMAL_ROUNDING_MODES:
        bigdecimal_finder = re.compile(rf"BigDecimal\.({rounding_mode_option})")
        bigdecimal_match = bigdecimal_finder.search(old_file)
        if bigdecimal_match is not None:
            rounding_mode = bigdecimal_match.group(1)
            old_file = bigdecimal_finder.sub(f"RoundingMode.{rounding_mode}", old_file)

    return old_file


if __name__ == "__main__":
    main()
