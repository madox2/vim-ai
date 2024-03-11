import vim
import os
import configparser

roles_config_path = os.path.expanduser(vim.eval("g:vim_ai_roles_config_file"))
if not os.path.exists(roles_config_path):
    raise Exception(f"Role config file does not exist: {roles_config_path}")

roles = configparser.ConfigParser()
roles.read(roles_config_path)

if vim.eval("exists('g:vim_ai_roles_config_function')") == '1':
    roles_config_function = vim.eval("g:vim_ai_roles_config_function")
    if not vim.eval("exists('*" + roles_config_function + "')"):
        raise Exception(f"Role config function does not exist: {roles_config_function}")
    else:
        roles.update(vim.eval(roles_config_function + "()"))

role_names = [name for name in roles.sections() if not '.' in name]

role_list = [f'"{name}"' for name in role_names]
role_list = ", ".join(role_list)

role_list = f"[{role_list}]"

vim.command(f'let l:role_list = {role_list}')
