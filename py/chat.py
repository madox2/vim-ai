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

def run_ai_chat(context):
    command_type = context['command_type']
    prompt = context['prompt']
    config = make_config(context['config'])
    config_options = config['options']
    roles = context['roles']

    def initialize_chat_window():
        file_content = vim.eval('trim(join(getline(1, "$"), "\n"))')
        contains_user_prompt = re.search(r"^>>> (user|exec|include)", file_content, flags=re.MULTILINE)
        lines = vim.eval('getline(1, "$")')

        # if populate is set in config, populate once
        # it shouldn't re-populate after chat header options are modified (#158)
        populate = config['ui']['populate_options'] == '1' and not '[chat]' in lines
        # when called special `populate` role, force chat header re-population
        re_populate = 'populate' in roles

        if re_populate:
            if '[chat]' in lines:
                line_num = lines.index('[chat]') + 1
                vim.command("normal! " + str(line_num) + "gg")
                vim.command("normal! d}dd")

        if not contains_user_prompt:
            # user role not found, put whole file content as an user prompt
            vim.command("normal! gg")
            vim.command("normal! O>>> user\n")

        if populate or re_populate:
            vim.command("normal! gg")
            _populate_options(config)

        vim.command("normal! G")
        vim_break_undo_sequence()
        vim.command("redraw")

        last_role = re.match(r".*^(>>>|<<<) (\w+)", file_content, flags=re.DOTALL | re.MULTILINE)
        if last_role and last_role.group(2) not in ('user', 'include', 'exec'):
            # last role is not a user role, most likely completion was cancelled before
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
