import vim

chat_py_imported = True

def _populate_options(config):
    default_config = make_config(vim.eval('g:vim_ai_chat_default'))

    default_options = default_config['options']
    options = config['options']

    vim.command("normal! O[chat]")
    vim.command("normal! o")
    vim.command("normal! iprovider=" + config['provider'] + "\n")
    for key, value in options.items():
        default_value = default_options.get(key, '')
        if key == 'initial_prompt':
            value = "\\n".join(value)
            if default_value:
                default_value = "\\n".join(default_value)

        if default_value == value:
            continue # do not show default values
        vim.command("normal! ioptions." + key + "=" + value + "\n")

    # this is always 1 when populating, the only supported option in chat header
    vim.command("normal! iui.populate_options=1\n")

def run_ai_chat(context):
    command_type = context['command_type']
    prompt = context['prompt']
    config = make_config(context['config'])
    config_options = config['options']
    roles = context['roles']

    # populate_options in the chat header always takes precedence to ensure it populates once set
    chat_populate_options = parse_chat_header_config()['ui'].get('populate_options', '')
    populate_options = chat_populate_options or config['ui']['populate_options']
    should_populate_config = populate_options == '1'

    def initialize_chat_window():
        lines = vim.eval('getline(1, "$")')

        # re-populate only when there is a reason for it, empty :AIC should not trigger population
        re_populate = len(roles) > 0 or not '[chat]' in lines

        if re_populate or not should_populate_config:
            if '[chat]' in lines:
                line_num = lines.index('[chat]') + 1
                vim.command("normal! " + str(line_num) + "gg")
                vim.command("normal! d}dd")

        contains_user_prompt = '>>> user' in lines
        if not contains_user_prompt:
            # user role not found, put whole file content as an user prompt
            vim.command("normal! gg")
            vim.command("normal! O>>> user\n")

        if re_populate and should_populate_config:
            vim.command("normal! gg")
            _populate_options(config)

        vim.command("normal! G")
        vim_break_undo_sequence()
        vim.command("redraw")

        file_content = vim.eval('trim(join(getline(1, "$"), "\n"))')
        role_lines = re.findall(r'(^>>> user|^>>> system|^<<< thinking|^<<< assistant).*', file_content, flags=re.MULTILINE)
        if not role_lines[-1].startswith(">>> user"):
            # last role is not user, most likely completion was cancelled before
            vim.command("normal! o")
            vim.command("normal! i\n>>> user\n\n")

        if prompt:
            vim.command("normal! i" + prompt)
            vim_break_undo_sequence()
            vim.command("redraw")

    initialize_chat_window()

    chat_config = parse_chat_header_config()
    options = {**config_options, **chat_config['options']}
    provider = chat_config['provider'] or config['provider']

    initial_prompt = '\n'.join(options.get('initial_prompt', []))
    initial_messages = parse_chat_messages(initial_prompt)

    chat_content = vim.eval('trim(join(getline(1, "$"), "\n"))')
    print_debug(f"[{command_type}] text:\n" + chat_content)
    chat_messages = parse_chat_messages(chat_content)

    messages = initial_messages + chat_messages

    try:
        last_content = messages[-1]["content"][-1]
        if last_content['type'] != 'text' or last_content['text']:
            vim.command("redraw")

            print('Answering...')
            vim.command("redraw")
            provider_class = load_provider(provider)
            provider = provider_class(command_type, options, ai_provider_utils)
            response_chunks = provider.request(messages)

            def _chunks_to_sections(chunks):
                first_thinking_chunk = True
                first_content_chunk = True
                for chunk in chunks:
                    if chunk['type'] == 'thinking' and first_thinking_chunk:
                        first_thinking_chunk = False
                        vim.command("normal! Go\n<<< thinking\n\n")
                    if chunk['type'] == 'assistant' and first_content_chunk:
                        first_content_chunk = False
                        vim.command("normal! Go\n<<< assistant\n\n")
                    yield chunk['content']

            render_text_chunks(_chunks_to_sections(response_chunks), append_to_eol=True)

            vim.command("normal! a\n\n>>> user\n\n")
            vim.command("redraw")
            clear_echo_message()
    except BaseException as error:
        handle_completion_error(provider, error)
        print_debug("[{}] error: {}", command_type, traceback.format_exc())
