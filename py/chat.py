import openai

# import utils
plugin_root = vim.eval("s:plugin_root")
vim.command(f"py3file {plugin_root}/py/utils.py")

options = make_options()
file_content = vim.eval('trim(join(getline(1, "$"), "\n"))')

openai.api_key = load_api_key()

lines = file_content.splitlines()
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

if not messages:
    file_content = ">>> user\n\n" + file_content
    messages.append({"role": "user", "content": file_content })

for message in messages:
    # strip newlines from the content as it causes empty responses
    message["content"] = message["content"].strip()

try:
    if messages[-1]["content"].strip():
        vim.command("normal! Go\n<<< assistant\n\n")
        vim.command("redraw")

        print('Answering...')
        vim.command("redraw")

        response = openai.ChatCompletion.create(messages=messages, stream=True, **options)

        generating_text = False
        for resp in response:
            text = resp['choices'][0]['delta'].get('content', '')
            if not text.strip() and not generating_text:
                continue # trim newlines from the beginning

            generating_text = True
            vim.command("normal! a" + text)
            vim.command("redraw")

        vim.command("normal! a\n\n>>> user\n\n")
        vim.command("redraw")
except KeyboardInterrupt:
    vim.command("normal! a Ctrl-C...")
except openai.error.Timeout:
    vim.command("normal! aRequest timeout...")
