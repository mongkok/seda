from botocore.exceptions import BotoCoreError


class AWSError(Exception):
    def __init__(self, exc: BotoCoreError) -> None:
        self.detail = str(exc)
        self.operation_name = exc.operation_name
        self.meta = exc.response["ResponseMetadata"]
        error = exc.response["Error"]
        self.code = error["Code"]
        self.msg = error["Message"]
        super().__init__(self.msg)

    def __repr__(self) -> str:
        return f"{self.code}(code={self.meta['HTTPStatusCode']}, msg={self.msg!r})"


class AlreadyExistsError(AWSError):
    pass


class NotFound(AWSError):
    pass


class ValidationError(AWSError):
    pass


class ImportPathError(Exception):
    pass
