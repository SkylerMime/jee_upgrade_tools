from reformat_file import resolve_object_util_deprecation, reformat_file
import pathlib
import pytest

OBJECT_UTIL_REPEATED = """
import org.apache.commons.lang3.ObjectUtils;

firstline;
test.add("First " + ObjectUtils.toString(exampleVariable.method()));
secondline;
test.add("First " + org.apache.commons.lang3.ObjectUtils.toString(secondVariable.method(more()).more())).more();
"""

OBJECT_UTIL_REPEATED_EXPECTED = """
import java.util.Objects;

firstline;
test.add("First " + Objects.toString(exampleVariable.method(), ""));
secondline;
test.add("First " + Objects.toString(secondVariable.method(more()).more(), "")).more();
"""

def run_reformat_test_on(file_name: str, file_data: str):
    TEST_FILE_DIRECTORY = './testfiles'
    TEST_FILE_NAME = file_name
    TEST_FILE_PATH = TEST_FILE_DIRECTORY + '/' + TEST_FILE_NAME

    for file_to_remove in pathlib.Path(TEST_FILE_DIRECTORY).iterdir():
        file_to_remove.unlink()

    directory_to_remove = pathlib.Path(TEST_FILE_DIRECTORY)
    if directory_to_remove.exists():
        directory_to_remove.rmdir()
    
    pathlib.Path('./testfiles').mkdir()

    with open(TEST_FILE_PATH, mode="x", encoding="UTF-8") as test_file:
        test_file.write(file_data)
    
    reformat_file(TEST_FILE_PATH)

    result = ''
    with open(TEST_FILE_PATH, encoding="UTF-8") as test_file:
        result = test_file.read()

    return result

def test_reformat_java_file():
    result = run_reformat_test_on('test.java', OBJECT_UTIL_REPEATED)
    
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

    assert run_reformat_test_on('test.xhtml', UI_G_TEST_INPUT) == UI_G_EXPECTED_OUTPUT

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

    assert resolve_object_util_deprecation(OBJECT_UTIL_TEST_INPUT) == OBJECT_UTIL_EXPECTED_OUTPUT

def test_inline_replace():
    # java.util.Objects will need to be imported manually if it hasn't been already!
    # TODO: Do this automatically

    OBJECT_UTIL_INLINE = 'test.add("First " + org.apache.commons.lang3.ObjectUtils.toString(object));'

    OBJECT_UTIL_INLINE_EXPECTED = 'test.add("First " + Objects.toString(object, ""));'

    assert resolve_object_util_deprecation(OBJECT_UTIL_INLINE) == OBJECT_UTIL_INLINE_EXPECTED

def test_nesting_replace():
    OBJECT_UTIL_NESTING = 'test.add("First " + org.apache.commons.lang3.ObjectUtils.toString(secondVariable.method(more()).more())).more();'

    OBJECT_UTIL_NESTING_EXPECTED = 'test.add("First " + Objects.toString(secondVariable.method(more()).more(), "")).more();'

    assert resolve_object_util_deprecation(OBJECT_UTIL_NESTING) == OBJECT_UTIL_NESTING_EXPECTED

def test_multi_replace():
    assert resolve_object_util_deprecation(OBJECT_UTIL_REPEATED) == OBJECT_UTIL_REPEATED_EXPECTED

def test_bad_filepath():
    with pytest.raises(FileNotFoundError):
        reformat_file("./fakefile.txt")
