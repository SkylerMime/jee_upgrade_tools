from reformat_file import (
    resolve_bigdecimal_constants,
    resolve_object_util_deprecation,
    reformat_file,
    resolve_primitive_constructors,
    resolve_raw_events,
    resolve_raw_tabchange,
    ui_g_to_p_grid,
    html_elements,
    shorthand_close_xhtml_elements,
)
from pathlib import Path
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


def run_reformat_test_on(file_name: str, file_data: str, full_mode: bool = False):
    TEST_FILE_DIRECTORY = Path("./testfiles")
    TEST_FILE_PATH = TEST_FILE_DIRECTORY / file_name

    _clear_directory(TEST_FILE_DIRECTORY)

    with TEST_FILE_PATH.open(mode="x", encoding="UTF-8") as test_file:
        test_file.write(file_data)

    reformat_file(TEST_FILE_PATH, full_mode)

    result = ""
    with open(TEST_FILE_PATH, encoding="UTF-8") as test_file:
        result = test_file.read()

    return result


def run_reformat_directory_test(file_data: str):
    TEST_FILE_DIRECTORY = "./testfiles"
    TEST_FILE_NAMES = "first.java", "second.java"

    _clear_directory(TEST_FILE_DIRECTORY)

    for file in TEST_FILE_NAMES:
        file_path = TEST_FILE_DIRECTORY + "/" + file
        with open(file_path, mode="x", encoding="UTF-8") as test_file:
            test_file.write(file_data)

    reformat_file(TEST_FILE_DIRECTORY, False)

    result = set()
    for file in TEST_FILE_NAMES:
        file_path = TEST_FILE_DIRECTORY + "/" + file
        with open(file_path, encoding="UTF-8") as test_file:
            result.add(test_file.read())

    return result


def _clear_directory(directory_path: Path):
    for file_to_remove in Path(directory_path).iterdir():
        file_to_remove.unlink()

    directory_to_remove = Path(directory_path)
    if directory_to_remove.exists():
        directory_to_remove.rmdir()

    Path(directory_path).mkdir()


def test_reformat_java_files_in_directory():
    result = run_reformat_directory_test(OBJECT_UTIL_REPEATED)

    assert result == {OBJECT_UTIL_REPEATED_EXPECTED, OBJECT_UTIL_REPEATED_EXPECTED}


def test_reformat_java_file():
    result = run_reformat_test_on("test.java", OBJECT_UTIL_REPEATED)

    assert result == OBJECT_UTIL_REPEATED_EXPECTED


def test_reformat_xhtml_file():
    UI_G_TEST_INPUT = """
<div class="ui-g">
    <div class="ui-g-12 ui-md-12 ui-lg-12 ui-xl-6" style="margin-left:-5px">
    <button class="ui-fluid">
    </button>
"""

    UI_G_EXPECTED_OUTPUT = """
<div class="p-grid">
    <div class="p-col-12 p-md-12 p-lg-12 p-xl-6" style="margin-left:-5px">
    <button class="ui-fluid" />
"""

    assert (
        run_reformat_test_on("test.xhtml", UI_G_TEST_INPUT, full_mode=True)
        == UI_G_EXPECTED_OUTPUT
    )


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


def test_add_other_generic():
    assert (
        resolve_raw_tabchange("public void setEvent(ScheduleEvent event) {")
        == "public void setEvent(ScheduleEvent<?> event) {"
    )


def test_generic_adds_stay_set():
    assert (
        resolve_raw_tabchange("public void setEvent(ScheduleEvent<?> event) {")
        == "public void setEvent(ScheduleEvent<?> event) {"
    )


def test_dont_add_import_generic():
    assert (
        resolve_raw_tabchange("import org.primefaces.model.ScheduleEvent;")
        == "import org.primefaces.model.ScheduleEvent;"
    )


def test_ui_num_replacement_keeps_non_num():
    assert ui_g_to_p_grid('<div class="ui-fluid">') == '<div class="ui-fluid">'


def test_ui_num_replacement_replaces_after_non_num():
    assert (
        ui_g_to_p_grid('<div class="ui-fluid ui-sm-4">')
        == '<div class="ui-fluid p-sm-4">'
    )


def test_get_html_elements_ignores_whitespace():
    htmlElements = html_elements("<first>      </first>")
    assert htmlElements[1].noWhitespace() == "</first>"


def test_across_line_shorthand_replacement():
    assert (
        shorthand_close_xhtml_elements(
            """<test><newElement class="test">
</newElement></test>"""
        )
        == """<test><newElement class="test" /></test>"""
    )


def test_whitespace_separated_shorthand_replacement():
    assert (
        shorthand_close_xhtml_elements(
            """<test class="ui-fluid">
    </test>"""
        )
        == '<test class="ui-fluid" />'
    )


def test_two_line_shorthand_replacements():
    assert (
        shorthand_close_xhtml_elements(
            """
<test><newElement class="test">
</newElement></test>
<secondElement></secondElement>
"""
        )
        == """
<test><newElement class="test" /></test>
<secondElement />
"""
    )


def test_raw_event_should_use_generic():
    RAW_EVENT = """
public void myMethod(RowEditEvent event)
{
    firstline = firstCall();
    MyType firstVar = (MyType) event.getObject();
    secondline();
}
"""

    GENERICS_EVENT = """
public void myMethod(RowEditEvent<MyType> event)
{
    firstline = firstCall();
    MyType firstVar = event.getObject();
    secondline();
}
"""

    assert resolve_raw_events(RAW_EVENT) == GENERICS_EVENT


def test_multiple_raw_events_should_use_generics():
    RAW_EVENT = """
public void myMethod(RowEditEvent event)
{
    firstline = firstCall();
    MyType firstVar = (MyType) event.getObject();
    secondline();
    MyType otherVar = (MyType)event.getObject();
}

public void myMethodTwo(SelectEvent event)
{
    thirdline = thirdCall();
    MyOtherType secondvar = (MyOtherType) event.getObject();
    fourthline();
}
"""

    GENERICS_EVENT = """
public void myMethod(RowEditEvent<MyType> event)
{
    firstline = firstCall();
    MyType firstVar = event.getObject();
    secondline();
    MyType otherVar = event.getObject();
}

public void myMethodTwo(SelectEvent<MyOtherType> event)
{
    thirdline = thirdCall();
    MyOtherType secondvar = event.getObject();
    fourthline();
}
"""

    assert resolve_raw_events(RAW_EVENT) == GENERICS_EVENT


def test_multiple_raw_events_for_same_event_type_should_use_generics():
    RAW_EVENT = """
public void myMethod(SelectEvent event)
{
    firstline = firstCall();
    MyType firstVar = (MyType) event.getObject();
    secondline();
    MyType otherVar = (MyType) event.getObject();
}

public void myMethodTwo(SelectEvent event)
{
    thirdline = thirdCall();
    MyOtherType secondvar = (MyOtherType) event.getObject();
    fourthline();
}
"""

    GENERICS_EVENT = """
public void myMethod(SelectEvent<MyType> event)
{
    firstline = firstCall();
    MyType firstVar = event.getObject();
    secondline();
    MyType otherVar = event.getObject();
}

public void myMethodTwo(SelectEvent<MyOtherType> event)
{
    thirdline = thirdCall();
    MyOtherType secondvar = event.getObject();
    fourthline();
}
"""

    assert resolve_raw_events(RAW_EVENT) == GENERICS_EVENT


def test_primitives_should_use_value_of():
    OLD_CONSTRUCTOR = "test() + 8 + new Long(myVal)"
    NEW_VALUE_OF = "test() + 8 + Long.valueOf(myVal)"

    assert resolve_primitive_constructors(OLD_CONSTRUCTOR) == NEW_VALUE_OF


def test_bigdecimals_should_use_enum():
    INT_VERSION = """
private BigDecimal total = BigDecimal.ZERO.setScale(2, BigDecimal.ROUND_HALF_EVEN);
private BigDecimal total = BigDecimal.ZERO.setScale(2, BigDecimal.ROUND_UP);
"""
    ENUM_VERSION = """
private BigDecimal total = BigDecimal.ZERO.setScale(2, RoundingMode.ROUND_HALF_EVEN);
private BigDecimal total = BigDecimal.ZERO.setScale(2, RoundingMode.ROUND_UP);
"""

    assert resolve_bigdecimal_constants(INT_VERSION) == ENUM_VERSION
