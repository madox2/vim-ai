from utils import parse_chat_messages
import os

curr_dir = os.path.dirname(__file__)

def strip_text(txt):
    txt = txt.strip()
    lines = txt.splitlines()
    return "\n".join([line.lstrip() for line in lines])

def test_parse_user_message():
    chat_content = strip_text(
    """
    >>> user

    generate lorem ipsum
    """)
    actual_messages = parse_chat_messages(chat_content)
    assert [
        {
            'role': 'user',
            'content': [
                {
                    'type': 'text',
                    'text': 'generate lorem ipsum',
                },
            ],
        },
    ] == actual_messages


def test_parse_system_message():
    chat_content = strip_text("""
    >>> system

    you are general assystant

    >>> user

    generate lorem ipsum
    """)
    actual_messages = parse_chat_messages(chat_content)
    assert [
        {
            'role': 'system',
            'content': [
                {
                    'type': 'text',
                    'text': 'you are general assystant',
                },
            ],
        },
        {
            'role': 'user',
            'content': [
                {
                    'type': 'text',
                    'text': 'generate lorem ipsum',
                },
            ],
        },
    ] == actual_messages


def test_parse_two_user_messages():
    chat_content = strip_text(
    """
    >>> user

    generate lorem ipsum

    >>> user

    in english
    """)
    actual_messages = parse_chat_messages(chat_content)
    assert [
        {
            'role': 'user',
            'content': [
                {
                    'type': 'text',
                    'text': 'generate lorem ipsum',
                },
                {
                    'type': 'text',
                    'text': 'in english',
                },
            ],
        },
    ] == actual_messages

def test_parse_assistant_message():
    chat_content = strip_text("""
    >>> user

    generate lorem ipsum

    <<< assistant

    bla bla bla

    >>> user

    again
    """)
    actual_messages = parse_chat_messages(chat_content)
    assert [
        {
            'role': 'user',
            'content': [
                {
                    'type': 'text',
                    'text': 'generate lorem ipsum',
                },
            ],
        },
        {
            'role': 'assistant',
            'content': [
                {
                    'type': 'text',
                    'text': 'bla bla bla',
                },
            ],
        },
        {
            'role': 'user',
            'content': [
                {
                    'type': 'text',
                    'text': 'again',
                },
            ],
        },
    ] == actual_messages

def test_parse_include_single_file_message():
    chat_content = strip_text(f"""
    >>> user

    translate to human language

    >>> include

    {curr_dir}/resources/test1.include.txt

    <<< assistant

    it already is in human language

    >>> user

    try harder
    """)
    messages = parse_chat_messages(chat_content)
    actual_messages = parse_chat_messages(chat_content)
    assert [
        {
            'role': 'user',
            'content': [
                {
                    'type': 'text',
                    'text': 'translate to human language',
                },
                {
                    'type': 'text',
                    'text': f'==> {curr_dir}/resources/test1.include.txt <==\nhello world',
                },
            ],
        },
        {
            'role': 'assistant',
            'content': [
                {
                    'type': 'text',
                    'text': 'it already is in human language',
                },
            ],
        },
        {
            'role': 'user',
            'content': [
                {
                    'type': 'text',
                    'text': 'try harder',
                },
            ],
        },
    ] == actual_messages

def test_parse_include_multiple_files_message():
    chat_content = strip_text(f"""
    >>> user

    translate to human language

    >>> include

    {curr_dir}/resources/test1.include.txt
    {curr_dir}/resources/test2.include.txt
    """)
    messages = parse_chat_messages(chat_content)
    actual_messages = parse_chat_messages(chat_content)
    assert [
        {
            'role': 'user',
            'content': [
                {
                    'type': 'text',
                    'text': 'translate to human language',
                },
                {
                    'type': 'text',
                    'text': f'==> {curr_dir}/resources/test1.include.txt <==\nhello world',
                },
                {
                    'type': 'text',
                    'text': f'==> {curr_dir}/resources/test2.include.txt <==\nvim is awesome',
                },
            ],
        },
    ] == actual_messages

def test_parse_include_glob_files_message():
    chat_content = strip_text(f"""
    >>> user

    translate to human language

    >>> include

    {curr_dir}/**/*.include.txt
    """)
    actual_messages = parse_chat_messages(chat_content)
    assert [
        {
            'role': 'user',
            'content': [
                {
                    'type': 'text',
                    'text': 'translate to human language',
                },
                {
                    'type': 'text',
                    'text': f'==> {curr_dir}/resources/test1.include.txt <==\nhello world',
                },
                {
                    'type': 'text',
                    'text': f'==> {curr_dir}/resources/test2.include.txt <==\nvim is awesome',
                },
            ],
        },
    ] == actual_messages

def test_parse_include_image_message():
    chat_content = strip_text(f"""
    >>> user

    what is on the image?

    >>> include

    {curr_dir}/**/*.jpg
    """)
    actual_messages = parse_chat_messages(chat_content)
    assert [
        {
            'role': 'user',
            'content': [
                {
                    'type': 'text',
                    'text': 'what is on the image?',
                },
                {
                    'type': 'image_url',
                    'image_url': {
                        'url': 'data:image/jpg;base64,aW1hZ2UgZGF0YQo='
                    },
                },
            ],
        },
    ] == actual_messages

def test_parse_include_image_with_files_message():
    chat_content = strip_text(f"""
    >>> include

    {curr_dir}/resources/test1.include.txt
    {curr_dir}/resources/image_file.jpg
    {curr_dir}/resources/test2.include.txt
    """)
    actual_messages = parse_chat_messages(chat_content)
    assert [
        {
            'role': 'user',
            'content': [
                {
                    'type': 'text',
                    'text': f'==> {curr_dir}/resources/test1.include.txt <==\nhello world',
                },
                {
                    'type': 'image_url',
                    'image_url': {
                        'url': 'data:image/jpg;base64,aW1hZ2UgZGF0YQo='
                    },
                },
                {
                    'type': 'text',
                    'text': f'==> {curr_dir}/resources/test2.include.txt <==\nvim is awesome',
                },
            ],
        },
    ] == actual_messages

def test_parse_include_unsupported_binary_file():
    chat_content = strip_text(f"""
    >>> include

    {curr_dir}/resources/binary_file.bin
    {curr_dir}/resources/test1.include.txt
    """)
    actual_messages = parse_chat_messages(chat_content)
    assert [
        {
            'role': 'user',
            'content': [
                {
                    'type': 'text',
                    'text': f'==> {curr_dir}/resources/binary_file.bin <==\nBinary file, cannot display',
                },
                {
                    'type': 'text',
                    'text': f'==> {curr_dir}/resources/test1.include.txt <==\nhello world',
                },
            ],
        },
    ] == actual_messages
