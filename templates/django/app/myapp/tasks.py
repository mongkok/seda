from datetime import datetime

from seda import task


@task
def mytask(timespec: str = "auto") -> str:
    return datetime.now().isoformat(timespec=timespec)
