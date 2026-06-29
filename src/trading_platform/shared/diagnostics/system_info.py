import platform

def get_system_info():
    return {
        'python': platform.python_version(),
        'platform': platform.platform(),
    }
