from context import make_ai_context, make_prompt

default_config = {
  "options": {
    "model": "gpt-4o",
    "endpoint_url": "https://api.openai.com/v1/chat/completions",
    "max_tokens": "0",
    "max_completion_tokens": "0",
    "temperature": "1",
    "request_timeout": "20",
    "stream": "1",
    "auth_type": "bearer",
    "token_file_path": "",
    "token_load_fn": "",
    "selection_boundary": "",
    "initial_prompt": "You are a general assistant.",
  },
  "ui": {
    "open_chat_command": "preset_below",
    "scratch_buffer_keep_open": "0",
    "populate_options": "0",
    "paste_mode": "1",
  },
}

def test_role_config():
    context = make_ai_context({
        'config_default': default_config,
        'config_extension': {},
        'user_instruction': '/deprecated-test-role-simple user instruction',
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
        'user_instruction': '/deprecated-test-role hello',
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

    context  = make_ai_context({ **base, 'command_type': 'complete' })
    actual_config = context['config']
    actual_prompt = context['prompt']
    assert 'model-common' == actual_config['options']['model']
    assert '0' == actual_config['ui']['paste_mode']
    assert 'hello' == actual_prompt
    assert 'https://localhost/complete' == actual_config['options']['endpoint_url']

    context  = make_ai_context({ **base, 'command_type': 'edit' })
    actual_config = context['config']
    actual_prompt = context['prompt']
    assert 'model-common' == actual_config['options']['model']
    assert '0' == actual_config['ui']['paste_mode']
    assert 'hello' == actual_prompt
    assert 'https://localhost/edit' == actual_config['options']['endpoint_url']

def test_multiple_role_configs():
    context = make_ai_context({
        'config_default': default_config,
        'config_extension': {},
        'user_instruction': '/deprecated-test-role /deprecated-test-role-simple hello',
        'user_selection': '',
        'command_type': 'chat',
    })
    actual_config = context['config']
    actual_prompt = context['prompt']
    assert 'o1-preview' == actual_config['options']['model']
    assert 'https://localhost/chat' == actual_config['options']['endpoint_url']
    assert 'simple role prompt:\nhello' == actual_prompt
