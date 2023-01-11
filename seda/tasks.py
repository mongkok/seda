import inspect
import typing as t
from datetime import datetime

from seda import types


class BaseTask:
    def __init__(self, func: t.Callable) -> None:
        self.func = func
        module = inspect.getmodule(func)
        assert module is not None
        self.path = f"{module.__name__}.{func.__name__}"

    def __repr__(self) -> str:
        return f"<@task {self.path}>"


class Task(BaseTask):
    def __eq__(self, other: t.Any) -> bool:
        if not isinstance(other, Task):
            return NotImplemented
        return self.path == other.path

    def __hash__(self) -> int:
        return hash((self.__class__, self.path))


class Schedule(BaseTask):
    def __init__(
        self,
        func: t.Callable,
        expression: str,
        *,
        args: t.Optional[t.Sequence],
        kwargs: t.Optional[t.Dict[str, t.Any]],
        timezone: t.Optional[str] = None,
        time_window: t.Optional[types.ScheduleTimeWindow] = None,
        dead_letter_arn: t.Optional[str] = None,
        retry_policy: t.Optional[types.ScheduleRetryPolicy] = None,
        start_date: t.Optional[datetime] = None,
        end_date: t.Optional[datetime] = None,
        kms_key: t.Optional[str] = None,
    ) -> None:
        super().__init__(func)
        self.expression = expression
        self.args = args
        self.kwargs = kwargs
        self.timezone = timezone
        self.time_window = time_window
        self.dead_letter_arn = dead_letter_arn
        self.retry_policy = retry_policy
        self.start_date = start_date
        self.end_date = end_date
        self.kms_key = kms_key

    @property
    def identity(self) -> t.Tuple:
        return (
            self.__class__,
            self.path,
            self.expression,
            self.args,
            self.kwargs,
            self.timezone,
            self.time_window,
            self.start_date,
            self.end_date,
        )

    def __repr__(self) -> str:
        return f"<@schedule {self.path}({self.expression})>"

    def __eq__(self, other: t.Any) -> bool:
        if not isinstance(other, Schedule):
            return NotImplemented
        return self.identity == other.identity

    def __hash__(self) -> int:
        return hash(self.identity)
