import vim

chat_py_imported = True

def run_ai_chat(context):
    prompt = context['prompt']
    config = make_config(context['config'])
    config_options = config['options']
    config_ui = config['ui']

    def initialize_chat_window():
        lines = vim.eval('getline(1, "$")')
        contains_user_prompt = '>>> user' in lines
        if not contains_user_prompt:
            # user role not found, put whole file content as an user prompt
            vim.command("normal! gg")
            populates_options = config_ui['populate_options'] == '1'
            if populates_options:
                vim.command("normal! O[chat-options]")
                vim.command("normal! o")
                for key, value in config_options.items():
                    if key == 'initial_prompt':
                        value = "\\n".join(value)
                    vim.command("normal! i" + key + "=" + value + "\n")
            vim.command("normal! " + ("o" if populates_options else "O"))
            vim.command("normal! i>>> user\n")

        vim.command("normal! G")
        vim_break_undo_sequence()
        vim.command("redraw")

        file_content = vim.eval('trim(join(getline(1, "$"), "\n"))')
        role_lines = re.findall(r'(^>>> user|^>>> system|^<<< assistant).*', file_content, flags=re.MULTILINE)
        if not role_lines[-1].startswith(">>> user"):
            # last role is not user, most likely completion was cancelled before
            vim.command("normal! o")
            vim.command("normal! i\n>>> user\n\n")

        if prompt:
            vim.command("normal! i" + prompt)
            vim_break_undo_sequence()
            vim.command("redraw")

    initialize_chat_window()

    chat_options = parse_chat_header_options()
    options = {**config_options, **chat_options}

    initial_prompt = '\n'.join(options.get('initial_prompt', []))
    initial_messages = parse_chat_messages(initial_prompt)

    chat_content = vim.eval('trim(join(getline(1, "$"), "\n"))')
    print_debug("[chat] text:\n" + chat_content)
    chat_messages = parse_chat_messages(chat_content)

    messages = initial_messages + chat_messages

    try:
        last_content = messages[-1]["content"][-1]
        if last_content['type'] != 'text' or last_content['text']:
            vim.command("normal! Go\n<<< assistant\n\n")
            vim.command("redraw")

            print('Answering...')
            vim.command("redraw")

            text_chunks = make_chat_text_chunks(messages, options)
            render_text_chunks(text_chunks)

            vim.command("normal! a\n\n>>> user\n\n")
            vim.command("redraw")
            clear_echo_message()
    except BaseException as error:
        handle_completion_error(error)
        print_debug("[chat] error: {}", traceback.format_exc())
