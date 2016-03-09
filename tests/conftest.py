try:
    # Enable pytest-twisted only if available
    import pytest_twisted
    del pytest_twisted
    pytest_plugins = "pytest_twisted"
except ImportError:
    pass
