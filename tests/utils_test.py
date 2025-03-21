import os
from utils import parse_include_paths

dirname = os.path.dirname(__file__)
root_dir = os.path.abspath(os.path.join(dirname, '..'))

def test_parse_relative_path():
    actual = parse_include_paths('tests/resources/test1.include.txt')
    assert ['tests/resources/test1.include.txt'] == actual

def test_parse_absolute_path():
    actual = parse_include_paths(f'{root_dir}/tests/resources/test1.include.txt')
    assert [f'{root_dir}/tests/resources/test1.include.txt'] == actual

def test_parse_relative_path_glob():
    actual = parse_include_paths('**/*.include.txt')
    assert [
        'tests/resources/test1.include.txt',
        'tests/resources/test2.include.txt',
    ] == actual

def test_parse_absolute_path_glob():
    actual = parse_include_paths(f'{root_dir}/**/*.include.txt')
    assert [
        f'{root_dir}/tests/resources/test1.include.txt',
        f'{root_dir}/tests/resources/test2.include.txt',
    ] == actual
