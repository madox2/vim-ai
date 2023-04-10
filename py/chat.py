import openai

# import utils
plugin_root = vim.eval("s:plugin_root")
vim.command(f"py3file {plugin_root}/py/utils.py")

config_options = vim.eval("options")
config_ui = vim.eval("ui")

openai.api_key = load_api_key()

def initialize_chat_window():
    lines = vim.eval('getline(1, "$")')
    contains_user_prompt = '>>> user' in lines
    if not contains_user_prompt:
        # user role not found, put whole file content as an user prompt
        vim.command("normal! gg")
        populates_options = config_ui['populate_options'] == '1'
        if populates_options:
            vim.command("normal! O[chat-options]")
            vim.command("normal! o")
            for key, value in config_options.items():
                if key == 'initial_prompt':
                    value = "\\n".join(value)
                vim.command("normal! i" + key + "=" + value + "\n")
        vim.command("normal! " + ("o" if populates_options else "O"))
        vim.command("normal! i>>> user\n")
        vim.command("normal! G")
        vim_break_undo_sequence()
        vim.command("redraw")

def parse_chat_header_options():
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

initialize_chat_window()

chat_options = parse_chat_header_options()
options = {**config_options, **chat_options}
request_options = make_request_options(options)

initial_prompt = '\n'.join(options.get('initial_prompt', []))
initial_messages = parse_chat_messages(initial_prompt)

chat_content = vim.eval('trim(join(getline(1, "$"), "\n"))')
chat_messages = parse_chat_messages(chat_content)

messages = initial_messages + chat_messages

try:
    if messages[-1]["content"].strip():
        vim.command("normal! Go\n<<< assistant\n\n")
        vim.command("redraw")

        print('Answering...')
        vim.command("redraw")

        response = openai.ChatCompletion.create(messages=messages, stream=True, **request_options)
        text_chunks = map(lambda resp: resp['choices'][0]['delta'].get('content', ''), response)
        render_text_chunks(text_chunks)

        vim.command("normal! a\n\n>>> user\n\n")
        vim.command("redraw")
except KeyboardInterrupt:
    vim.command("normal! a Ctrl-C...")
except openai.error.Timeout:
    vim.command("normal! aRequest timeout...")
