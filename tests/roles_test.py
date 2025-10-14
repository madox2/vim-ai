from roles import load_ai_role_names

def test_role_completion():
    role_names = load_ai_role_names('complete')
    assert set(role_names) == {
        'test-role-simple',
        'test-role',
        'test-role-openrouter-reasoning',
        'deprecated-test-role-simple',
        'deprecated-test-role',
    }

def test_role_chat_only():
    role_names = load_ai_role_names('chat')
    assert set(role_names) == {
        'test-role-simple',
        'test-role',
        'test-role-openrouter-reasoning',
        'chat-only-role',
        'deprecated-test-role-simple',
        'deprecated-test-role',
        'all_params',
        # default roles
        'right',
        'below',
        'tab',
        'populate',
        'populate-all',
    }

def test_explicit_image_roles():
    role_names = load_ai_role_names('image')
    assert set(role_names) == { 'hd-image', 'hd', 'natural' }
