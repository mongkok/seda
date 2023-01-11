# SEDA

<p align="center">
    <em>A Python toolkit to build <b>S</b>erverless <b>E</b>vent-<b>D</b>riven <b>A</b>pplications on AWS.</em>
    <br><em>Documentation: <a href="https://seda.domake.io"><del>https://seda.domake.io</del></a> (pending)</em>
    <br><em><b>Examples: <a href="https://github.com/mongkok/seda/tree/main/templates">/templates</a></b></em>
</p>
<p align="center">
    <a href="https://github.com/mongkok/seda/actions">
        <img src="https://github.com/mongkok/seda/actions/workflows/test-suite.yml/badge.svg" alt="Test">
    </a>
    <a href="https://codecov.io/gh/mongkok/seda">
        <img src="https://img.shields.io/codecov/c/github/mongkok/seda?color=%2334D058" alt="Coverage">
    </a>
    <a href="https://www.codacy.com/gh/mongkok/seda/dashboard">
        <img src="https://app.codacy.com/project/badge/Grade/ee6de85d485d4d9fbb5592ac95cec155" alt="Codacy">
    </a>
    <a href="https://pypi.org/project/seda">
        <img src="https://img.shields.io/pypi/v/seda" alt="Package version">
    </a>
</p>

## What

*   [x] Allows to schedule **periodic** and **one-time** tasks on **EventBridge Scheduler**.
*   [x] Simplifies creating, executing, and managing asynchronous task using SNS messages and Lambda events.
*   [x] Includes `@decorators` in addition to `@app.decorators` for reusable apps.
*   [x] Works well with any framework, interface,  toolkit... see [/templates](https://github.com/mongkok/seda/tree/main/templates).
*   [x] Provides Serverless framework support via [plugin](https://github.com/mongkok/serverless-seda).
*   [ ] Other event sources, e.g. CloudWatch, Kinesis, Dynamodb, SQS, S3...
*   [ ] Easy to read documentation and tests.
*   [ ] SAM templates and CDK support.

## Installation

```sh
pip install seda
```

## Example

**main.py**:

```py
from datetime import datetime

from seda import Seda

seda = Seda()


@seda.schedule("cron(* * * * ? *)", args=("minutes",))
async def myschedule(timespec: str = "auto") -> None:
    seda.log.info(f"myschedule: {datetime.now().isoformat(timespec=timespec)}")


@seda.task
async def mytask(timespec: str = "auto") -> None:
    seda.log.info(f"mytask: {datetime.now().isoformat(timespec=timespec)}")
```
**`main.seda`** is an AWS Lambda handler in charge of managing the creation and execution of our tasks.

*   **`@schedule`:** creates a new periodic "schedule" on EventBridge at deployment time.
*   **`@task`:** creates one-time asynchronous tasks at runtime:
    *   SNS messages: default
    *   Lambda events:  `@task(service="lambda")`
    *   EventBridge one-time schedules: `mytask.at("...")`

For reusable apps use `@task` and `@schedule` decorators that always points to the currently active `Seda` instance:

**tasks.py**:

```py
from datetime import datetime

from seda import task


@task
async def mytask(timespec: str = "auto") -> str:
    return datetime.now().isoformat(timespec=timespec)
```

## Tasks

```py
await mytask()
```

*   **SNS**: This task is executed asynchronously by sending a message to a previously subscribed SNS topic.
*   **λ**: A second option is to directly invoke the Lambda function `InvocationType=Event` by adding the *"service"* option to the task decorator `@task(service="lambda")`.
*   **test**: For local and test environments the task is executed synchronously by default.

## One-time schedules
 
```py
from datetime import datetime, timedelta

mytask.at(datetime.now() + timedelta(minutes=5))
```

The **`.at(datetime)`** method is equivalent to **`@schedule("at(datetime)")`**.

These one-time schedules are created under a second EventBridge Schedule Group (group 1 -  N schedules) so after a new deployment we can clean the group of periodic schedules but keeping our one-time schedules.

## `@schedule`

| SEDA / AWS | TYPE | EXAMPLE |
| ---------- | ---- | ------- |
| expression<br />[ScheduleExpression](https://docs.aws.amazon.com/scheduler/latest/APIReference/API_CreateSchedule.html#scheduler-CreateSchedule-request-ScheduleExpression) | `str` | - `"rate(5 minutes)"`<br />- `"cron(*/5 * * * ? *)"`<br />- `"at(2025-10-26T12:00:00)"` |
| args<br />- | `Optional[Sequence]` | `("a", "b")` |
| kwargs<br />- | `Optional[Dict]` | `{"a": "b"}` |
| timezone<br />[ScheduleExpressionTimezone](https://docs.aws.amazon.com/scheduler/latest/APIReference/API_CreateSchedule.html#scheduler-CreateSchedule-request-ScheduleExpressionTimezone) | `Optional[str]` | `"Asia/Saigon"` |
| time_window<br />[FlexibleTimeWindow](https://docs.aws.amazon.com/scheduler/latest/APIReference/API_CreateSchedule.html#scheduler-CreateSchedule-request-FlexibleTimeWindow) |`Optional[ScheduleTimeWindow]` | `{"Mode": "FLEXIBLE", "MaximumWindowInMinutes": 15}` |
| retry_policy<br />[RetryPolicy](https://docs.aws.amazon.com/scheduler/latest/APIReference/API_Target.html#scheduler-Type-Target-RetryPolicy) | `Optional[ScheduleRetryPolicy]` | `{"MaximumEventAgeInSeconds": 60, "MaximumRetryAttempts": 10}` |
| start_date<br />[StartDate](https://docs.aws.amazon.com/scheduler/latest/APIReference/API_CreateSchedule.html#scheduler-CreateSchedule-request-StartDate) | `Optional[datetime]` | `datetime.now() + timedelta(minutes=5)` |
| end_date<br />[EndDate](https://docs.aws.amazon.com/scheduler/latest/APIReference/API_CreateSchedule.html#scheduler-CreateSchedule-request-EndDate) | `Optional[datetime]` | `datetime.now() + timedelta(days=5)` |
| dead_letter_arn<br />[DeadLetterConfig.Arn](https://docs.aws.amazon.com/scheduler/latest/APIReference/API_Target.html#scheduler-Type-Target-DeadLetterConfig) | `Optional[str]` | `"arn:aws:sqs:..."` |
| kms_key<br />[KmsKeyArn](https://docs.aws.amazon.com/scheduler/latest/APIReference/API_CreateSchedule.html#scheduler-CreateSchedule-request-KmsKeyArn) | `Optional[str]` | `"arn:aws:kms:..."` |

## CLI

SEDA CLI provides a list of commands to deploy, remove and debug SEDA resources on an **existing** Lambda function:

```sh
seda deploy --app main.seda -f myfunction
```

**Deploy `@schedule`, `@task`:**

*   Creates the Schedule Groups for periodic and one-time tasks
*   Creates N periodic schedules
*   Creates SNS topic and a Lambda subscription to this topic
*   Adds related IAM roles and policies

A second deployment removes the periodic task Schedule Group and creates a new one adding the new schedules.

We can also remove the deployed stack:

```sh
seda remove --app main.seda -f myfunction
```

**Remote Function Invocation**

Invoke Python interpreter:

```sh
seda python 'import sys;print(sys.version)' -f myfunction
```

Run shell commands:

```sh
seda shell env -f myfunction
```

## Serverless Framework

The plugin [serverless-seda](https://github.com/mongkok/serverless-seda) adds all SEDA CLI commands to Serverless framework CLI:

```sh
sls seda deploy
```

## ASGI

SEDA seamlessly integrates with ASGI applications by adding [Mangum](https://github.com/jordaneremieff/mangum) handler to `seda[asgi]`.

```sh
pip install seda[asgi]
```

**main.py**:

```py
from fastapi import FastAPI
from seda import Seda


app = FastAPI()
seda = Seda(app)
```

## Default handler

Add any callable as a handler to process any non-SEDA events:

```py
def myhandler(event, context):
    pass


seda = Seda(default_handler=myhandler)
```
