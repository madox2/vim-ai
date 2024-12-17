import vim
import os

if "PYTEST_VERSION" in os.environ:
    from utils import *

roles_py_imported = True

def load_ai_role_names(command_type):
    roles = read_role_files()
    enhance_roles_with_custom_function(roles)

    role_names = set()
    for name in roles.sections():
        parts = name.split('.')
        if len(parts) == 1 or parts[-1] == command_type:
            role_names.add(parts[0])

    return list(role_names)
