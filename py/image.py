import vim
import datetime
import os

image_py_imported = True

def make_openai_image_options(options):
    return {
        'model': options['model'],
        'quality': options['quality'],
        'size': options['size'],
        'style': options['style'],
        'response_format': 'b64_json',
    }

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

    try:
        if prompt:
            print('Generating...')
            openai_options = make_openai_image_options(config_options)
            http_options = make_http_options(config_options)
            request = { 'prompt': prompt, **openai_options }

            print_debug("[image] text:\n" + prompt)
            print_debug("[image] request: {}", request)
            url = config_options['endpoint_url']

            response, *_ = openai_request(url, request, http_options)
            print_debug("[image] response: {}", { 'images_count': len(response['data']) })

            path = make_image_path(ui)
            b64_data = response['data'][0]['b64_json']
            save_b64_to_file(path, b64_data)

            clear_echo_message()
            print(f"Image: {path}")
    except BaseException as error:
        handle_completion_error(error)
        print_debug("[image] error: {}", traceback.format_exc())
