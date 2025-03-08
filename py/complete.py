import vim

complete_py_imported = True

def run_ai_completition(context):
    prompt = context['prompt']
    config = make_config(context['config'])
    config_options = config['options']
    config_ui = config['ui']

    engine = config['engine']

    def complete_engine(prompt):
        openai_options = make_openai_options(config_options)
        http_options = make_http_options(config_options)
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
        return make_chat_text_chunks(messages, config_options)

    engines = {"chat": chat_engine, "complete": complete_engine}

    try:
        if prompt:
            print('Completing...')
            vim.command("redraw")
            provider_class = load_provider(config['provider'])
            provider = provider_class(config)
            messages = parse_chat_messages(f">>> user\n\n{prompt}".strip())
            text_chunks = provider.request(messages)
            render_text_chunks(text_chunks)
            clear_echo_message()
    except BaseException as error:
        handle_completion_error(error)
        print_debug("[complete] error: {}", traceback.format_exc())
