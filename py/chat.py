import openai
import json
import time

# import utils
plugin_root = vim.eval("s:plugin_root")
vim.command(f"py3file {plugin_root}/py/utils.py")

options = make_options()
file_content = vim.eval('trim(join(getline(1, "$"), "\n"))')

# save history as json
try:
    with open(f"{plugin_root}/chat_history.json", "r") as f:
        history = json.load(f)
except Exception as err:
    print(f"Error loading json: '{err}'")
    time.sleep(2)
    history = []

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
    messages.append({"role": "user", "content": file_content})

# filter out empty messages (happens when no context is provided to the chat,
# i.e. only a question was asked and no code from the original document was
# supplied):
messages = [m for m in messages if m["content"].strip() != ""]

# remove extra linebreaks added at the start of the message
for i, m in enumerate(messages):
    messages[i]["content"] = messages[i]["content"].lstrip()

history.extend(messages)
full_response = ""

try:
    if messages[-1]["content"].strip():
        vim.command("normal! Go\n<<< assistant\n\n")
        vim.command("redraw")

        print('Answering...')
        vim.command("redraw")

        response = openai.ChatCompletion.create(messages=messages, stream=True, **options)

        generating_text = False
        text = ""
        for resp in response:
            new_text = resp['choices'][0]['delta'].get('content', '')
            if not new_text.strip() and not generating_text:
                continue # trim newlines from the beginning
            text += new_text
            if len(text) > 50:
                full_response += text
                text = print_text(text)

            generating_text = True

        if len(text):
            full_response += text
            text = print_text(text)
        vim.command("normal! a\n\n>>> user\n\n")
        vim.command("redraw")

        print('Done answering.')

except KeyboardInterrupt:
    vim.command("normal! a Ctrl-C...")
    print("Completion stopped.")
except openai.error.Timeout:
    vim.command("normal! aRequest timeout...")
    print("Completion timed out.")


# append the new completion to history
history.append(
        {
            "type": "completion",
            "content": full_response,
            }
        )
with open(f"{plugin_root}/chat_history.json", "w") as f:
    json.dump(history[-10_000:], f, indent=2)
