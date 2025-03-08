from collections.abc import Sequence, Mapping, Generator, Iterator
from typing import TypedDict, Literal, Union, List, Protocol

class TextContent(TypedDict):
    type: Literal['text']
    text: str

class ImageUrlContent(TypedDict):
    type: Literal['image_url']
    image_url: dict[str, str]  # {'url': str}

MessageContent = Union[TextContent, ImageUrlContent]

class Message(TypedDict):
    role: Literal['system', 'user', 'assistant']
    content: List[MessageContent]
    type: str

class ResponseChunk(TypedDict):
    type: Literal['content', 'thinking']
    content: str


def print_debug(text, *args):
    if not is_ai_debugging():
        return
    with open(vim.eval("g:vim_ai_debug_log_file"), "a") as file:
        message = text.format(*args) if len(args) else text
        file.write(f"[{datetime.datetime.now()}] " + message + "\n")

def make_openai_options(options):
    max_tokens = int(options['max_tokens'])
    max_completion_tokens = int(options['max_completion_tokens'])
    result = {
        'model': options['model'],
        'temperature': float(options['temperature']),
        'stream': int(options['stream']) == 1,
    }
    if max_tokens > 0:
        result['max_tokens'] = max_tokens
    if max_completion_tokens > 0:
        result['max_completion_tokens'] = max_completion_tokens
    return result

def make_http_options(options):
    return {
        'request_timeout': float(options['request_timeout']),
        'enable_auth': bool(int(options['enable_auth'])),
        'token_file_path': options['token_file_path'],
    }

def openai_request(url, data, options):
    enable_auth=options['enable_auth']
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "VimAI",
    }
    if enable_auth:
        (OPENAI_API_KEY, OPENAI_ORG_ID) = load_api_key(options['token_file_path'])
        headers['Authorization'] = f"Bearer {OPENAI_API_KEY}"

        if OPENAI_ORG_ID is not None:
            headers["OpenAI-Organization"] =  f"{OPENAI_ORG_ID}"

    request_timeout=options['request_timeout']
    req = urllib.request.Request(
        url,
        data=json.dumps({ **data }).encode("utf-8"),
        headers=headers,
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=request_timeout) as response:
        if not data.get('stream', 0):
            yield json.loads(response.read().decode())
            return
        for line_bytes in response:
            line = line_bytes.decode("utf-8", errors="replace")
            if line.startswith(OPENAI_RESP_DATA_PREFIX):
                line_data = line[len(OPENAI_RESP_DATA_PREFIX):-1]
                if line_data.strip() == OPENAI_RESP_DONE:
                    pass
                else:
                    openai_obj = json.loads(line_data)
                    yield openai_obj


# TODO: reuse helper functions that are duplicated in utils.py
# TODO: each provider should provide it's error handling
# TODO: each provider should take care of it's default options
# TODO: how to properly extend AIProvider from types.py
# TODO: handle api keys
class OpenAIProvider():

    def __init__(self, config: Mapping[str, str]) -> None:
        self.config = config

    def request(self, messages: Sequence[Message]) -> Iterator[ResponseChunk]:
        config_options = self.config
        openai_options = make_openai_options(config_options)
        http_options = make_http_options(config_options)
        request = {
            'messages': messages,
            **openai_options
        }
        print_debug("[engine-chat] request: {}", request)
        url = config_options['endpoint_url']
        response = openai_request(url, request, http_options)

        def _choices(resp):
            choices = resp.get('choices', [{}])

            # NOTE choices may exist in the response, but be an empty list.
            if not choices:
                return [{}]

            return choices

        def map_chunk_no_stream(resp) -> ResponseChunk:
            print_debug("[engine-chat] response: {}", resp)
            content = _choices(resp)[0].get('message', {}).get('content', '')
            return {'type': 'content', 'content': content}

        def map_chunk_stream(resp) -> ResponseChunk:
            print_debug("[engine-chat] response: {}", resp)
            content = _choices(resp)[0].get('delta', {}).get('content', '')
            return {'type': 'content', 'content': content}

        map_chunk = map_chunk_stream if openai_options['stream'] else map_chunk_no_stream

        return map(map_chunk, response)
