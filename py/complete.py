import openai

# import utils
plugin_root = vim.eval("s:plugin_root")
vim.command(f"py3file {plugin_root}/py/utils.py")

engine = vim.eval("engine")
options = make_options()
request_options = make_request_options(options)

prompt = vim.eval("prompt").strip()

openai.api_key = load_api_key()

def complete_engine(prompt):
    response = openai.Completion.create(stream=True, prompt=prompt, **request_options)
    text_chunks = map(lambda resp: resp['choices'][0].get('text', ''), response)
    return text_chunks

def chat_engine(prompt):
    initial_prompt = options.get('initial_prompt', [])
    initial_prompt = '\n'.join(initial_prompt)
    chat_content = f"{initial_prompt}\n\n>>> user\n\n{prompt}".strip()
    messages = parse_chat_messages(chat_content)
    response = openai.ChatCompletion.create(messages=messages, stream=True, **request_options)
    text_chunks = map(lambda resp: resp['choices'][0]['delta'].get('content', ''), response)
    return text_chunks

engines = {"chat": chat_engine, "complete": complete_engine}

try:
    if prompt:
        print('Completing...')
        vim.command("redraw")
        text_chunks = engines[engine](prompt)
        render_text_chunks(text_chunks)
except KeyboardInterrupt:
    vim.command("normal! a Ctrl-C...")
except openai.error.Timeout:
    vim.command("normal! aRequest timeout...")
