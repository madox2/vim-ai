import vim

complete_py_imported = True

def run_ai_completition(context):
    command_type = context['command_type']
    prompt = context['prompt']
    config = make_config(context['config'])
    config_options = config['options']
    config_ui = config['ui']

    try:
        if 'engine' in config and config['engine'] == 'complete':
            raise KnownError('complete engine is no longer supported')

        if prompt:
            print('Completing...')
            vim.command("redraw")

            initial_prompt = config_options.get('initial_prompt', [])
            initial_prompt = '\n'.join(initial_prompt)
            chat_content = f"{initial_prompt}\n\n>>> user\n\n{prompt}".strip()
            messages = parse_chat_messages(chat_content)
            print_debug(f"[{command_type}] text:\n" + chat_content)

            provider_class = load_provider(config['provider'])
            provider = provider_class(command_type, config_options, ai_provider_utils)
            response_chunks = provider.request(messages)

            text_chunks = map(
                lambda c: c.get("content"),
                filter(lambda c: c['type'] == 'assistant', response_chunks), # omit `thinking` section
            )

            render_text_chunks(text_chunks)

            clear_echo_message()
    except BaseException as error:
        handle_completion_error(error)
        print_debug("[{}] error: {}", command_type, traceback.format_exc())
