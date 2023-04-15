# import utils
plugin_root = vim.eval("s:plugin_root")
vim.command(f"py3file {plugin_root}/py/utils.py")

engine = vim.eval("l:engine")
config_options = vim.eval("l:options")
openai_options = make_openai_options(config_options)
http_options = make_http_options(config_options)

prompt = vim.eval("l:prompt").strip()

def complete_engine(prompt):
    request = {
        'stream': True,
        'prompt': prompt,
        **openai_options
    }
    printDebug("[engine-complete] request: {}", request)
    response = openai_request('https://api.openai.com/v1/completions', request, http_options)
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
        **openai_options
    }
    printDebug("[engine-chat] request: {}", request)
    response = openai_request('https://api.openai.com/v1/chat/completions', request, http_options)
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
except URLError as error:
    if isinstance(error.reason, socket.timeout):
        vim.command("normal! aRequest timeout...")
    else:
        raise error
