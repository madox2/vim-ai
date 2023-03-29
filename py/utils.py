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

def make_options():
    options_default = vim.eval("options_default")
    options_user = vim.eval("options")
    options = {**options_default, **options_user}
    options['request_timeout'] = float(options['request_timeout'])
    options['temperature'] = float(options['temperature'])
    options['max_tokens'] = int(options['max_tokens'])
    return options

def print_text(text):
    vim.command("normal! a" + text)
    vim.command("redraw")
    return ""
