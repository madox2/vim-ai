from roles import load_ai_role_names
import os
from unittest.mock import patch
import vim

dirname = os.path.dirname(__file__)
markdown_roles_dir = os.path.join(dirname, 'resources/roles-md')
mixed_roles_dir = os.path.join(dirname, 'resources/roles-mixed')

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

def test_load_markdown_roles_from_directory():
    default_eval = vim.eval
    with patch('vim.eval', side_effect=lambda cmd: markdown_roles_dir if cmd in ('g:vim_ai_roles_config_path', 'g:vim_ai_roles_config_file') else default_eval(cmd)):
        role_names = load_ai_role_names('chat')
        assert 'markdown-role' in role_names

def test_markdown_image_role_names():
    default_eval = vim.eval
    with patch('vim.eval', side_effect=lambda cmd: markdown_roles_dir if cmd in ('g:vim_ai_roles_config_path', 'g:vim_ai_roles_config_file') else default_eval(cmd)):
        role_names = load_ai_role_names('image')
        assert 'markdown-image' in role_names

def test_load_mixed_roles_from_directory_with_path_config():
    default_eval = vim.eval
    with patch('vim.eval', side_effect=lambda cmd: mixed_roles_dir if cmd == 'g:vim_ai_roles_config_path' else default_eval(cmd)):
        role_names = load_ai_role_names('chat')
        assert 'mixed-ini-role' in role_names
        assert 'mixed-from-ini' in role_names
        assert 'mixed-md-role' in role_names

def test_path_config_takes_precedence_over_file_config():
    default_eval = vim.eval
    with patch('vim.eval', side_effect=lambda cmd: mixed_roles_dir if cmd == 'g:vim_ai_roles_config_path' else markdown_roles_dir if cmd == 'g:vim_ai_roles_config_file' else default_eval(cmd)):
        role_names = load_ai_role_names('chat')
        assert 'mixed-md-role' in role_names
        assert 'markdown-role' not in role_names
