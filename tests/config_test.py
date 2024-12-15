import vim
import os
from config import make_config

dirname = os.path.dirname(__file__)

def default_eval_mock(cmd):
    match cmd:
        case 'g:vim_ai_debug_log_file':
            return '/tmp/vim_ai_debug.log'
        case 'g:vim_ai_roles_config_file':
            return dirname + '/resources/roles.ini'
        case _:
            return None

default_config = {
  "options": {
    "model": "gpt-4o",
    "endpoint_url": "https://api.openai.com/v1/chat/completions",
    "max_tokens": "0",
    "max_completion_tokens": "0",
    "temperature": "1",
    "request_timeout": "20",
    "stream": "1",
    "enable_auth": "1",
    "token_file_path": "",
    "selection_boundary": "",
    "initial_prompt": "You are a general assistant.",
  },
  "ui": {
    "open_chat_command": "preset_below",
    "scratch_buffer_keep_open": "0",
    "populate_options": "0",
    "code_syntax_enabled": "1",
    "paste_mode": "1",
  },
}

def make_input_mock(mocker, input_options):
    def eval_mock(cmd):
        if cmd == 'l:input':
            return input_options
        return default_eval_mock(cmd)
    mocker.patch('vim.eval', eval_mock)


def test_default_config(mocker):
    make_input_mock(mocker, {
        'config_default': default_config,
        'config_extension': {},
        'instruction': 'hello',
        'command_type': 'chat',
    })
    command_spy = mocker.spy(vim, "command")
    actual_output = make_config('l:input', 'l:output')
    expected_output = {
        'config': default_config,
        'role_prompt': '',
    }
    command_spy.assert_called_once_with(f"let l:output={expected_output}")
    assert expected_output == actual_output

def test_param_config(mocker):
    make_input_mock(mocker, {
        'config_default': default_config,
        'config_extension': {
            'options': {
                'max_tokens': '1000',
            },
        },
        'instruction': 'hello',
        'command_type': 'chat',
    })
    actual_config = make_config('l:input', 'l:output')['config']
    assert '1000' == actual_config['options']['max_tokens']
    assert 'gpt-4o' == actual_config['options']['model']

def test_role_config(mocker):
    make_input_mock(mocker, {
        'config_default': default_config,
        'config_extension': {},
        'instruction': '/test-role-simple',
        'command_type': 'chat',
    })
    config = make_config('l:input', 'l:output')
    actual_config = config['config']
    actual_role_prompt = config['role_prompt']
    assert 'o1-preview' == actual_config['options']['model']
    assert 'simple role prompt' == actual_role_prompt

def test_role_config_different_commands(mocker):
    make_input_mock(mocker, {
        'config_default': default_config,
        'config_extension': {},
        'instruction': '/test-role hello',
        'command_type': 'chat',
    })
    config = make_config('l:input', 'l:output')
    actual_config = config['config']
    actual_role_prompt = config['role_prompt']
    assert 'model-common' == actual_config['options']['model']
    assert 'https://localhost/chat' == actual_config['options']['endpoint_url']
    assert '0' == actual_config['ui']['paste_mode']
    assert 'preset_tab' == actual_config['ui']['open_chat_command']
    assert '' == actual_role_prompt

    make_input_mock(mocker, {
        'config_default': default_config,
        'config_extension': {},
        'instruction': '/test-role hello',
        'command_type': 'complete',
    })
    config = make_config('l:input', 'l:output')
    actual_config = config['config']
    actual_role_prompt = config['role_prompt']
    assert 'model-common' == actual_config['options']['model']
    assert 'https://localhost/complete' == actual_config['options']['endpoint_url']
    assert '0' == actual_config['ui']['paste_mode']
    assert '' == actual_role_prompt

def test_multiple_role_configs(mocker):
    make_input_mock(mocker, {
        'config_default': default_config,
        'config_extension': {},
        'instruction': '/test-role /test-role-simple hello',
        'command_type': 'chat',
    })
    config = make_config('l:input', 'l:output')
    actual_config = config['config']
    actual_role_prompt = config['role_prompt']
    assert 'o1-preview' == actual_config['options']['model']
    assert 'https://localhost/chat' == actual_config['options']['endpoint_url']
    assert 'simple role prompt' == actual_role_prompt
