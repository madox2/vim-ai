import vim
import datetime
import glob
import sys
import os
import json
import urllib.error
import urllib.request
import socket
import re
from urllib.error import URLError
from urllib.error import HTTPError
import traceback
import configparser
import base64

utils_py_imported = True

DEFAULT_ROLE_NAME = 'default'

def is_ai_debugging():
    return vim.eval("g:vim_ai_debug") == "1"

class KnownError(Exception):
    pass

def unwrap(input_var):
    return vim.eval(input_var)

def load_api_key(config_token_file_path):
    # token precedence: config file path, global file path, env variable
    global_token_file_path = vim.eval("g:vim_ai_token_file_path")
    api_key_param_value = os.getenv("OPENAI_API_KEY")
    try:
        token_file_path = config_token_file_path or global_token_file_path
        with open(os.path.expanduser(token_file_path), 'r') as file:
            api_key_param_value = file.read()
    except Exception:
        pass

    if not api_key_param_value:
        raise KnownError("Missing OpenAI API key")

    # The text is in format of "<api key>,<org id>" and the
    # <org id> part is optional
    elements = api_key_param_value.strip().split(",")
    api_key = elements[0].strip()
    org_id = None

    if len(elements) > 1:
        org_id = elements[1].strip()

    return (api_key, org_id)

def make_config(config):
    options = config['options']
    # initial prompt can be both a string and a list of strings, normalize it to list
    if 'initial_prompt' in options and isinstance(options['initial_prompt'], str):
        options['initial_prompt'] = options['initial_prompt'].split('\n')
    return config

def make_openai_options(options):
    max_tokens = int(options['max_tokens'])
    max_completion_tokens = int(options['max_completion_tokens'])
    result = {
        'model': options['model'],
        'temperature': float(options['temperature']),
        'stream': int(options['stream']) == 1,
    }
    if max_tokens > 0:
        result['max_tokens'] = max_tokens
    if max_completion_tokens > 0:
        result['max_completion_tokens'] = max_completion_tokens
    return result

def make_http_options(options):
    return {
        'request_timeout': float(options['request_timeout']),
        'enable_auth': bool(int(options['enable_auth'])),
        'token_file_path': options['token_file_path'],
    }

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

def print_debug(text, *args):
    if not is_ai_debugging():
        return
    with open(vim.eval("g:vim_ai_debug_log_file"), "a") as file:
        message = text.format(*args) if len(args) else text
        file.write(f"[{datetime.datetime.now()}] " + message + "\n")

OPENAI_RESP_DATA_PREFIX = 'data: '
OPENAI_RESP_DONE = '[DONE]'

def openai_request(url, data, options):
    enable_auth=options['enable_auth']
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "VimAI",
    }
    if enable_auth:
        (OPENAI_API_KEY, OPENAI_ORG_ID) = load_api_key(options['token_file_path'])
        headers['Authorization'] = f"Bearer {OPENAI_API_KEY}"

        if OPENAI_ORG_ID is not None:
            headers["OpenAI-Organization"] =  f"{OPENAI_ORG_ID}"

    request_timeout=options['request_timeout']
    req = urllib.request.Request(
        url,
        data=json.dumps({ **data }).encode("utf-8"),
        headers=headers,
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=request_timeout) as response:
        if not data.get('stream', 0):
            yield json.loads(response.read().decode())
            return
        for line_bytes in response:
            line = line_bytes.decode("utf-8", errors="replace")
            if line.startswith(OPENAI_RESP_DATA_PREFIX):
                line_data = line[len(OPENAI_RESP_DATA_PREFIX):-1]
                if line_data.strip() == OPENAI_RESP_DONE:
                    pass
                else:
                    openai_obj = json.loads(line_data)
                    yield openai_obj

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

def make_chat_text_chunks(messages, config_options):
    openai_options = make_openai_options(config_options)
    http_options = make_http_options(config_options)

    request = {
        'messages': messages,
        **openai_options
    }
    print_debug("[engine-chat] request: {}", request)
    url = config_options['endpoint_url']
    response = openai_request(url, request, http_options)

    def _choices(resp):
        choices = resp.get('choices', [{}])

        # NOTE choices may exist in the response, but be an empty list.
        if not choices:
            return [{}]

        return choices

    def map_chunk_no_stream(resp):
        print_debug("[engine-chat] response: {}", resp)
        return _choices(resp)[0].get('message', {}).get('content', '')

    def map_chunk_stream(resp):
        print_debug("[engine-chat] response: {}", resp)
        delta = _choices(resp)[0].get('delta', {})
        return delta.get('reasoning_content') or delta.get('content', '')
 
    map_chunk = map_chunk_stream if openai_options['stream'] else map_chunk_no_stream

    return map(map_chunk, response)

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
