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
    messages = parse_chat_messages(chat_content)
    assert 1 == len(messages)
    assert 'user' == messages[0]['role']
    assert 'generate lorem ipsum' == messages[0]['content']


def test_parse_system_message():
    chat_content = strip_text("""
    >>> system

    you are general assystant

    >>> user

    generate lorem ipsum
    """)
    messages = parse_chat_messages(chat_content)
    assert 2 == len(messages)
    assert 'system' == messages[0]['role']
    assert 'you are general assystant' == messages[0]['content']
    assert 'user' == messages[1]['role']
    assert 'generate lorem ipsum' == messages[1]['content']

def test_parse_assistant_message():
    chat_content = strip_text("""
    >>> user

    generate lorem ipsum

    <<< assistant

    bla bla bla

    >>> user

    again
    """)
    messages = parse_chat_messages(chat_content)
    assert 3 == len(messages)
    assert 'user' == messages[0]['role']
    assert 'generate lorem ipsum' == messages[0]['content']
    assert 'assistant' == messages[1]['role']
    assert 'bla bla bla' == messages[1]['content']
    assert 'user' == messages[2]['role']
    assert 'again' == messages[2]['content']

def test_parse_include_single_file_message():
    chat_content = strip_text(f"""
    >>> user

    translate to human language

    >>> include

    {curr_dir}/resources/test1.include.txt
    """)
    messages = parse_chat_messages(chat_content)
    assert 2 == len(messages)
    assert 'user' == messages[0]['role']
    assert 'translate to human language' == messages[0]['content']
    assert 'user' == messages[1]['role']
    expected_content = strip_text(f"""
    ==> {curr_dir}/resources/test1.include.txt <==
    hello world
    """)
    assert expected_content == messages[1]['content']

def test_parse_include_multiple_files_message():
    chat_content = strip_text(f"""
    >>> user

    translate to human language

    >>> include

    {curr_dir}/resources/test1.include.txt
    {curr_dir}/resources/test2.include.txt
    """)
    messages = parse_chat_messages(chat_content)
    assert 2 == len(messages)
    assert 'user' == messages[0]['role']
    assert 'translate to human language' == messages[0]['content']
    assert 'user' == messages[1]['role']
    expected_content = strip_text(f"""
    ==> {curr_dir}/resources/test1.include.txt <==
    hello world

    ==> {curr_dir}/resources/test2.include.txt <==
    vim is awesome
    """)
    assert expected_content == messages[1]['content']

def test_parse_include_glob_files_message():
    chat_content = strip_text(f"""
    >>> user

    translate to human language

    >>> include

    {curr_dir}/**/*.include.txt
    """)
    messages = parse_chat_messages(chat_content)
    assert 2 == len(messages)
    assert 'user' == messages[0]['role']
    assert 'translate to human language' == messages[0]['content']
    assert 'user' == messages[1]['role']
    expected_content = strip_text(f"""
    ==> {curr_dir}/resources/test1.include.txt <==
    hello world

    ==> {curr_dir}/resources/test2.include.txt <==
    vim is awesome
    """)
    assert expected_content == messages[1]['content']

def test_parse_include_image_message():
    # TODO
    pass

def test_parse_include_image_with_files_message():
    # TODO
    pass
