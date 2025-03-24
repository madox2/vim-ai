import vim
import datetime
import os

image_py_imported = True

def make_image_path(ui):
    download_dir = ui.get('download_dir', vim.eval('getcwd()'))
    timestamp = datetime.datetime.now(datetime.UTC).strftime("%Y%m%dT%H%M%SZ")
    filename = f'vim_ai_{timestamp}.png'
    return os.path.join(download_dir, filename)

def run_ai_image(context):
    prompt = context['prompt']
    config = context['config']
    config_options = config['options']
    ui = config['ui']
    command_type = context['command_type']

    try:
        if prompt:
            print('Generating...')
            print_debug("[image] text:\n" + prompt)

            provider_class = load_provider(config['provider'])
            provider = provider_class(command_type, config_options, ai_provider_utils)
            response_chunks = provider.request_image(prompt)

            info_messages = []
            for image in response_chunks:
                path = make_image_path(ui)
                save_b64_to_file(path, image['b64_data'])
                info_messages.append(f"Image: {path}")

            clear_echo_message()
            print("\n".join(info_messages))
    except BaseException as error:
        handle_completion_error(config['provider'], error)
        print_debug("[{}] error: {}", command_type, traceback.format_exc())
