from context import make_ai_context, make_prompt

default_config = {
  "engine": "chat",
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

def test_default_config():
    actual_context = make_ai_context({
        'config_default': default_config,
        'config_extension': {},
        'user_instruction': 'translate to Slovak',
        'user_selection': 'Hello world!',
        'command_type': 'chat',
    })
    expected_options = {
        **default_config['options'],
        'token_file_path': '/custom/path/ai.token',
    }
    expected_context = {
        'config': { **default_config, 'options': expected_options },
        'prompt': 'translate to Slovak:\nHello world!',
    }
    assert expected_context == actual_context

def test_param_config():
    actual_config = make_ai_context({
        'config_default': default_config,
        'config_extension': {
            'options': {
                'max_tokens': '1000',
            },
        },
        'user_instruction': 'hello',
        'user_selection': '',
        'command_type': 'chat',
    })['config']
    assert '1000' == actual_config['options']['max_tokens']
    assert 'gpt-4o' == actual_config['options']['model']

def test_role_config():
    context = make_ai_context({
        'config_default': default_config,
        'config_extension': {},
        'user_instruction': '/test-role-simple user instruction',
        'user_selection': 'selected text',
        'command_type': 'chat',
    })
    actual_config = context['config']
    actual_prompt = context['prompt']
    assert 'o1-preview' == actual_config['options']['model']
    assert 'simple role prompt:\nuser instruction:\nselected text' == actual_prompt

def test_role_config_different_commands():
    base = {
        'config_default': default_config,
        'config_extension': {},
        'user_instruction': '/test-role hello',
        'user_selection': '',
    }
    context  = make_ai_context({ **base, 'command_type': 'chat' })
    actual_config = context['config']
    actual_prompt = context['prompt']
    assert 'model-common' == actual_config['options']['model']
    assert '0' == actual_config['ui']['paste_mode']
    assert 'preset_tab' == actual_config['ui']['open_chat_command']
    assert 'hello' == actual_prompt
    assert 'https://localhost/chat' == actual_config['options']['endpoint_url']
    assert 'chat' == actual_config['engine']

    context  = make_ai_context({ **base, 'command_type': 'complete' })
    actual_config = context['config']
    actual_prompt = context['prompt']
    assert 'model-common' == actual_config['options']['model']
    assert '0' == actual_config['ui']['paste_mode']
    assert 'hello' == actual_prompt
    assert 'https://localhost/complete' == actual_config['options']['endpoint_url']
    assert 'complete' == actual_config['engine']

    context  = make_ai_context({ **base, 'command_type': 'edit' })
    actual_config = context['config']
    actual_prompt = context['prompt']
    assert 'model-common' == actual_config['options']['model']
    assert '0' == actual_config['ui']['paste_mode']
    assert 'hello' == actual_prompt
    assert 'https://localhost/edit' == actual_config['options']['endpoint_url']
    assert 'complete' == actual_config['engine']

def test_multiple_role_configs():
    context = make_ai_context({
        'config_default': default_config,
        'config_extension': {},
        'user_instruction': '/test-role /test-role-simple hello',
        'user_selection': '',
        'command_type': 'chat',
    })
    actual_config = context['config']
    actual_prompt = context['prompt']
    assert 'o1-preview' == actual_config['options']['model']
    assert 'https://localhost/chat' == actual_config['options']['endpoint_url']
    assert 'simple role prompt:\nhello' == actual_prompt

def test_chat_only_role():
    context = make_ai_context({
        'config_default': default_config,
        'config_extension': {},
        'user_instruction': '/chat-only-role',
        'user_selection': '',
        'command_type': 'chat',
    })
    actual_config = context['config']
    assert 'preset_tab' == actual_config['options']['open_chat_command']

def test_default_roles():
    base = {
        'config_default': default_config,
        'config_extension': {},
        'user_instruction': '/chat-only-role',
        'user_selection': '',
        'command_type': 'chat',
    }
    context = make_ai_context({ **base, 'user_instruction': '/right hello world!' })
    assert 'preset_right' == context['config']['ui']['open_chat_command']

    context = make_ai_context({ **base, 'user_instruction': '/tab' })
    assert 'preset_tab' == context['config']['ui']['open_chat_command']

def test_user_prompt():
    assert 'fix grammar: helo word' == make_prompt( '', 'fix grammar: helo word', '', '')
    assert 'fix grammar:\nhelo word' == make_prompt( '', 'fix grammar', 'helo word', '')

def test_role_prompt():
    assert 'fix grammar:\nhelo word' == make_prompt( 'fix grammar', 'helo word', '', '')
    assert 'fix grammar:\nhelo word' == make_prompt( 'fix grammar', '', 'helo word', '')
    assert 'fix grammar:\nand spelling:\nhelo word' == make_prompt( 'fix grammar', 'and spelling', 'helo word', '')

def test_selection_prompt():
    assert 'fix grammar:\nhelo word' == make_prompt( '', '', 'fix grammar:\nhelo word', '')

def test_selection_boundary():
    assert 'fix grammar:\n###\nhelo word\n###' == make_prompt( '', 'fix grammar', 'helo word', '###')
    assert 'fix grammar:\n###\nhelo word\n###' == make_prompt( 'fix grammar', '', 'helo word', '###')
