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

prompt = "".join(sys.stdin.readlines())

completion = openai.Completion.create(
    model="text-davinci-003",
    prompt=prompt,
    max_tokens=1000,
    temperature=0.1
)

print(completion.choices[0].text)
