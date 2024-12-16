import vim
import os

if "PYTEST_VERSION" in os.environ:
    from utils import *

roles_py_imported = True

def load_ai_role_names(command_type):
    roles_config_path = os.path.expanduser(vim.eval("g:vim_ai_roles_config_file"))
    if not os.path.exists(roles_config_path):
        raise Exception(f"Role config file does not exist: {roles_config_path}")

    roles = configparser.ConfigParser()
    roles.read(roles_config_path)

    enhance_roles_with_custom_function(roles)

    role_names = set()
    for name in roles.sections():
        parts = name.split('.')
        if len(parts) == 1 or parts[-1] == command_type:
            role_names.add(parts[0])

    return list(role_names)
