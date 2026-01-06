import os
import sys

# Add the py directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'py'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'mocks'))

from unittest.mock import patch

# Test get_proxy_settings function
def test_get_proxy_settings_with_vim_variable():
    """Test that proxy settings are read from vim variable"""
    # Mock the vim module and the proxy variable
    with patch.dict('sys.modules', {'vim': __import__('vim')}):
        import vim
        vim.eval = lambda x: 'http://proxy.example.com:8080' if x == 'g:vim_ai_proxy' else ''
        
        # Need to reload utils to pick up the new vim mock
        if 'utils' in sys.modules:
            del sys.modules['utils']
        
        from utils import get_proxy_settings
        
        proxy_settings = get_proxy_settings()
        assert proxy_settings is not None
        assert proxy_settings['http'] == 'http://proxy.example.com:8080'
        assert proxy_settings['https'] == 'http://proxy.example.com:8080'
        print("✓ Test passed: proxy settings from vim variable")

def test_get_proxy_settings_with_env_variable():
    """Test that proxy settings are read from environment variable when vim variable is empty"""
    with patch.dict('sys.modules', {'vim': __import__('vim')}):
        import vim
        vim.eval = lambda x: '' if x == 'g:vim_ai_proxy' else ''  # Empty vim proxy variable
        
        # Need to reload utils to pick up the new vim mock
        if 'utils' in sys.modules:
            del sys.modules['utils']
        
        with patch.dict(os.environ, {'https_proxy': 'http://env.proxy.com:3128'}):
            from utils import get_proxy_settings
            
            proxy_settings = get_proxy_settings()
            assert proxy_settings is not None
            assert proxy_settings['http'] == 'http://env.proxy.com:3128'
            assert proxy_settings['https'] == 'http://env.proxy.com:3128'
            print("✓ Test passed: proxy settings from environment variable")

def test_get_proxy_settings_no_proxy():
    """Test that None is returned when no proxy is configured"""
    with patch.dict('sys.modules', {'vim': __import__('vim')}):
        import vim
        vim.eval = lambda x: '' if x == 'g:vim_ai_proxy' else ''  # Empty vim proxy variable
        
        # Need to reload utils to pick up the new vim mock
        if 'utils' in sys.modules:
            del sys.modules['utils']
        
        # Clear any proxy environment variables
        with patch.dict(os.environ, {}, clear=True):
            from utils import get_proxy_settings
            
            proxy_settings = get_proxy_settings()
            assert proxy_settings is None
            print("✓ Test passed: no proxy configured")

if __name__ == '__main__':
    print("Running proxy configuration tests...")
    try:
        test_get_proxy_settings_with_vim_variable()
    except Exception as e:
        print(f"✗ Test failed: {e}")
    
    try:
        test_get_proxy_settings_with_env_variable()
    except Exception as e:
        print(f"✗ Test failed: {e}")
    
    try:
        test_get_proxy_settings_no_proxy()
    except Exception as e:
        print(f"✗ Test failed: {e}")
    
    print("All tests completed!")
