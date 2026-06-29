class TradingPlatformError(Exception):
    """Base exception for Trading Platform Pro."""


class ConfigurationError(TradingPlatformError):
    """Raised when configuration is invalid or incomplete."""


class LifecycleError(TradingPlatformError):
    """Raised when an invalid lifecycle transition is requested."""


class DependencyResolutionError(TradingPlatformError):
    """Raised when a dependency cannot be resolved."""
