import contextlib
import logging.config
import os
import typing as t
from string import Template

try:
    import django
except ImportError:  # pragma: nocover
    django = None  # type: ignore[assignment]

try:
    import mangum
except ImportError:  # pragma: nocover
    mangum = None  # type: ignore[assignment]

from seda import types
from seda.logging import LOGGING_CONFIG
from seda.session import Session
from seda.tasks import Schedule
from seda.utils import get_uid

LAMBDA_FUNCTION_POLICY_NAME = "seda-schedule-sns-policy"
SCHEDULE_GROUP_NAME = "seda-f-$function_name"
SCHEDULE_NAME = "$path-$uid"
SCHEDULE_ROLE_NAME = "seda-schedule-$region-f-$function_name"
SNS_TOPIC_NAME = "seda-async-f-$function_name"


class Config:
    def __init__(
        self,
        app: t.Optional[t.Callable] = None,
        *,
        function_name: t.Optional[str] = None,
        default_handler: t.Optional[t.Callable] = None,
        api_base_path: str = "/",
        lifespan: types.Lifespan = "auto",
        function_policy_name: str = LAMBDA_FUNCTION_POLICY_NAME,
        schedule_group_name: str = SCHEDULE_GROUP_NAME,
        schedule_name: str = SCHEDULE_NAME,
        schedule_role_name: str = SCHEDULE_ROLE_NAME,
        sns_topic_name: str = SNS_TOPIC_NAME,
        region: t.Optional[str] = None,
        profile: t.Optional[str] = None,
        access_key_id: t.Optional[str] = None,
        secret_access_key: t.Optional[str] = None,
        session_token: t.Optional[str] = None,
        **options: t.Any,
    ) -> None:
        self.app = app
        self.session = Session(
            region=region,
            profile=profile,
            access_key_id=access_key_id,
            secret_access_key=secret_access_key,
            session_token=session_token,
        )
        self._function_name = function_name or os.environ.get(
            "AWS_LAMBDA_FUNCTION_NAME"
        )
        self.api_base_path = api_base_path
        self.function_policy_name = function_policy_name
        self.schedule_group_name = Template(schedule_group_name)
        self.schedule_name = Template(schedule_name)
        self.schedule_role_name = Template(schedule_role_name)
        self.sns_topic_name = Template(sns_topic_name)
        self._account_id: t.Optional[str] = None
        self.lifespan = lifespan if django is not None else "off"

        if default_handler is None and self.app is not None:
            if mangum is not None:
                default_handler = mangum.Mangum(
                    self.app,
                    lifespan=self.lifespan,
                    api_gateway_base_path=self.api_base_path,
                    **options,
                )
            elif callable(self.app):
                default_handler = self.app

        self.default_handler = default_handler
        logging.config.dictConfig(LOGGING_CONFIG)

    @property
    def region(self) -> str:
        return self.session.region

    @property
    def sync(self) -> bool:
        return self._function_name is None

    @property
    def function_name(self) -> str:
        if self._function_name is None:
            raise RuntimeError("Lambda function name is required.")
        return self._function_name

    @contextlib.contextmanager
    def set_function_name(self, name: str) -> t.Generator:
        function_name = self._function_name
        self._function_name = name
        try:
            yield
        finally:
            self._function_name = function_name

    def get_schedule_role_name(self) -> str:
        return self.schedule_role_name.substitute(
            region=self.region,
            function_name=self.function_name,
        )

    def get_function_policy_name(self) -> str:
        return self.function_policy_name

    def get_schedule_group_name(self, onetime: bool = False) -> str:
        group_name = self.schedule_group_name.substitute(
            function_name=self.function_name,
        )
        if onetime:
            group_name += "-onetime"
        return group_name

    def get_schedule_name(self, schedule: Schedule) -> str:
        return self.schedule_name.substitute(
            function_name=self.function_name,
            path=schedule.path,
            uid=get_uid(),
        )

    def get_sns_topic_name(self) -> str:
        return self.sns_topic_name.substitute(function_name=self.function_name)

    def get_sns_statement_id(self) -> str:
        return f"seda-f-{self.function_name}-permission-sns"
