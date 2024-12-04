import vim
import re

# Load configuration and utility functions
plugin_root = vim.eval("s:plugin_root")
vim.command(f"py3file {plugin_root}/py/utils.py")

prompt, role_options = parse_prompt_and_role(vim.eval("l:prompt"))
config = normalize_config(vim.eval("l:config"))
config_options = {
    **config['options'],
    **role_options.get('options_default', {}),
    **role_options.get('options_chat', {}),
}
config_ui = config['ui']

def initialize_chat_window():
    lines = vim.eval('getline(1, "$")')
    contains_user_prompt = '>>> user' in lines
    if not contains_user_prompt:
        populate_initial_content()

    position_cursor_at_end_of_buffer()
    vim_break_undo_sequence()

    file_content = vim.eval('trim(join(getline(1, "$"), "\n"))')
    role_lines = re.findall(r'(^>>> user|^>>> system|^<<< assistant).*', file_content, flags=re.MULTILINE)
    if not role_lines or not role_lines[-1].startswith(">>> user"):
        vim.command("normal! o")
        vim.command("normal! i\n>>> user\n\n")

    if prompt.strip():
        vim.command("normal! i" + prompt)
        vim_break_undo_sequence()
        vim.command("redraw")

def populate_initial_content():
    vim.command("normal! gg")
    populates_options = config_ui.get('populate_options', '1') == '1'
    if populates_options:
        vim.command("normal! O[chat-options]")
        vim.command("normal! o")
        for key, value in config_options.items():
            if key == 'initial_prompt':
                value = "\\n".join(value) if isinstance(value, list) else value
            vim.command("normal! i" + key + "=" + value + "\n")
    vim.command("normal! " + ("o" if populates_options else "O"))
    vim.command("normal! i>>> user\n")

def position_cursor_at_end_of_buffer():
    vim.command("normal! G")

def handle_answer_sequence(messages, openai_options, is_selection):
    vim.command("normal! Go\n<<< assistant\n\n")
    vim.command("redraw")

    print('Answering...')
    vim.command("redraw")

    request = {
        'stream': True,
        'messages': messages,
        **openai_options
    }

    printDebug("[chat] request: {}", request)
    url = options['endpoint_url']
    response = openai_request(url, request, http_options)

    def map_chunk(resp):
        printDebug("[chat] response: {}", resp)
        return resp['choices'][0]['delta'].get('content', '')

    text_chunks = map(map_chunk, response)
    render_text_chunks(text_chunks, is_selection)

    vim.command("normal! a\n\n>>> user\n\n")
    vim.command("redraw")
    clear_echo_message()

initialize_chat_window()

chat_options = parse_chat_header_options()
options = {**config_options, **chat_options}
openai_options = make_openai_options(options)
http_options = make_http_options(options)

initial_prompt = '\n'.join(options.get('initial_prompt', []))
initial_messages = parse_chat_messages(initial_prompt)

chat_content = vim.eval('trim(join(getline(1, "$"), "\n"))')
chat_messages = parse_chat_messages(chat_content)
is_selection = vim.eval("l:is_selection")

messages = initial_messages + chat_messages

try:
    if messages[-1]["content"].strip():
        vim.command("normal! Go\n<<< assistant\n\n")
        vim.command("redraw")

        print('Answering...')
        vim.command("redraw")

        request = {
            'messages': messages,
            **openai_options
        }
        printDebug("[chat] request: {}", request)
        url = options['endpoint_url']
        response = openai_request(url, request, http_options)

        def map_chunk_no_stream(resp):
            printDebug("[chat] response: {}", resp)
            return resp['choices'][0]['message'].get('content', '')

        def map_chunk_stream(resp):
            printDebug("[chat] response: {}", resp)
            return resp['choices'][0]['delta'].get('content', '')

        map_chunk = map_chunk_stream if openai_options['stream'] else map_chunk_no_stream

        text_chunks = map(map_chunk, response)
        render_text_chunks(text_chunks, is_selection)

        vim.command("normal! a\n\n>>> user\n\n")
        vim.command("redraw")
        clear_echo_message()

except BaseException as error:
    handle_completion_error(error)
    printDebug("[chat] error: {}", traceback.format_exc())
