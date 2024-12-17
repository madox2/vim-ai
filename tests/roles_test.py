from roles import load_ai_role_names

def test_role_completion():
    role_names = load_ai_role_names('complete')
    assert set(role_names) == {
        'test-role-simple',
        'test-role',
        'deprecated-test-role-simple',
        'deprecated-test-role',
    }

def test_role_chat_only():
    role_names = load_ai_role_names('chat')
    assert set(role_names) == {
        'test-role-simple',
        'test-role',
        'chat-only-role',
        'deprecated-test-role-simple',
        'deprecated-test-role',
        # default roles
        'right',
        'below',
        'tab',
    }
