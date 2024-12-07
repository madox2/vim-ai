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

is_debugging = vim.eval("g:vim_ai_debug") == "1"
debug_log_file = vim.eval("g:vim_ai_debug_log_file")

class KnownError(Exception):
    pass

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

def normalize_config(config):
    normalized = { **config }
    # initial prompt can be both a string and a list of strings, normalize it to list
    if 'initial_prompt' in config['options'] and isinstance(config['options']['initial_prompt'], str):
        normalized['options']['initial_prompt'] = normalized['options']['initial_prompt'].split('\n')
    return normalized

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

# During text manipulation in Vim's visual mode, we utilize "normal! c" command. This command deletes the highlighted text,
# immediately followed by entering insert mode where it generates desirable text.

# Normally, Vim contemplates the position of the first character in selection to decide whether to place the entered text
# before or after the cursor. For instance, if the given line is "abcd", and "abc" is selected for deletion and "1234" is
# written in its place, the result is as expected "1234d" rather than "d1234". However, if "bc" is chosen for deletion, the
# achieved output is "a1234d", whereas "1234ad" is not.

# Despite this, post Vim script's execution of "normal! c", it takes an exit immediately returning to the normal mode. This
# might trigger a potential misalignment issue especially when the most extreme left character is the line’s second character.

# To avoid such pitfalls, the method "need_insert_before_cursor" checks not only the selection status, but also the character
# at the first position of the highlighting. If the selection is off or the first position is not the second character in the line,
# it determines no need for prefixing the cursor.
def need_insert_before_cursor(is_selection):
    if is_selection == False:
        return False
    pos = vim.eval("getpos(\"'<\")[1:2]")
    if not isinstance(pos, list) or len(pos) != 2:
        raise ValueError("Unexpected getpos value, it should be a list with two elements")
    return pos[1] == "1" # determines if visual selection starts on the first window column

def render_text_chunks(chunks, is_selection):
    generating_text = False
    full_text = ''
    insert_before_cursor = need_insert_before_cursor(is_selection)
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


def parse_chat_messages(chat_content):
    lines = chat_content.splitlines()
    messages = []
    for line in lines:
        if line.startswith(">>> system"):
            messages.append({"role": "system", "content": ""})
            continue
        if line.startswith(">>> user"):
            messages.append({"role": "user", "content": ""})
            continue
        if line.startswith(">>> include"):
            messages.append({"role": "include", "content": ""})
            continue
        if line.startswith("<<< assistant"):
            messages.append({"role": "assistant", "content": ""})
            continue
        if not messages:
            continue
        messages[-1]["content"] += "\n" + line

    for message in messages:
        # strip newlines from the content as it causes empty responses
        message["content"] = message["content"].strip()

        if message["role"] == "include":
            message["role"] = "user"
            paths = message["content"].split("\n")
            message["content"] = ""

            pwd = vim.eval("getcwd()")
            for i in range(len(paths)):
                path = os.path.expanduser(paths[i])
                if not os.path.isabs(path):
                    path = os.path.join(pwd, path)

                paths[i] = path

                if '**' in path:
                    paths[i] = None
                    paths.extend(glob.glob(path, recursive=True))

            for path in paths:
                if path is None:
                    continue

                if os.path.isdir(path):
                    continue

                try:
                    with open(path, "r") as file:
                        message["content"] += f"\n\n==> {path} <==\n" + file.read()
                except UnicodeDecodeError:
                    message["content"] += "\n\n" + f"==> {path} <=="
                    message["content"] += "\n" + "Binary file, cannot display"

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

def printDebug(text, *args):
    if not is_debugging:
        return
    with open(debug_log_file, "a") as file:
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
        if not data['stream']:
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

def load_role_config(role):
    roles_config_path = os.path.expanduser(vim.eval("g:vim_ai_roles_config_file"))
    if not os.path.exists(roles_config_path):
        raise Exception(f"Role config file does not exist: {roles_config_path}")

    roles = configparser.ConfigParser()
    roles.read(roles_config_path)

    enhance_roles_with_custom_function(roles)

    if not role in roles:
        raise Exception(f"Role `{role}` not found")

    options = roles[f"{role}.options"] if f"{role}.options" in roles else {}
    options_complete =roles[f"{role}.options-complete"] if f"{role}.options-complete" in roles else {}
    options_chat = roles[f"{role}.options-chat"] if f"{role}.options-chat" in roles else {}

    return {
        'role': dict(roles[role]),
        'options': {
            'options_default': dict(options),
            'options_complete': dict(options_complete),
            'options_chat': dict(options_chat),
        },
    }

empty_role_options = {
    'options_default': {},
    'options_complete': {},
    'options_chat': {},
}

def parse_prompt_and_role(raw_prompt):
    prompt = raw_prompt.strip()
    role = re.split(' |:', prompt)[0]
    if not role.startswith('/'):
        # does not require role
        return (prompt, empty_role_options)

    prompt = prompt[len(role):].strip()
    role = role[1:]

    config = load_role_config(role)
    if 'prompt' in config['role'] and config['role']['prompt']:
        delim = '' if prompt.startswith(':') else ':\n'
        prompt = config['role']['prompt'] + delim + prompt
    return (prompt, config['options'])

def make_chat_text_chunks(messages, config_options):
    openai_options = make_openai_options(config_options)
    http_options = make_http_options(config_options)

    request = {
        'messages': messages,
        **openai_options
    }
    printDebug("[engine-chat] request: {}", request)
    url = config_options['endpoint_url']
    response = openai_request(url, request, http_options)

    def map_chunk_no_stream(resp):
        printDebug("[engine-chat] response: {}", resp)
        return resp['choices'][0]['message'].get('content', '')

    def map_chunk_stream(resp):
        printDebug("[engine-chat] response: {}", resp)
        return resp['choices'][0]['delta'].get('content', '')

    map_chunk = map_chunk_stream if openai_options['stream'] else map_chunk_no_stream

    return map(map_chunk, response)
