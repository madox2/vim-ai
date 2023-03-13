import openai

# import utils
plugin_root = vim.eval("s:plugin_root")
vim.command(f"py3file {plugin_root}/py/utils.py")

openai.api_key = load_api_key()

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

vim.command("normal! Go\n<<< assistant\n\n")
vim.command("redraw")

response = openai.ChatCompletion.create(
  model="gpt-3.5-turbo",
  messages=messages,
  stream=True,
)

for resp in response:
    if 'content' in resp['choices'][0]['delta']:
        text = resp['choices'][0]['delta']['content']
        vim.command("normal! a" + text)
        vim.command("redraw")

vim.command("normal! a\n\n>>> user\n")
vim.command("redraw")
