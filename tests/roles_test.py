from roles import load_ai_role_names

def test_role_completion():
    role_names = load_ai_role_names()
    assert role_names == [
        'test-role-simple',
        'test-role',
        'deprecated-test-role-simple',
        'deprecated-test-role',
    ]
