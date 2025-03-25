import os
from utils import parse_include_paths, ai_provider_utils, KnownError
import pytest
from unittest.mock import patch

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

@patch.dict(os.environ, {"AI_API_KEY": "env.secret"})
def test_load_api_key_precedence():
    assert "file.secret" == ai_provider_utils.load_api_key(
        "AI_API_KEY",
        token_file_path="tests/resources/example.token",
        token_load_fn="g:LoadToken()",
    )
    assert "fn.secret" == ai_provider_utils.load_api_key(
        "AI_API_KEY",
        token_load_fn="g:LoadToken()",
    )
    assert "env.secret" == ai_provider_utils.load_api_key(
        "AI_API_KEY",
    )

def test_missing_api_key():
    with pytest.raises(KnownError) as e_info:
        ai_provider_utils.load_api_key("AI_API_KEY_NONEXISTING")
