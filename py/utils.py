import vim
import datetime
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

is_debugging = vim.eval("g:vim_ai_debug") == "1"
debug_log_file = vim.eval("g:vim_ai_debug_log_file")

def load_api_key():
    config_file_path = os.path.join(os.path.expanduser("~"), ".config/openai.token")
    api_key = os.getenv("OPENAI_API_KEY")
    try:
        with open(config_file_path, 'r') as file:
            api_key = file.read()
    except Exception:
        pass
    if not api_key:
        raise Exception("Missing OpenAI API key")
    return api_key.strip()

def make_openai_options(options):
    return {
        'model': options['model'],
        'max_tokens': int(options['max_tokens']),
        'temperature': float(options['temperature']),
    }

def make_http_options(options):
    return {
        'request_timeout': float(options['request_timeout']),
    }

def render_text_chunks(chunks):
    generating_text = False
    full_text = ''
    for text in chunks:
        if not text.strip() and not generating_text:
            continue # trim newlines from the beginning
        generating_text = True
        vim.command("normal! a" + text)
        vim.command("undojoin")
        vim.command("redraw")
        full_text += text
    if not full_text.strip():
        print_info_message('Empty response received. Tip: You can try modifying the prompt and retry.')

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
        if line.startswith("<<< assistant"):
            messages.append({"role": "assistant", "content": ""})
            continue
        if not messages:
            continue
        messages[-1]["content"] += "\n" + line

    for message in messages:
        # strip newlines from the content as it causes empty responses
        message["content"] = message["content"].strip()

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
        file.write(f"[{datetime.datetime.now()}] " + text.format(*args) + "\n")

OPENAI_RESP_DATA_PREFIX = 'data: '
OPENAI_RESP_DONE = '[DONE]'
OPENAI_API_KEY = load_api_key()

def openai_request(url, data, options):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }
    request_timeout=options['request_timeout']
    req = urllib.request.Request(
        url,
        data=json.dumps({ **data }).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=request_timeout) as response:
        for line_bytes in response:
            line = line_bytes.decode("utf-8", errors="replace")
            if line.startswith(OPENAI_RESP_DATA_PREFIX):
                line_data = line[len(OPENAI_RESP_DATA_PREFIX):-1]
                if line_data == OPENAI_RESP_DONE:
                    pass
                else:
                    openai_obj = json.loads(line_data)
                    yield openai_obj

def print_info_message(msg):
    vim.command("redraw")
    vim.command(f"normal \<Esc>")
    vim.command("echohl ErrorMsg")
    vim.command(f"echomsg '{msg}'")
    vim.command("echohl None")

def handle_completion_error(error):
    # nvim throws - pynvim.api.common.NvimError: Keyboard interrupt
    is_nvim_keyboard_interrupt = "Keyboard interrupt" in str(error)
    if isinstance(error, KeyboardInterrupt) or is_nvim_keyboard_interrupt:
        print_info_message("Completion cancelled...")
    elif isinstance(error, URLError) and isinstance(error.reason, socket.timeout):
        print_info_message("Request timeout...")
    elif isinstance(error, HTTPError):
        status_code = error.getcode()
        msg = f"OpenAI: HTTPError {status_code}"
        if status_code == 401:
            msg += ' (Hint: verify that your API key is valid)'
        if status_code == 404:
            msg += ' (Hint: verify that you have access to the OpenAI API and to the model)'
        elif status_code == 429:
            msg += ' (Hint: verify that your billing plan is "Pay as you go")'
        print_info_message(msg)
    else:
        raise error

# clears "Completing..." message from the status line
def clear_echo_message():
    # https://neovim.discourse.group/t/how-to-clear-the-echo-message-in-the-command-line/268/3
    vim.command("call feedkeys(':','nx')")
