class TradingPlatformError(Exception):
    pass


class ConfigurationError(TradingPlatformError):
    pass


class DependencyError(TradingPlatformError):
    pass


class LifecycleError(TradingPlatformError):
    pass


class DependencyResolutionError(DependencyError):
    pass