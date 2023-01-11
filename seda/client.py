import base64
import json
import sys
import typing as t
from datetime import datetime

from botocore.client import BaseClient

from seda import exceptions, types
from seda.session import Session

if sys.version_info < (3, 8):  # pragma: no cover
    from typing_extensions import Literal
else:  # pragma: no cover
    from typing import Literal


DEFAULT_RETRY_DELAY = 2


class Client:
    def __init__(self, session: Session) -> None:
        self._client_cache: t.Dict[str, BaseClient] = {}
        self.session = session

    def client(self, service_name: str) -> BaseClient:
        if service_name not in self._client_cache:
            self._client_cache[service_name] = self.session.client(service_name)
        return self._client_cache[service_name]

    def get_identity(self) -> types.IdentityResponse:
        return self.client("sts").get_caller_identity()

    def get_role(self, role_name: str) -> types.RoleResponse:
        client = self.client("iam")
        try:
            return client.get_role(RoleName=role_name)
        except client.exceptions.NoSuchEntityException as exc:
            raise exceptions.NotFound(exc)

    def create_role(
        self,
        name: str,
        trust_policy: types.Policy,
        policy: types.Policy,
    ) -> types.RoleResponse:
        client = self.client("iam")
        try:
            result = client.create_role(
                RoleName=name,
                AssumeRolePolicyDocument=json.dumps(trust_policy),
            )
        except client.exceptions.EntityAlreadyExistsException as exc:
            raise exceptions.AlreadyExistsError(exc)
        try:
            self.put_role_policy(
                role_name=name,
                policy_name=name,
                policy_document=policy,
            )
        except client.exceptions.MalformedPolicyDocumentException as exc:
            self.delete_role(name=name)
            raise exc
        return result

    def put_role_policy(
        self,
        role_name: str,
        policy_name: str,
        policy_document: types.Policy,
    ) -> types.Response:
        client = self.client("iam")
        return client.put_role_policy(
            RoleName=role_name,
            PolicyName=policy_name,
            PolicyDocument=json.dumps(policy_document),
        )

    def delete_role(self, name: str) -> types.Response:
        client = self.client("iam")
        try:
            policies = client.list_role_policies(RoleName=name)
        except client.exceptions.NoSuchEntityException as exc:
            raise exceptions.NotFound(exc)

        for policy_name in policies["PolicyNames"]:
            self.delete_role_policy(name, policy_name)
        return client.delete_role(RoleName=name)

    def delete_role_policy(self, role_name: str, policy_name: str) -> types.Response:
        client = self.client("iam")
        try:
            return client.delete_role_policy(RoleName=role_name, PolicyName=policy_name)
        except client.exceptions.NoSuchEntityException as exc:
            raise exceptions.NotFound(exc)

    def get_function(self, name: str) -> types.LambdaFunctionResponse:
        client = self.client("lambda")
        try:
            return client.get_function(FunctionName=name)
        except client.exceptions.ResourceNotFoundException as exc:
            raise exceptions.NotFound(exc)

    def invoke_function(
        self,
        name: str,
        *,
        invocation_type: Literal[
            "Event", "RequestResponse", "DryRun"
        ] = "RequestResponse",
        client_context: t.Optional[t.Dict[str, t.Any]] = None,
        payload: t.Optional[t.Dict[str, t.Any]] = None,
        log_type: t.Optional[Literal["Tail"]] = "Tail",
        qualifier: str = "$LATEST",
    ) -> types.InvokeFunctionResponse:
        client = self.client("lambda")
        try:
            return client.invoke(
                FunctionName=name,
                InvocationType=invocation_type,
                ClientContext=base64.b64encode(
                    json.dumps(client_context or {}).encode()
                ).decode(),
                Payload=json.dumps(payload or {}),
                LogType=log_type,
                Qualifier=qualifier,
            )
        except client.exceptions.ResourceNotFoundException as exc:
            raise exceptions.NotFound(exc)

    def add_lambda_permission(
        self,
        function_name: str,
        *,
        statement_id: str,
        action: str,
        principal: str,
        source_arn: t.Optional[str] = None,
        source_account: t.Optional[str] = None,
    ) -> types.Response:
        client = self.client("lambda")
        data: t.Dict[str, t.Any] = {
            "FunctionName": function_name,
            "StatementId": statement_id,
            "Action": action,
            "Principal": principal,
        }
        if source_arn:
            data["SourceArn"] = source_arn
        if source_account:
            data["SourceAccount"] = source_account
        try:
            return client.add_permission(**data)
        except client.exceptions.ResourceConflictException as exc:
            raise exceptions.AlreadyExistsError(exc)
        except client.exceptions.ResourceNotFoundException as exc:
            raise exceptions.NotFound(exc)

    def remove_lambda_permission(
        self,
        function_name: str,
        statement_id: str,
    ) -> types.Response:
        client = self.client("lambda")
        try:
            return client.remove_permission(
                FunctionName=function_name,
                StatementId=statement_id,
            )
        except client.exceptions.ResourceNotFoundException as exc:
            raise exceptions.NotFound(exc)

    def get_schedule_group(self, name: str) -> types.ScheduleGroupResponse:
        client = self.client("scheduler")
        try:
            return client.get_schedule_group(Name=name)
        except client.exceptions.ResourceNotFoundException as exc:
            raise exceptions.NotFound(exc)

    def create_schedule_group(self, name: str) -> types.CreateScheduleGroupResponse:
        client = self.client("scheduler")
        try:
            return client.create_schedule_group(Name=name)
        except client.exceptions.ConflictException as exc:
            raise exceptions.AlreadyExistsError(exc)

    def delete_schedule_group(self, name: str) -> types.Response:
        client = self.client("scheduler")
        try:
            return client.delete_schedule_group(Name=name)
        except client.exceptions.ResourceNotFoundException as exc:
            raise exceptions.NotFound(exc)

    def list_schedules(self, group_name: str) -> types.ListSchedulesResponse:
        client = self.client("scheduler")
        try:
            return client.list_schedules(GroupName=group_name)
        except client.exceptions.ResourceNotFoundException as exc:
            raise exceptions.NotFound(exc)

    def get_schedule(self, name: str, group_name: str) -> types.ScheduleResponse:
        client = self.client("scheduler")
        try:
            return client.get_schedule(Name=name, GroupName=group_name)
        except client.exceptions.ResourceNotFoundException as exc:
            raise exceptions.NotFound(exc)

    def create_schedule(
        self,
        name: str,
        group_name: str,
        expression: str,
        target_arn: str,
        role_arn: str,
        *,
        timezone: t.Optional[str] = None,
        target_input: t.Optional[t.Dict[str, t.Any]] = None,
        time_window: t.Optional[types.ScheduleTimeWindow] = None,
        dead_letter_arn: t.Optional[str] = None,
        retry_policy: t.Optional[types.ScheduleRetryPolicy] = None,
        start_date: t.Optional[datetime] = None,
        end_date: t.Optional[datetime] = None,
        kms_key: t.Optional[str] = None,
    ) -> types.CreateScheduleResponse:
        client = self.client("scheduler")

        if time_window is None:
            time_window = types.ScheduleTimeWindow(Mode="OFF")
        data: t.Dict[str, t.Any] = {
            "Name": name,
            "GroupName": group_name,
            "ScheduleExpression": expression,
            "Target": {
                "Arn": target_arn,
                "RoleArn": role_arn,
                "Input": json.dumps(target_input or {}),
            },
            "FlexibleTimeWindow": time_window,
        }
        if timezone is not None:
            data["ScheduleExpressionTimezone"] = timezone
        if retry_policy is not None:
            data["RetryPolicy"] = retry_policy
        if start_date is not None:
            data["StartDate"] = start_date
        if end_date is not None:
            data["EndDate"] = end_date
        if kms_key is not None:
            data["KmsKeyArn"] = kms_key
        if dead_letter_arn is not None:
            data["Target"]["DeadLetterConfig"] = {"Arn": dead_letter_arn}
        try:
            return client.create_schedule(**data)
        except client.exceptions.ConflictException as exc:
            raise exceptions.AlreadyExistsError(exc)
        except client.exceptions.ValidationException as exc:
            raise exceptions.ValidationError(exc)
        except client.exceptions.ResourceNotFoundException as exc:
            raise exceptions.NotFound(exc)

    def delete_schedule(self, name: str, group_name: str) -> types.Response:
        client = self.client("scheduler")
        try:
            return client.delete_schedule(Name=name, GroupName=group_name)
        except client.exceptions.ResourceNotFoundException as exc:
            raise exceptions.NotFound(exc)

    def create_sns_topic(self, name: str) -> types.CreateSNSTopicResponse:
        client = self.client("sns")
        try:
            return client.create_topic(Name=name)
        except client.exceptions.ConflictException as exc:
            raise exceptions.AlreadyExistsError(exc)

    def delete_sns_topic(self, topic_arn: str) -> types.Response:
        client = self.client("sns")
        try:
            return client.delete_topic(TopicArn=topic_arn)
        except client.exceptions.AlreadyDeletedError as exc:
            raise exceptions.NotFound(exc)

    def sns_subscribe(
        self,
        topic_arn: str,
        *,
        protocol: types.SubscriptionProtocol,
        endpoint: str,
    ) -> types.CreateSubscriptionResponse:
        client = self.client("sns")
        return client.subscribe(
            TopicArn=topic_arn,
            Protocol=protocol,
            Endpoint=endpoint,
        )

    def list_subscriptions_by_topic(
        self,
        topic_arn: str,
    ) -> types.ListSubscriptionsResponse:
        client = self.client("sns")
        try:
            return client.list_subscriptions_by_topic(TopicArn=topic_arn)
        except client.exceptions.NotFoundException as exc:
            raise exceptions.NotFound(exc)

    def sns_unsubscribe(self, subscription_arn: str) -> types.Response:
        client = self.client("sns")
        return client.unsubscribe(SubscriptionArn=subscription_arn)

    def sns_publish(
        self,
        target_arn: str,
        message: t.Dict[str, t.Any],
    ) -> types.SNSPublishResponse:
        client = self.client("sns")
        return client.publish(TargetArn=target_arn, Message=json.dumps(message))
