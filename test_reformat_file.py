from reformat_file import (
    resolve_object_util_deprecation,
    reformat_file,
    resolve_raw_tabchange,
    ui_g_to_p_grid,
)
import pathlib
import pytest

OBJECT_UTIL_REPEATED = """
import org.apache.commons.lang3.ObjectUtils;

firstline;
test.add("First " + ObjectUtils.toString(exampleVariable.method()));
secondline;
test.add("Second " + org.apache.commons.lang3.ObjectUtils.toString(secondVariable.method(more()).more())).more();
"""

OBJECT_UTIL_REPEATED_EXPECTED = """
import java.util.Objects;

firstline;
test.add("First " + Objects.toString(exampleVariable.method(), ""));
secondline;
test.add("Second " + Objects.toString(secondVariable.method(more()).more(), "")).more();
"""


def run_reformat_test_on(file_name: str, file_data: str):
    TEST_FILE_DIRECTORY = "./testfiles"
    TEST_FILE_NAME = file_name
    TEST_FILE_PATH = TEST_FILE_DIRECTORY + "/" + TEST_FILE_NAME

    for file_to_remove in pathlib.Path(TEST_FILE_DIRECTORY).iterdir():
        file_to_remove.unlink()

    directory_to_remove = pathlib.Path(TEST_FILE_DIRECTORY)
    if directory_to_remove.exists():
        directory_to_remove.rmdir()

    pathlib.Path("./testfiles").mkdir()

    with open(TEST_FILE_PATH, mode="x", encoding="UTF-8") as test_file:
        test_file.write(file_data)

    reformat_file(TEST_FILE_PATH)

    result = ""
    with open(TEST_FILE_PATH, encoding="UTF-8") as test_file:
        result = test_file.read()

    return result


def test_reformat_java_file():
    result = run_reformat_test_on("test.java", OBJECT_UTIL_REPEATED)

    assert result == OBJECT_UTIL_REPEATED_EXPECTED


def test_reformat_xhtml_file():
    UI_G_TEST_INPUT = """
<div class="ui-g">
    <div class="ui-g-12 ui-md-12 ui-lg-12 ui-xl-6" style="margin-left:-5px">
"""

    UI_G_EXPECTED_OUTPUT = """
<div class="p-grid">
    <div class="p-col-12 p-md-12 p-lg-12 p-xl-6" style="margin-left:-5px">
"""

    assert run_reformat_test_on("test.xhtml", UI_G_TEST_INPUT) == UI_G_EXPECTED_OUTPUT


def test_object_util():
    OBJECT_UTIL_TEST_INPUT = """
import org.apache.commons.lang3.ObjectUtils;

firstline;
test.add("First " + ObjectUtils.toString(exampleVariable.method()));
"""

    OBJECT_UTIL_EXPECTED_OUTPUT = """
import java.util.Objects;

firstline;
test.add("First " + Objects.toString(exampleVariable.method(), ""));
"""

    assert (
        resolve_object_util_deprecation(OBJECT_UTIL_TEST_INPUT)
        == OBJECT_UTIL_EXPECTED_OUTPUT
    )


def test_inline_replace():
    # java.util.Objects will need to be imported manually if it hasn't been already!
    # TODO: Do this automatically

    OBJECT_UTIL_INLINE = (
        'test.add("First " + org.apache.commons.lang3.ObjectUtils.toString(object));'
    )

    OBJECT_UTIL_INLINE_EXPECTED = 'test.add("First " + Objects.toString(object, ""));'

    assert (
        resolve_object_util_deprecation(OBJECT_UTIL_INLINE)
        == OBJECT_UTIL_INLINE_EXPECTED
    )


def test_nesting_replace():
    OBJECT_UTIL_NESTING = 'test.add("First " + org.apache.commons.lang3.ObjectUtils.toString(secondVariable.method(more()).more())).more();'

    OBJECT_UTIL_NESTING_EXPECTED = 'test.add("First " + Objects.toString(secondVariable.method(more()).more(), "")).more();'

    assert (
        resolve_object_util_deprecation(OBJECT_UTIL_NESTING)
        == OBJECT_UTIL_NESTING_EXPECTED
    )


def test_multi_line_replace():
    OBJECT_UTIL_MULTI_LINE = """
firstline;

test.add("First " + ObjectUtils.toString(exampleVariable.method()));
"""

    OBJECT_UTIL_MULTI_LINE_EXPECTED = """
firstline;

test.add("First " + Objects.toString(exampleVariable.method(), ""));
"""

    assert (
        resolve_object_util_deprecation(OBJECT_UTIL_MULTI_LINE)
        == OBJECT_UTIL_MULTI_LINE_EXPECTED
    )


def test_multi_line_replace_with_imports():
    OBJECT_UTIL_MULTI_LINE = """
import org.apache.commons.lang3.ObjectUtils;

firstline;
test.add("First " + ObjectUtils.toString(exampleVariable.method()));
secondline;
"""

    OBJECT_UTIL_MULTI_LINE_EXPECTED = """
import java.util.Objects;

firstline;
test.add("First " + Objects.toString(exampleVariable.method(), ""));
secondline;
"""

    assert (
        resolve_object_util_deprecation(OBJECT_UTIL_MULTI_LINE)
        == OBJECT_UTIL_MULTI_LINE_EXPECTED
    )


def test_two_replacements():
    OBJECT_UTIL_TWO = """
test.add(ObjectUtils.toString(first),
ObjectUtils.toString(second));
    """

    OBJECT_UTIL_TWO_EXPECTED = """
test.add(Objects.toString(first, ""),
Objects.toString(second, ""));
    """

    assert resolve_object_util_deprecation(OBJECT_UTIL_TWO) == OBJECT_UTIL_TWO_EXPECTED


def test_inline_and_regular_replacement():
    OBJECT_UTIL_TWO = """
test.add("First " + ObjectUtils.toString(first.method()));
test.add(org.apache.commons.lang3.ObjectUtils.toString(second.method()));
"""

    OBJECT_UTIL_TWO_EXPECTED = """
test.add("First " + Objects.toString(first.method(), ""));
test.add(Objects.toString(second.method(), ""));
"""

    assert resolve_object_util_deprecation(OBJECT_UTIL_TWO) == OBJECT_UTIL_TWO_EXPECTED


def test_multi_replace():
    assert (
        resolve_object_util_deprecation(OBJECT_UTIL_REPEATED)
        == OBJECT_UTIL_REPEATED_EXPECTED
    )


def test_bad_filepath():
    with pytest.raises(FileNotFoundError):
        reformat_file("./fakefile.txt")


def test_add_generic():
    assert (
        resolve_raw_tabchange("public void onTabChange(TabChangeEvent event) {")
        == "public void onTabChange(TabChangeEvent<?> event) {"
    )


def test_ui_num_replacement_keeps_non_num():
    assert ui_g_to_p_grid('<div class="ui-fluid">') == '<div class="ui-fluid">'


def test_ui_num_replacement_replaces_after_non_num():
    assert (
        ui_g_to_p_grid('<div class="ui-fluid ui-sm-4">')
        == '<div class="ui-fluid p-sm-4">'
    )
