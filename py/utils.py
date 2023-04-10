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
    if not api_key:
        raise Exception("Missing OpenAI API key")
    return api_key.strip()

def make_request_options(options):
    request_options = {}
    request_options['model'] = options['model']
    request_options['max_tokens'] = int(options['max_tokens'])
    request_options['temperature'] = float(options['temperature'])
    request_options['request_timeout'] = float(options['request_timeout'])
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
