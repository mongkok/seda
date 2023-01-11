from seda import types

POLICY_VERSION: types.PolicyVersion = "2012-10-17"

SCHEDULE_TRUST_POLICY = types.Policy(
    Version=POLICY_VERSION,
    Statement=[
        {
            "Effect": "Allow",
            "Action": "sts:AssumeRole",
            "Principal": {
                "Service": "scheduler.amazonaws.com",
            },
        },
    ],
)

LAMBDA_INVOKE_POLICY = types.Policy(
    Version=POLICY_VERSION,
    Statement=[
        {
            "Effect": "Allow",
            "Action": ["lambda:InvokeFunction"],
            "Resource": [],
        },
    ],
)

LAMBDA_FUNCTION_POLICY = types.Policy(
    Version=POLICY_VERSION,
    Statement=[
        {
            "Effect": "Allow",
            "Action": "scheduler:CreateSchedule",
            "Resource": [],
        },
        {
            "Effect": "Allow",
            "Action": "iam:PassRole",
            "Resource": [],
        },
        {
            "Effect": "Allow",
            "Action": "sns:Publish",
            "Resource": [],
        },
    ],
)
