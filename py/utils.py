import datetime
import sys
import os
import json
import urllib.error
import urllib.request

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

is_debugging = vim.eval("g:vim_ai_debug") == "1"
debug_log_file = vim.eval("g:vim_ai_debug_log_file")

def make_request_options(options):
    request_options = {}
    request_options['model'] = options['model']
    request_options['max_tokens'] = int(options['max_tokens'])
    request_options['temperature'] = float(options['temperature'])
    return request_options

def render_text_chunks(chunks):
    generating_text = False
    for text in chunks:
        if not text.strip() and not generating_text:
            continue # trim newlines from the beginning
        generating_text = True
        vim.command("normal! a" + text)
        vim.command("redraw")

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

def openai_request(url, data):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(req) as response:
        for line_bytes in response:
            line = line_bytes.decode("utf-8", errors="replace")
            if line.startswith(OPENAI_RESP_DATA_PREFIX):
                line_data = line[len(OPENAI_RESP_DATA_PREFIX):-1]
                if line_data == OPENAI_RESP_DONE:
                    pass
                else:
                    openai_obj = json.loads(line_data)
                    yield openai_obj
