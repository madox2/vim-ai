import vim

roles_py_imported = True

def load_ai_role_names():
    roles_config_path = os.path.expanduser(vim.eval("g:vim_ai_roles_config_file"))
    if not os.path.exists(roles_config_path):
        raise Exception(f"Role config file does not exist: {roles_config_path}")

    roles = configparser.ConfigParser()
    roles.read(roles_config_path)

    enhance_roles_with_custom_function(roles)

    role_names = [name for name in roles.sections() if not '.' in name]

    return role_names
