import vim
import re
import os
import configparser

def merge_deep_recursive(target, source = {}):
    source = source.copy()
    for key, value in source.items():
        if isinstance(value, dict):
            target_child = target.setdefault(key, {})
            merge_deep_recursive(target_child, value)
        else:
            target[key] = value
    return target

def merge_deep(objects):
    result = {}
    for o in objects:
        merge_deep_recursive(result, o)
    return result

def enhance_roles_with_custom_function(roles):
    if vim.eval("exists('g:vim_ai_roles_config_function')") == '1':
        roles_config_function = vim.eval("g:vim_ai_roles_config_function")
        if not vim.eval("exists('*" + roles_config_function + "')"):
            raise Exception(f"Role config function does not exist: {roles_config_function}")
        else:
            roles.update(vim.eval(roles_config_function + "()"))

def load_role_config(role):
    roles_config_path = os.path.expanduser(vim.eval("g:vim_ai_roles_config_file"))
    if not os.path.exists(roles_config_path):
        raise Exception(f"Role config file does not exist: {roles_config_path}")

    roles = configparser.ConfigParser()
    roles.read(roles_config_path)
    roles = dict(roles)

    enhance_roles_with_custom_function(roles)

    if not role in roles:
        raise Exception(f"Role `{role}` not found")

    options = roles.get(f"{role}.options", {})
    options_complete = roles.get(f"{role}.options-complete", {})
    options_chat = roles.get(f"{role}.options-chat", {})

    ui = roles.get(f"{role}.ui", {})
    ui_complete = roles.get(f"{role}.ui-complete", {})
    ui_chat = roles.get(f"{role}.ui-chat", {})

    return {
        'role': dict(roles[role]),
        'config_default': {
            'options': dict(options),
            'ui': dict(ui),
        },
        'config_complete': {
            'options': dict(options_complete),
            'ui': dict(ui_complete),
        },
        'config_chat': {
            'options': dict(options_chat),
            'ui': dict(ui_chat),
        },
    }

def parse_role_names(prompt):
    chunks = re.split(r'[ :]+', prompt)
    roles = []
    for chunk in chunks:
        if not chunk.startswith("/"):
            break
        roles.append(chunk)
    return [raw_role[1:] for raw_role in roles]

def parse_prompt_and_role_config(instruction, command_type):
    instruction = instruction.strip()
    roles = parse_role_names(instruction)
    if not roles:
        # does not require role
        return ('', {})

    last_role = roles[-1]
    role_configs = merge_deep([load_role_config(role) for role in roles])
    config = merge_deep([role_configs['config_default'], role_configs['config_' + command_type]])
    role_prompt = role_configs['role'].get('prompt', '')
    return role_prompt, config

def make_config(input_var, output_var):
    input_options = vim.eval(input_var)
    config_default = input_options['config_default']
    config_extension = input_options['config_extension']
    instruction = input_options['instruction']
    command_type = input_options['command_type']

    role_prompt, role_config = parse_prompt_and_role_config(instruction, command_type)

    final_config = merge_deep([config_default, config_extension, role_config])

    output = {}
    output['config'] = final_config
    output['role_prompt'] = role_prompt
    vim.command(f'let {output_var}={output}')
    return output
