import openai

# import utils
plugin_root = vim.eval("s:plugin_root")
vim.command(f"py3file {plugin_root}/py/utils.py")

prompt = vim.eval("prompt")

openai.api_key = load_api_key()

try:
    if prompt.strip():

        print('Completing...')
        vim.command("redraw")

        response = openai.Completion.create(
            model="text-davinci-003",
            prompt=prompt,
            max_tokens=1000,
            temperature=0.1,
            stream=True,
            request_timeout=request_timeout_seconds,
        )

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
