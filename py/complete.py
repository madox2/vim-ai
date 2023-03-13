import openai

# import utils
plugin_root = vim.eval("s:plugin_root")
vim.command(f"py3file {plugin_root}/py/utils.py")

prompt = vim.eval("prompt")

openai.api_key = load_api_key()

response = openai.Completion.create(
    model="text-davinci-003",
    prompt=prompt,
    max_tokens=1000,
    temperature=0.1
)

output = response['choices'][0]['text']
