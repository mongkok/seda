import functools
import importlib
import string
import typing as t
import uuid

from seda.exceptions import ImportPathError

if t.TYPE_CHECKING:
    from seda.app import Seda


@functools.lru_cache(maxsize=None)
def get_callable(path: str, *, sep: str = ".") -> t.Callable:
    mod_name, _, call_name = path.rpartition(sep)

    if not mod_name or not call_name:
        raise ImportPathError(f'Import "{path}" must be "<mod>{sep}<attr>".')
    try:
        module = importlib.import_module(mod_name)
    except ImportError as exc:
        raise ImportPathError(exc)

    module = importlib.import_module(mod_name)
    try:
        call = getattr(module, call_name)
    except AttributeError:
        raise ImportPathError(
            f'Attribute "{call_name}" not found in module "{mod_name}".'
        )
    if not callable(call):
        raise ImportPathError(f'"{path}" is not callable.')
    return call


def get_app(path: str) -> "Seda":
    from . import Seda

    app = get_callable(path)

    if not isinstance(app, Seda):
        raise ImportPathError(f'"{app}" is not a "Seda" instance.')
    return app


def get_uid(uid: str = "") -> str:
    n = uuid.uuid4().int
    chars = string.digits + string.ascii_letters
    while n:
        n, digit = divmod(n, 62)
        uid += chars[digit]
    return uid + chars[0] * max(22 - len(uid), 0)
