import openai

# import utils
plugin_root = vim.eval("s:plugin_root")
vim.command(f"py3file {plugin_root}/py/utils.py")

engine = vim.eval("engine")
config_options = vim.eval("options")
request_options = make_request_options(config_options)

prompt = vim.eval("prompt").strip()

openai.api_key = load_api_key()

def complete_engine(prompt):
    request = {
        'stream': True,
        'prompt': prompt,
        **request_options
    }
    printDebug("[engine-complete] request: {}", request)
    response = openai.Completion.create(**request)
    def map_chunk(resp):
        printDebug("[engine-complete] response: {}", resp)
        return resp['choices'][0].get('text', '')
    text_chunks = map(map_chunk, response)
    return text_chunks

def chat_engine(prompt):
    initial_prompt = config_options.get('initial_prompt', [])
    initial_prompt = '\n'.join(initial_prompt)
    chat_content = f"{initial_prompt}\n\n>>> user\n\n{prompt}".strip()
    messages = parse_chat_messages(chat_content)
    request = {
        'stream': True,
        'messages': messages,
        **request_options
    }
    printDebug("[engine-chat] request: {}", request)
    response = openai.ChatCompletion.create(**request)
    def map_chunk(resp):
        printDebug("[engine-chat] response: {}", resp)
        return resp['choices'][0]['delta'].get('content', '')
    text_chunks = map(map_chunk, response)
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
