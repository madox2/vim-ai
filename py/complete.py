import vim

complete_py_imported = True

def run_ai_completition(context):
    prompt = context['prompt']
    config = make_config(context['config'])
    config_options = config['options']
    config_ui = config['ui']

    engine = config['engine']

    def complete_engine(prompt):
        # this engine is deprecated
        openai_options = {
            'model': config_options['model'],
            'temperature': float(config_options['temperature']),
            'stream': int(config_options['stream']) == 1,
            'max_tokens': int(config_options['max_tokens']),
        }
        http_options = {
            'request_timeout': float(config_options['request_timeout']),
            'enable_auth': bool(int(config_options['enable_auth'])),
            'token_file_path': config_options['token_file_path'],
        }

        print_debug("[engine-complete] text:\n" + prompt)

        request = {
            'prompt': prompt,
            **openai_options
        }
        print_debug("[engine-complete] request: {}", request)
        url = config_options['endpoint_url']
        response = openai_request(url, request, http_options)
        def map_chunk(resp):
            print_debug("[engine-complete] response: {}", resp)
            return resp['choices'][0].get('text', '')
        text_chunks = map(map_chunk, response)
        return text_chunks

    def chat_engine(prompt):
        initial_prompt = config_options.get('initial_prompt', [])
        initial_prompt = '\n'.join(initial_prompt)
        chat_content = f"{initial_prompt}\n\n>>> user\n\n{prompt}".strip()
        messages = parse_chat_messages(chat_content)
        print_debug("[engine-chat] text:\n" + chat_content)

        provider_class = load_provider(config['provider'])
        provider = provider_class(config_options, ai_provider_utils)
        response_chunks = provider.request(messages)

        # TODO: omit `thinking` section when supported
        text_chunks = map(lambda r: r['content'], response_chunks)

        return text_chunks

    engines = {"chat": chat_engine, "complete": complete_engine}

    try:
        if prompt:
            print('Completing...')
            vim.command("redraw")

            text_chunks = engines[engine](prompt)
            render_text_chunks(text_chunks)

            clear_echo_message()
    except BaseException as error:
        handle_completion_error(error)
        print_debug("[complete] error: {}", traceback.format_exc())
