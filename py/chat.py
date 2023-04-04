import openai

# import utils
plugin_root = vim.eval("s:plugin_root")
vim.command(f"py3file {plugin_root}/py/utils.py")

options = vim.eval("options")
request_options = make_request_options()

openai.api_key = load_api_key()

lines = vim.eval('getline(1, "$")')
contains_user_prompt = any(line == '>>> user' for line in lines)
if not contains_user_prompt:
    # user role not found, put whole file content as an user prompt
    vim.command("normal! ggO>>> user\n")
    vim.command("normal! G")
    vim.command("let &ul=&ul") # breaks undo sequence (https://vi.stackexchange.com/a/29087)
    vim.command("redraw")

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
