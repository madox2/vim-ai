import openai

# import utils
plugin_root = vim.eval("s:plugin_root")
vim.command(f"py3file {plugin_root}/py/utils.py")

prompt = vim.eval("prompt")
request_options = make_request_options()

openai.api_key = load_api_key()

try:
    if prompt.strip():

        print('Completing...')
        vim.command("redraw")

        response = openai.Completion.create(stream=True, prompt=prompt, **request_options)

        generating_text = False
        for resp in response:
            text = resp['choices'][0].get('text', '')
            if not text.strip() and not generating_text:
                continue # trim newlines from the beginning

            generating_text = True
            vim.command("normal! a" + text)
            vim.command("redraw")
except KeyboardInterrupt:
    vim.command("normal! a Ctrl-C...")
except openai.error.Timeout:
    vim.command("normal! aRequest timeout...")
