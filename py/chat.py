import openai

# import utils
plugin_root = vim.eval("s:plugin_root")
vim.command(f"py3file {plugin_root}/py/utils.py")

openai.api_key = load_api_key()

lines = vim.eval('getline(1, "$")')
contains_user_prompt = '>>> user' in lines
if not contains_user_prompt:
    # user role not found, put whole file content as an user prompt
    vim.command("normal! ggO>>> user\n")
    vim.command("normal! G")
    vim.command("let &ul=&ul") # breaks undo sequence (https://vi.stackexchange.com/a/29087)
    vim.command("redraw")

options_chat = {}
lines = vim.eval('getline(1, "$")')
contains_chat_options = '[chat-options]' in lines
if contains_chat_options:
    # parse options that are defined in the chat header
    options_index = lines.index('[chat-options]')
    for line in lines[options_index + 1:]:
        if line.startswith('#'):
            # ignore comments
            continue
        if line.strip() == '':
            # stop at the end of the region
            break
        (key, value) = line.split('=')
        options_chat[key.strip()] = value.strip()

options = make_options(options_chat)
request_options = make_request_options(options)

initial_prompt = options.get('initial_prompt', [])
initial_prompt = '\n'.join(initial_prompt)
file_content = vim.eval('trim(join(getline(1, "$"), "\n"))')
chat_content = f"{initial_prompt}\n{file_content}"
messages = parse_chat_messages(chat_content)

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
