import vim
import re
import os
import configparser

if "PYTEST_VERSION" in os.environ:
    from utils import *

context_py_imported = True

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

def parse_prompt_and_role_config(user_instruction, command_type):
    user_instruction = user_instruction.strip()
    roles = parse_role_names(user_instruction)
    if not roles:
        # does not require role
        return (user_instruction, '', {})

    last_role = roles[-1]
    user_prompt = user_instruction[user_instruction.index(last_role) + len(last_role):].strip() # strip roles

    role_configs = merge_deep([load_role_config(role) for role in roles])
    config = merge_deep([role_configs['config_default'], role_configs['config_' + command_type]])
    role_prompt = role_configs['role'].get('prompt', '')
    return user_prompt, role_prompt, config

def make_selection_prompt(user_selection, user_prompt, role_prompt, selection_boundary):
    if not user_prompt and not role_prompt:
        return user_selection
    elif user_selection:
        if selection_boundary and selection_boundary not in user_selection:
            return f"{selection_boundary}\n{user_selection}\n{selection_boundary}"
        else:
            return user_selection
    return ''

def make_prompt(role_prompt, user_prompt, user_selection, selection_boundary):
    user_prompt = user_prompt.strip()
    delimiter = ":\n" if user_prompt and user_selection else ""
    user_selection = make_selection_prompt(user_selection, user_prompt, role_prompt, selection_boundary)
    prompt = f"{user_prompt}{delimiter}{user_selection}"
    if not role_prompt:
        return prompt
    delimiter = '' if prompt.startswith(':') else ':\n'
    prompt = f"{role_prompt}{delimiter}{prompt}"
    return prompt

def make_ai_context(params):
    config_default = params['config_default']
    config_extension = params['config_extension']
    user_instruction = params['user_instruction']
    user_selection = params['user_selection']
    command_type = params['command_type']

    user_prompt, role_prompt, role_config = parse_prompt_and_role_config(user_instruction, command_type)
    final_config = merge_deep([config_default, config_extension, role_config])
    selection_boundary = final_config['options']['selection_boundary']
    prompt = make_prompt(role_prompt, user_prompt, user_selection, selection_boundary)

    return {
        'config': final_config,
        'prompt': prompt,
    }
