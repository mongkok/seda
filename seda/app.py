import asyncio
import functools
import json
import logging
import shlex
import subprocess
import threading
import time
import typing as t
from datetime import datetime

from seda import exceptions, policies, types
from seda.client import DEFAULT_RETRY_DELAY, Client
from seda.config import (
    LAMBDA_FUNCTION_POLICY_NAME,
    SCHEDULE_GROUP_NAME,
    SCHEDULE_NAME,
    SCHEDULE_ROLE_NAME,
    SNS_TOPIC_NAME,
    Config,
)
from seda.decorators import aws_retry
from seda.run import run_task, sync_to_async
from seda.tasks import Schedule, Task

AWS_GLOBAL = {"iam", "cloudfront", "route53"}


class Seda:
    def __init__(
        self,
        app: t.Optional[t.Callable] = None,
        *,
        function_name: t.Optional[str] = None,
        config_class: t.Type[Config] = Config,
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
        account_id: t.Optional[str] = None,
        schedules: t.Optional[t.Sequence[Schedule]] = None,
        **options: t.Any,
    ) -> None:
        self.config = config_class(
            app=app,
            function_name=function_name,
            default_handler=default_handler,
            api_base_path=api_base_path,
            lifespan=lifespan,
            function_policy_name=function_policy_name,
            schedule_group_name=schedule_group_name,
            schedule_name=schedule_name,
            schedule_role_name=schedule_role_name,
            sns_topic_name=sns_topic_name,
            region=region,
            profile=profile,
            access_key_id=access_key_id,
            secret_access_key=secret_access_key,
            session_token=session_token,
            **options,
        )
        self.tasks: t.List[Task] = []
        self.schedules = [] if schedules is None else list(schedules)
        self.client = Client(self.config.session)
        self.log = logging.getLogger("seda")
        self._account_id = account_id

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, app: t.Optional[t.Callable] = None, **kwargs: t.Any) -> "Seda":
        if cls._instance is None:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __call__(self, event: types.LambdaEvent, context: types.LambdaContext) -> t.Any:
        if "python" in event:
            return exec(event["python"])
        elif "shell" in event:
            subprocess.run(shlex.split(event["shell"]))
            return
        elif "task" in event:
            return run_task(event["task"])
        elif "Records" in event:
            record: types.EventRecord = event["Records"][0]
            if "Sns" in record:
                message = json.loads(record["Sns"]["Message"])
                if "task" in message:
                    return run_task(message["task"])

        if self.config.default_handler is not None:
            return self.config.default_handler(event, context)
        return

    @property
    def account_id(self) -> str:
        if self._account_id is None:
            self._account_id = self.client.get_identity().get("Account")
        return t.cast(str, self._account_id)

    def task(self, *args: t.Any, **kwargs: t.Any) -> t.Callable:
        if len(args) == 1 and callable(args[0]):
            return self.task()(args[0])

        service = kwargs.get("service", "sns")

        def decorator(f: t.Callable) -> t.Callable:
            task_f = Task(f)
            self.tasks.append(task_f)

            @functools.wraps(f)
            def wrapper(*args: t.Any, **kwargs: t.Any) -> t.Any:
                if self.config.sync:
                    return f(*args, **kwargs)
                payload = {
                    "task": {"path": task_f.path, "args": args, "kwargs": kwargs},
                }
                if service == "sns":
                    return self.client.sns_publish(
                        target_arn=self.ARN(f"sns:{self.config.get_sns_topic_name()}"),
                        message=payload,
                    )
                return self.client.invoke_function(
                    name=self.config.function_name,
                    payload=payload,
                    invocation_type="Event",
                )

            if asyncio.iscoroutinefunction(f) and not self.config.sync:
                wrapper = sync_to_async(wrapper)

            wrapper.at = self.onetime(f)  # type: ignore[attr-defined]
            wrapper.task = f  # type: ignore[attr-defined]
            wrapper.app = self  # type: ignore[attr-defined]
            return wrapper

        return decorator

    def onetime(self, func: t.Callable) -> t.Callable:
        def at(
            onetime_date: datetime,
            *,
            args: t.Optional[t.Sequence] = None,
            kwargs: t.Optional[t.Dict[str, t.Any]] = None,
            timezone: t.Optional[str] = None,
            time_window: t.Optional[types.ScheduleTimeWindow] = None,
            dead_letter_arn: t.Optional[str] = None,
            retry_policy: t.Optional[types.ScheduleRetryPolicy] = None,
            start_date: t.Optional[datetime] = None,
            end_date: t.Optional[datetime] = None,
            kms_key: t.Optional[str] = None,
        ) -> types.SNSPublishResponse:
            schedule = Schedule(
                func=func,
                expression=f"at({onetime_date.replace(microsecond=0).isoformat()})",
                args=args,
                kwargs=kwargs,
                timezone=timezone,
                time_window=time_window,
                dead_letter_arn=dead_letter_arn,
                retry_policy=retry_policy,
                start_date=start_date,
                end_date=end_date,
                kms_key=kms_key,
            )
            return self.create_schedule(schedule, onetime=True)

        return at

    def schedule(
        self,
        expression: str,
        *,
        args: t.Optional[t.Sequence] = None,
        kwargs: t.Optional[t.Dict[str, t.Any]] = None,
        timezone: t.Optional[str] = None,
        time_window: t.Optional[types.ScheduleTimeWindow] = None,
        dead_letter_arn: t.Optional[str] = None,
        retry_policy: t.Optional[types.ScheduleRetryPolicy] = None,
        start_date: t.Optional[datetime] = None,
        end_date: t.Optional[datetime] = None,
        kms_key: t.Optional[str] = None,
    ) -> t.Callable:
        def decorator(f: t.Callable) -> t.Callable:
            schedule = Schedule(
                func=f,
                expression=expression,
                args=args,
                kwargs=kwargs,
                timezone=timezone,
                time_window=time_window,
                dead_letter_arn=dead_letter_arn,
                retry_policy=retry_policy,
                start_date=start_date,
                end_date=end_date,
                kms_key=kms_key,
            )
            if schedule in self.schedules:
                raise RuntimeError(f"Schedule {schedule} already exists.")

            self.schedules.append(schedule)
            return f

        return decorator

    def ARN(self, key: str) -> str:
        service, _, resource = key.partition(":")

        if not service or not resource:
            raise ValueError(f'Key "{key}" must be "<service>:<resource>".')

        region = "" if service in AWS_GLOBAL else self.config.region
        return f"arn:aws:{service}:{region}:{self.account_id}:{resource}"

    def get_function(self) -> types.LambdaFunctionResponse:
        return self.client.get_function(self.config.function_name)

    def get_function_role_name(self) -> str:
        return self.get_function()["Configuration"]["Role"].rsplit("/")[-1]

    def create_schedule_role(self) -> types.RoleResponse:
        trust_policy = policies.SCHEDULE_TRUST_POLICY.copy()
        group_name = self.config.get_schedule_group_name()
        trust_policy["Statement"][0]["Condition"] = {
            "ForAllValues:StringLike": {
                "aws:SourceArn": self.ARN(f"scheduler:schedule/{group_name}*/*"),
            },
            "ForAllValues:StringEquals": {
                "aws:SourceAccount": self.account_id,
            },
        }
        policy = policies.LAMBDA_INVOKE_POLICY.copy()
        function_arn = self.ARN(f"lambda:function:{self.config.function_name}")
        policy["Statement"][0]["Resource"] = [function_arn, f"{function_arn}:*"]
        role_name = self.config.get_schedule_role_name()
        return self.client.create_role(role_name, trust_policy, policy)

    def delete_schedule_role(self) -> types.Response:
        role_name = self.config.get_schedule_role_name()
        return self.client.delete_role(role_name)

    def put_function_policy(self) -> types.Response:
        function_role_name = self.get_function_role_name()
        policy = policies.LAMBDA_FUNCTION_POLICY.copy()
        policy_name = self.config.get_function_policy_name()
        group_name = self.config.get_schedule_group_name(onetime=True)
        schedule_role_name = self.config.get_schedule_role_name()
        resources = (
            self.ARN(f"scheduler:schedule/{group_name}/*"),
            self.ARN(f"iam:role/{schedule_role_name}"),
            self.ARN(f"sns:{self.config.get_sns_topic_name()}"),
        )
        for idx, resource in enumerate(resources):
            policy["Statement"][idx]["Resource"] = resource
        return self.client.put_role_policy(function_role_name, policy_name, policy)

    def delete_function_policy(self) -> types.Response:
        function_role_name = self.get_function_role_name()
        policy_name = self.config.get_function_policy_name()
        return self.client.delete_role_policy(function_role_name, policy_name)

    def get_schedule_group(self, onetime: bool = False) -> types.ScheduleGroupResponse:
        group_name = self.config.get_schedule_group_name(onetime=onetime)
        return self.client.get_schedule_group(group_name)

    def create_schedule_group(
        self,
        onetime: bool = False,
    ) -> types.CreateScheduleGroupResponse:
        group_name = self.config.get_schedule_group_name(onetime=onetime)
        while True:
            try:
                return self.client.create_schedule_group(group_name)
            except exceptions.AlreadyExistsError:
                try:
                    other_group = self.get_schedule_group()
                except exceptions.NotFound:
                    pass
                else:
                    if other_group["State"] == "DELETING":
                        time.sleep(DEFAULT_RETRY_DELAY)
                        continue
                raise

    def delete_schedule_group(self, onetime: bool = False) -> types.Response:
        group_name = self.config.get_schedule_group_name(onetime=onetime)
        return self.client.delete_schedule_group(group_name)

    @aws_retry(
        max_attempts=4,
        delay=4,
        retry_exceptions=exceptions.ValidationError,
        pattern=r"Scheduler.*role",
    )
    def create_schedule(
        self,
        schedule: Schedule,
        onetime: bool = False,
    ) -> types.CreateScheduleResponse:
        role_name = self.config.get_schedule_role_name()
        schedule_name = self.config.get_schedule_name(schedule)
        group_name = self.config.get_schedule_group_name(onetime=onetime)

        task = types.ScheduleTask(
            path=schedule.path,
            args=schedule.args,
            kwargs=schedule.kwargs,
            context={
                "ScheduleArn": "<aws.scheduler.schedule-arn> ",
                "ScheduledTime": "<aws.scheduler.scheduled-time>",
                "ExecutionId": "<aws.scheduler.execution-id>",
                "AttemptNumber": "<aws.scheduler.attempt-number>",
                "Expression": schedule.expression,
            },
        )
        return self.client.create_schedule(
            name=schedule_name,
            group_name=group_name,
            expression=schedule.expression,
            timezone=schedule.timezone,
            time_window=schedule.time_window,
            dead_letter_arn=schedule.dead_letter_arn,
            start_date=schedule.start_date,
            end_date=schedule.end_date,
            kms_key=schedule.kms_key,
            target_arn=self.ARN(f"lambda:function:{self.config.function_name}"),
            role_arn=self.ARN(f"iam:role/{role_name}"),
            target_input={"task": task},
        )

    def create_sns_topic(self) -> types.CreateSNSTopicResponse:
        return self.client.create_sns_topic(self.config.get_sns_topic_name())

    def delete_sns_topic(self) -> types.Response:
        topic_arn = self.ARN(f"sns:{self.config.get_sns_topic_name()}")

        for sub in self.client.list_subscriptions_by_topic(topic_arn=topic_arn)[
            "Subscriptions"
        ]:
            self.client.sns_unsubscribe(sub["SubscriptionArn"])
        return self.client.delete_sns_topic(topic_arn)

    def add_sns_permission(self) -> types.Response:
        topic_arn = self.ARN(f"sns:{self.config.get_sns_topic_name()}")
        return self.client.add_lambda_permission(
            function_name=self.config.function_name,
            statement_id=self.config.get_sns_statement_id(),
            action="lambda:InvokeFunction",
            principal="sns.amazonaws.com",
            source_arn=topic_arn,
            source_account=self.account_id,
        )

    def remove_sns_permission(self) -> types.Response:
        return self.client.remove_lambda_permission(
            function_name=self.config.function_name,
            statement_id=self.config.get_sns_statement_id(),
        )

    def sns_subscribe(self) -> types.CreateSubscriptionResponse:
        topic_arn = self.ARN(f"sns:{self.config.get_sns_topic_name()}")
        function_arn = self.ARN(f"lambda:function:{self.config.function_name}")
        return self.client.sns_subscribe(
            topic_arn,
            protocol="lambda",
            endpoint=function_arn,
        )


_default_app = Seda()
task = _default_app.task
schedule = _default_app.schedule
