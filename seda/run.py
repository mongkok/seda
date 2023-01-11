import asyncio
import functools
import typing as t

import anyio

from seda import types
from seda.utils import get_callable


def run_task(data: types.EventTask) -> t.Any:
    func = get_callable(data["path"])
    f = getattr(func, "task", func)
    task = functools.partial(f, *data.get("args") or (), **data.get("kwargs") or {})

    if asyncio.iscoroutinefunction(f):
        result = anyio.run(task)
        # asyncio.get_event_loop support
        asyncio.set_event_loop(asyncio.new_event_loop())
        return result
    return task()


def sync_to_async(f: t.Callable) -> t.Callable:
    async def wrapper(*args: t.Any, **kwargs: t.Any) -> t.Any:
        partial = functools.partial(f, *args, **kwargs)
        return await anyio.to_thread.run_sync(partial)

    return wrapper
