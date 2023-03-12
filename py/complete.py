import requests
import sys
import os

prompt = vim.eval("prompt")

config_file_path = os.path.join(os.path.expanduser("~"), ".config/openai.token")

api_key = os.getenv("OPENAI_API_KEY")

try:
    with open(config_file_path, 'r') as file:
        api_key = file.read()
except Exception:
    pass

api_key = api_key.strip()

url = "https://api.openai.com/v1/completions"
headers = {
    'Content-Type': 'application/json',
    'Authorization': f"Bearer {api_key}"
}
data = {
    "model": "text-davinci-003",
    "prompt":prompt,
    "max_tokens": 1000,
    "temperature": 0.1
}
response = requests.post(url, headers=headers, json=data)
response = response.json()

output = response['choices'][0]['text']
