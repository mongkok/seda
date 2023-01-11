import sys
import typing as t
from datetime import datetime

from botocore.response import StreamingBody

if sys.version_info < (3, 8):  # pragma: no cover
    from typing_extensions import Literal, Protocol, TypedDict
else:  # pragma: no cover
    from typing import Literal, Protocol, TypedDict

if sys.version_info < (3, 11):
    from typing_extensions import NotRequired
else:
    from typing import NotRequired

LambdaEvent = t.Dict[str, t.Any]
Lifespan = Literal["auto", "on", "off"]
PolicyVersion = Literal["2012-10-17", "2012-10-17", "2008-10-17"]
SubscriptionProtocol = Literal[
    "http",
    "https",
    "email",
    "email-json",
    "sms",
    "sqs",
    "application",
    "lambda",
    "firehose",
]


class LambdaContext(Protocol):
    aws_request_id: str
    client_context: t.Optional[t.Type]
    function_name: str
    function_version: str
    identity: t.Optional[t.Type]
    invoked_function_arn: str
    log_group_name: str
    log_stream_name: str
    memory_limit_in_mb: int
    get_remaining_time_in_millis: t.Callable[[], int]


class Statement(TypedDict):
    Action: NotRequired[t.Union[str, t.Sequence]]
    Condition: NotRequired[t.Dict[str, t.Any]]
    Effect: Literal["Allow", "Deny"]
    Id: NotRequired[str]
    Sid: NotRequired[str]
    Principal: NotRequired[t.Dict[str, t.Any]]
    Resource: NotRequired[t.Union[str, t.Sequence]]
    NotAction: NotRequired[t.Union[str, t.Sequence]]
    NotPrincipal: NotRequired[t.Dict[str, t.Any]]
    NotResource: NotRequired[t.Union[str, t.Sequence]]


class Policy(TypedDict):
    Statement: t.List[Statement]
    Version: NotRequired[PolicyVersion]


class ResponseMetadata(TypedDict):
    HTTPHeaders: t.Dict[str, str]
    HTTPStatusCode: int
    RequestId: str
    RetryAttempts: int


class Response(TypedDict):
    ResponseMetadata: ResponseMetadata


class IdentityResponse(Response):
    Account: str
    Arn: str
    UserId: str


class Role(TypedDict):
    Arn: str
    AssumeRolePolicyDocument: Policy
    CreateDate: datetime
    Path: str
    RoleId: str
    RoleName: str


class RoleResponse(Response):
    Role: Role


class LambdaFunctionResponse(Response):
    Code: t.Dict[str, str]
    Configuration: t.Dict[str, t.Any]
    Tags: t.Dict[str, str]


class InvokeFunctionResponse(Response):
    StatusCode: int
    FunctionError: str
    LogResult: str
    ExecutedVersion: str
    Payload: StreamingBody


class ScheduleGroupResponse(Response):
    Name: str
    State: Literal["ACTIVE", "DELETING"]


class CreateScheduleGroupResponse(Response):
    ScheduleGroupArn: str


class ScheduleRetryPolicy(TypedDict):
    MaximumEventAgeInSeconds: NotRequired[int]
    MaximumRetryAttempts: NotRequired[int]


class ScheduleDeadLetterConfig(TypedDict):
    Arn: str


class ScheduleTarget(TypedDict):
    Arn: str
    Input: t.Dict[str, t.Any]
    RoleArn: str
    RetryPolicy: ScheduleRetryPolicy
    DeadLetterConfig: NotRequired[ScheduleDeadLetterConfig]


class ScheduleTimeWindow(TypedDict):
    MaximumWindowInMinutes: NotRequired[int]
    Mode: Literal["OFF", "FLEXIBLE"]


class CreateScheduleResponse(Response):
    ScheduleArn: str


class ListSchedule(TypedDict):
    Arn: str
    CreationDate: datetime
    GroupName: str
    LastModificationDate: datetime
    Name: str
    State: str
    Target: ScheduleTarget


class Schedule(ListSchedule):
    FlexibleTimeWindow: ScheduleTimeWindow
    ScheduleExpression: str
    ScheduleExpressionTimezone: str


class ScheduleResponse(Schedule, Response):
    pass


class ListSchedulesResponse(Response):
    Schedules: t.Tuple[ListSchedule]


class CreateSNSTopicResponse(Response):
    TopicArn: str


class SNSPublishResponse(Response):
    MessageId: str


class CreateSubscriptionResponse(Response):
    SubscriptionArn: str


class Subscription(TypedDict):
    Endpoint: str
    Owner: str
    Protocol: SubscriptionProtocol
    SubscriptionArn: str
    TopicArn: str


class ListSubscriptionsResponse(Response):
    Subscriptions: t.List[Subscription]


class SNSRecord(TypedDict):
    Message: str
    MessageAttributes: t.Dict[str, t.Any]
    MessageId: str
    Signature: str
    SignatureVersion: str
    SigningCertUrl: str
    Subject: NotRequired[str]
    Timestamp: str
    TopicArn: str
    Type: str
    UnsubscribeUrl: str


class EventRecord(TypedDict):
    EventSource: str
    EventVersion: str
    EventSubscriptionArn: str
    Sns: SNSRecord


class EventTask(TypedDict):
    path: str
    args: t.Optional[t.Sequence]
    kwargs: t.Optional[t.Dict[str, t.Any]]


class ScheduleTaskContext(TypedDict):
    AttemptNumber: str
    ExecutionId: str
    Expression: str
    ScheduleArn: str
    ScheduledTime: str


class ScheduleTask(EventTask):
    context: ScheduleTaskContext
