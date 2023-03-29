import openai

# import utils
plugin_root = vim.eval("s:plugin_root")
vim.command(f"py3file {plugin_root}/py/utils.py")

prompt = vim.eval("prompt")
options = make_options()

openai.api_key = load_api_key()

try:
    if prompt.strip():

        print('Completing...')
        vim.command("redraw")
        text = ""

        if not "turbo" in options["model"].lower():
            response = openai.Completion.create(stream=True, prompt=prompt, **options)
            generating_text = False
            for resp in response:
                new_text = resp['choices'][0].get('text', '')
                if not new_text.strip() and not generating_text:
                    continue # trim newlines from the beginning
                text += new_text
                if len(text) > 50:
                    text = print_text(text)

                generating_text = True
            if len(text):
                text = print_text(text)

        else:
            # using chatgpt
            messages = [
                    {
                        "role": "system",
                        "content": "You are a perfectly useful assistant. You help by answering questions in a scholarly and unbiased style while ALWAYS remaining truthful. Your answers must be very concise and only include code except if the question implies that you add more details.",
                        },
                    {
                        "role": "user",
                        "content": prompt,
                        },
                    ]
            response = openai.ChatCompletion.create(
                    stream=True,
                    messages=messages,
                    **options)
            generating_text = False
            for resp in response:
                new_text = resp['choices'][0]['delta'].get('content', '')
                if not new_text.strip() and not generating_text:
                    continue # trim newlines from the beginning
                text += new_text
                if len(text) > 50:
                    text = print_text(text)

                generating_text = True

            if len(text):
                text = print_text(text)

except KeyboardInterrupt:
    vim.command("normal! a Ctrl-C...")
    print("Completion stopped.")
except openai.error.Timeout:
    vim.command("normal! aRequest timeout...")
    print("Completion timed out.")
