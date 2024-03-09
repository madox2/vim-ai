import vim
import os
import configparser

roles_config_path = os.path.expanduser('~/.vim/roles.ini') # TODO configure
roles = configparser.ConfigParser()
roles.read(roles_config_path)

role_names = [name for name in roles.sections() if not '.' in name]

role_list = [f'"{name}"' for name in role_names]
role_list = ", ".join(role_list)

role_list = f"[{role_list}]"

vim.command(f'let l:role_list = {role_list}')
