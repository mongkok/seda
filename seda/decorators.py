import functools
import re
import time
import typing as t

from seda import exceptions
from seda.client import DEFAULT_RETRY_DELAY


def aws_retry(
    max_attempts: int,
    *,
    delay: int = DEFAULT_RETRY_DELAY,
    retry_exceptions: t.Optional[
        t.Union[
            t.Type[exceptions.AWSError],
            t.Sequence[t.Type[exceptions.AWSError]],
        ]
    ] = None,
    pattern: t.Optional[str] = None,
) -> t.Callable:
    if not retry_exceptions:
        retry_exceptions = exceptions.AWSError
    if pattern:
        msg_regex = re.compile(pattern)

    def decorator(f: t.Callable) -> t.Callable:
        @functools.wraps(f)
        def wrapper(*args: t.Any, **kwargs: t.Any) -> t.Any:
            attempts = 0

            while True:
                try:
                    response = f(*args, **kwargs)
                except retry_exceptions as exc:  # type: ignore[misc]
                    time.sleep(delay)
                    attempts += 1
                    if (
                        attempts >= max_attempts
                        or pattern
                        and not msg_regex.search(exc.msg)
                    ):
                        raise
                    continue
                return response

        return wrapper

    return decorator
