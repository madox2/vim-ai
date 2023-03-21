import openai

# import utils
plugin_root = vim.eval("s:plugin_root")
vim.command(f"py3file {plugin_root}/py/utils.py")

openai.api_key = load_api_key()

options = vim.eval("options")
file_content = vim.eval('trim(join(getline(1, "$"), "\n"))')

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

try:
    if messages[-1]["content"].strip():
        vim.command("normal! Go\n<<< assistant\n\n")
        vim.command("redraw")

        print('Answering...')
        vim.command("redraw")

        response = openai.ChatCompletion.create(
            messages=messages,
            stream=True,
            model=options['model'],
            max_tokens=int(options['max_tokens']),
            temperature=float(options['temperature']),
            request_timeout=float(options['request_timeout']),
        )

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
