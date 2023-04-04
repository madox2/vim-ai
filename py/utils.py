import sys
import os

def load_api_key():
    config_file_path = os.path.join(os.path.expanduser("~"), ".config/openai.token")
    api_key = os.getenv("OPENAI_API_KEY")
    try:
        with open(config_file_path, 'r') as file:
            api_key = file.read()
    except Exception:
        pass
    return api_key.strip()

def make_request_options():
    options = vim.eval("options")
    request_options = {}
    request_options['model'] = options['model']
    request_options['max_tokens'] = int(options['max_tokens'])
    request_options['temperature'] = float(options['temperature'])
    request_options['request_timeout'] = float(options['request_timeout'])
    return request_options

