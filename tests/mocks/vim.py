import os

dirname = os.path.dirname(__file__)

def eval(cmd):
    match cmd:
        case 'g:vim_ai_debug_log_file':
            return '/tmp/vim_ai_debug.log'
        case 'g:vim_ai_roles_config_file':
            return os.path.join(dirname, '../resources/roles.ini')
        case 's:plugin_root':
            return os.path.join(dirname, '../..')
        case _:
            return None

def command(cmd):
    pass
