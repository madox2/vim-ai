import vim
import datetime
import glob
import os
import json
import socket
from urllib.error import URLError
from urllib.error import HTTPError
import traceback
import configparser
import base64

utils_py_imported = True

DEFAULT_ROLE_NAME = 'default'

def is_ai_debugging():
    return vim.eval("g:vim_ai_debug") == "1"

def print_debug(text, *args):
    if not is_ai_debugging():
        return
    with open(vim.eval("g:vim_ai_debug_log_file"), "a") as file:
        message = text.format(*args) if len(args) else text
        file.write(f"[{datetime.datetime.now()}] " + message + "\n")

class KnownError(Exception):
    pass

class AIProviderUtils():
    def print_debug(self, text, *args):
        print_debug(text, *args)

    def make_known_error(self, message: str):
        return KnownError(message)

    def load_api_key(self, env_variable_name: str, token_file_path: str):
        # TODO: env variable should take a precendence
        # token precedence: config file path, global file path, env variable
        global_token_file_path = vim.eval("g:vim_ai_token_file_path")
        api_key = os.getenv(env_variable_name)
        try:
            token_file_path = token_file_path or global_token_file_path
            with open(os.path.expanduser(token_file_path), 'r') as file:
                api_key = file.read()
        except Exception:
            pass
        if not api_key:
            raise KnownError("Missing API key")
        return api_key

ai_provider_utils = AIProviderUtils()

def unwrap(input_var):
    return vim.eval(input_var)

def make_config(config):
    options = config['options']
    # initial prompt can be both a string and a list of strings, normalize it to list
    if 'initial_prompt' in options and isinstance(options['initial_prompt'], str):
        options['initial_prompt'] = options['initial_prompt'].split('\n')
    return config

# when running AIEdit on selection and cursor ends on the first column, it needs to
# be decided whether to append (a) or insert (i) to prevent missalignment.
# Example: helloxxx<Esc>hhhvb:AIE translate<CR> - expected Holaxxx, not xHolaxx
def need_insert_before_cursor():
    pos = vim.eval("getpos(\"'<\")[1:2]")
    if not isinstance(pos, list) or len(pos) != 2:
        raise ValueError("Unexpected getpos value, it should be a list with two elements")
    return pos[1] == "1" # determines if visual selection starts on the first window column

def render_text_chunks(chunks):
    generating_text = False
    full_text = ''
    insert_before_cursor = need_insert_before_cursor()
    for text in chunks:
        if not generating_text:
            text = text.lstrip() # trim newlines from the beginning
        if not text:
            continue
        generating_text = True
        if insert_before_cursor:
            vim.command("normal! i" + text)
            insert_before_cursor = False
        else:
            vim.command("normal! a" + text)
        vim.command("undojoin")
        vim.command("redraw")
        full_text += text
    if not full_text.strip():
        raise KnownError('Empty response received. Tip: You can try modifying the prompt and retry.')

def encode_image(image_path):
    """Encodes an image file to a base64 string."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def is_image_path(path):
    ext = path.strip().split('.')[-1]
    return ext in ['jpg', 'jpeg', 'png', 'gif']

def parse_include_paths(path):
    if not path:
        return []
    pwd = vim.eval('getcwd()')

    path = os.path.expanduser(path)
    if not os.path.isabs(path):
        path = os.path.join(pwd, path)

    expanded_paths = [path]
    if '*' in path:
        expanded_paths = sorted(glob.glob(path, recursive=True))

    return [path for path in expanded_paths if not os.path.isdir(path)]

def make_image_message(path):
    ext = path.split('.')[-1]
    base64_image = encode_image(path)
    return { 'type': 'image_url', 'image_url': { 'url': f"data:image/{ext.replace('.', '')};base64,{base64_image}" } }

def make_text_file_message(path):
    try:
        path = os.path.relpath(path)
        with open(path, 'r') as file:
            file_content = file.read().strip()
            return { 'type': 'text', 'text': f'==> {path} <==\n' + file_content.strip() }
    except UnicodeDecodeError:
        return { 'type': 'text', 'text': f'==> {path} <==\nBinary file, cannot display' }

def parse_chat_messages(chat_content):
    lines = chat_content.splitlines()
    messages = []

    current_type = ''
    for line in lines:
        match line:
            case '>>> system':
                messages.append({'role': 'system', 'content': [{ 'type': 'text', 'text': '' }]})
                current_type = 'system'
            case '<<< assistant':
                messages.append({'role': 'assistant', 'content': [{ 'type': 'text', 'text': '' }]})
                current_type = 'assistant'
            case '>>> user':
                if messages and messages[-1]['role'] == 'user':
                    messages[-1]['content'].append({ 'type': 'text', 'text': '' })
                else:
                    messages.append({'role': 'user', 'content': [{ 'type': 'text', 'text': '' }]})
                current_type = 'user'
            case '>>> include':
                if not messages or messages[-1]['role'] != 'user':
                    messages.append({'role': 'user', 'content': []})
                current_type = 'include'
            case _:
                if not messages:
                    continue
                match current_type:
                    case 'assistant' | 'system' | 'user':
                        messages[-1]['content'][-1]['text'] += '\n' + line
                    case 'include':
                        paths = parse_include_paths(line)
                        for path in paths:
                            content = make_image_message(path) if is_image_path(path) else make_text_file_message(path)
                            messages[-1]['content'].append(content)

    for message in messages:
        # strip newlines from the text content as it causes empty responses
        for content in message['content']:
            if content['type'] == 'text':
                content['text'] = content['text'].strip()

    return messages

def parse_chat_header_options():
    try:
        options = {}
        lines = vim.eval('getline(1, "$")')
        contains_chat_options = '[chat-options]' in lines
        if contains_chat_options:
            # parse options that are defined in the chat header
            options_index = lines.index('[chat-options]')
            for line in lines[options_index + 1:]:
                if line.startswith('#'):
                    # ignore comments
                    continue
                if line == '':
                    # stop at the end of the region
                    break
                (key, value) = line.strip().split('=')
                if key == 'initial_prompt':
                    value = value.split('\\n')
                options[key] = value
        return options
    except:
        raise Exception("Invalid [chat-options]")

def vim_break_undo_sequence():
    # breaks undo sequence (https://vi.stackexchange.com/a/29087)
    vim.command("let &ul=&ul")

def print_info_message(msg):
    escaped_msg = msg.replace("'", "`")
    vim.command("redraw")
    vim.command("echohl ErrorMsg")
    vim.command(f"echomsg '{escaped_msg}'")
    vim.command("echohl None")

def parse_error_message(error):
    try:
        parsed = json.loads(error.read().decode())
        return parsed["error"]["message"]
    except:
        pass

def handle_completion_error(error):
    # nvim throws - pynvim.api.common.NvimError: Keyboard interrupt
    is_nvim_keyboard_interrupt = "Keyboard interrupt" in str(error)
    if isinstance(error, KeyboardInterrupt) or is_nvim_keyboard_interrupt:
        print_info_message("Completion cancelled...")
    elif isinstance(error, HTTPError):
        status_code = error.getcode()
        error_message = parse_error_message(error)
        msg = f"OpenAI: HTTPError {status_code}"
        if error_message:
            msg += f": {error_message}"
        print_info_message(msg)
    elif isinstance(error, URLError) and isinstance(error.reason, socket.timeout):
        print_info_message("Request timeout...")
    elif isinstance(error, URLError):
        print_info_message(f"URLError: {error.reason}")
    elif isinstance(error, KnownError):
        print_info_message(str(error))
    else:
        raise error

# clears "Completing..." message from the status line
def clear_echo_message():
    # https://neovim.discourse.group/t/how-to-clear-the-echo-message-in-the-command-line/268/3
    vim.command("call feedkeys(':','nx')")

def enhance_roles_with_custom_function(roles):
    if vim.eval("exists('g:vim_ai_roles_config_function')") == '1':
        roles_config_function = vim.eval("g:vim_ai_roles_config_function")
        if not vim.eval("exists('*" + roles_config_function + "')"):
            raise Exception(f"Role config function does not exist: {roles_config_function}")
        else:
            roles.update(vim.eval(roles_config_function + "()"))

def read_role_files():
    plugin_root = vim.eval("s:plugin_root")
    default_roles_config_path = str(os.path.join(plugin_root, "roles-default.ini"))
    roles_config_path = os.path.expanduser(vim.eval("g:vim_ai_roles_config_file"))
    if not os.path.exists(roles_config_path):
        raise Exception(f"Role config file does not exist: {roles_config_path}")

    roles = configparser.ConfigParser()
    roles.read([default_roles_config_path, roles_config_path])
    return roles

def save_b64_to_file(path, b64_data):
    f = open(path, "wb")
    f.write(base64.b64decode(b64_data))
    f.close()

def load_provider(provider_name):
    try:
        providers = vim.eval("g:vim_ai_providers")
        provider_config = providers[provider_name]
        provider_path = provider_config['script_path']
        provider_class_name = provider_config['class_name']
        vim.command(f"py3file {provider_path}")
        provider_class = globals()[provider_class_name]
    except KeyError as error:
        print_debug("[load-provider] provider: {}", error)
        raise error
    return provider_class
