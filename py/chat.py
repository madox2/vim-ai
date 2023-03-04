import openai

import sys
import os
import openai

config_file_path = os.path.join(os.path.expanduser("~"), ".config/openai.token")

api_key = os.getenv("OPENAI_API_KEY")

try:
    with open(config_file_path, 'r') as file:
        api_key = file.read()
except Exception:
    pass

openai.api_key = api_key.strip()

lines = sys.stdin.readlines()

file_content = "".join(lines)

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

response = openai.ChatCompletion.create(
  model="gpt-3.5-turbo",
  messages=messages
)

answer = response['choices'][0]['message']['content']

print(f"{file_content.strip()}\n\n<<< assistant\n\n{answer.strip()}\n\n>>> user\n")
