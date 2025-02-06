import sys
import pathlib
from collections.abc import Callable
from typing import Self
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
        file_path = sys.argv[1]
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
def reformat_file(file_path: str, full_mode: bool = False):
    file_data = ""

    with open(file_path, encoding="UTF-8") as old_file:
        file_data = old_file.read()
        if file_path.endswith(".xhtml"):
            if full_mode:
                file_data = ui_g_to_p_grid(file_data)
            file_data = shorthand_close_xhtml_elements(file_data)
        elif file_path.endswith(".java"):
            file_data = resolve_object_util_deprecation(file_data)
            file_data = resolve_raw_tabchange(file_data)
            file_data = resolve_raw_events(file_data)

    file_to_rem = pathlib.Path(file_path)
    file_to_rem.unlink()

    with open(file_path, mode="x", encoding="UTF-8") as old_file:
        old_file.write(file_data)


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
            return (
                parentheses_string[: last_right_parenthesis_index + 1],
                parentheses_string[last_right_parenthesis_index + 1 :],
            )

    raise AssertionError("Balanced parentheses not found")


# Replace raw tabchange types with parameterized generics
def resolve_raw_tabchange(old_file: str):
    return _replace_all(old_file, _replace_raw_tabchange_with_generic)


def _replace_raw_tabchange_with_generic(old_file: str):
    first_part, _, last_part = old_file.partition("TabChangeEvent ")
    if last_part == "":
        return first_part, ""
    return f"{first_part}TabChangeEvent<?> ", last_part


def resolve_raw_events(old_file: str):
    return _replace_all(old_file, _use_generics_on_raw_types)


RAW_EVENT_TYPES = [
    "RowEditEvent",
    "SelectEvent",
]


def _use_generics_on_raw_types(old_file: str):
    for event in RAW_EVENT_TYPES:
        explicit_cast_finder = re.compile(r"\((\w*?)\) (\w*?).getObject\(\)")
        explicit_cast_match = explicit_cast_finder.search(old_file)
        if explicit_cast_match is not None:
            inner_type, event_var_name = explicit_cast_match.group(1, 2)

            method_heading_finder = re.compile(
                rf"void (\w*?)\({event} {event_var_name}\)"
            )
            event_match = method_heading_finder.search(old_file)
            if event_match is not None:
                method_name = event_match.group(1)
                method_heading_replacement = (
                    f"void {method_name}({event}<{inner_type}> {event_var_name})"
                )
                old_file = method_heading_finder.sub(
                    method_heading_replacement, old_file, 1
                )

                explicit_cast_replacement = f"{event_var_name}.getObject()"
                old_file = explicit_cast_finder.sub(explicit_cast_replacement, old_file)

    return old_file, ""


if __name__ == "__main__":
    main()
