import vim

# import utils
plugin_root = vim.eval("s:plugin_root")
vim.command(f"py3file {plugin_root}/py/utils.py")

config = normalize_config(vim.eval("l:config"))
engine = config['engine']

prompt, role_options = parse_prompt_and_role(vim.eval("l:prompt"))
config_options = {
    **config['options'],
    **role_options['options_default'],
    **role_options['options_complete'],
}
openai_options = make_openai_options(config_options)
http_options = make_http_options(config_options)

is_selection = vim.eval("l:is_selection")

def complete_engine(prompt):
    request = {
        'stream': True,
        'prompt': prompt,
        **openai_options
    }
    printDebug("[engine-complete] request: {}", request)
    url = config_options['endpoint_url']
    response = openai_request(url, request, http_options)
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
    url = config_options['endpoint_url']
    response = openai_request(url, request, http_options)
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
        render_text_chunks(text_chunks, is_selection)
        clear_echo_message()
except BaseException as error:
    handle_completion_error(error)
    printDebug("[complete] error: {}", traceback.format_exc())
