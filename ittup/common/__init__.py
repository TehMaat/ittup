from ittup.common.settings import Load


def __getattr__(name: str):
    # The config is loaded on first use, so '--help' doesn't need a valid config file
    if name == 'config_settings':
        return Load().config
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
