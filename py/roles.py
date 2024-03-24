import vim

# import utils
plugin_root = vim.eval("s:plugin_root")
vim.command(f"py3file {plugin_root}/py/utils.py")

roles_config_path = os.path.expanduser(vim.eval("g:vim_ai_roles_config_file"))
if not os.path.exists(roles_config_path):
    raise Exception(f"Role config file does not exist: {roles_config_path}")

roles = configparser.ConfigParser()
roles.read(roles_config_path)

enhance_roles_with_custom_function(roles)

role_names = [name for name in roles.sections() if not '.' in name]

role_list = [f'"{name}"' for name in role_names]
role_list = ", ".join(role_list)

role_list = f"[{role_list}]"

vim.command(f'let l:role_list = {role_list}')
