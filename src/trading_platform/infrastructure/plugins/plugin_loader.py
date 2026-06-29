class PluginLoader:
    def __init__(self) -> None:
        self._plugins = {}

    def add_plugin(self, name: str, plugin: object) -> None:
        self._plugins[name] = plugin

    def load_all(self) -> dict[str, object]:
        return dict(self._plugins)
