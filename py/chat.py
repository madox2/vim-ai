import requests
import sys
import os

file_content = vim.eval("prompt")

config_file_path = os.path.join(os.path.expanduser("~"), ".config/openai.token")

api_key = os.getenv("OPENAI_API_KEY")

try:
    with open(config_file_path, 'r') as file:
        api_key = file.read()
except Exception:
    pass

api_key = api_key.strip()

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


url = "https://api.openai.com/v1/chat/completions"
headers = {
    'Content-Type': 'application/json',
    'Authorization': F"Bearer {api_key}"
}
data = {
    "model": "gpt-3.5-turbo",
    "messages": messages
}
response = requests.post(url, headers=headers, json=data)
response = response.json()

answer = response['choices'][0]['message']['content']

output = f"{file_content.strip()}\n\n<<< assistant\n\n{answer.strip()}\n\n>>> user\n"
