import pathlib
import pkgutil
from importlib import import_module
from importlib.util import find_spec


def _modules(postfix="") -> list:
    return [
        import_module(f".{name}{postfix}", package=__name__)
        for (_, name, _) in pkgutil.iter_modules([str(pathlib.Path(__file__).parent)])
        if find_spec(f".{name}{postfix}", package=__name__)
    ]


def detect_models():
    _modules(".models")
