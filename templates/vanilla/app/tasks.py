from datetime import datetime

from seda import task


@task
async def mytask(timespec: str = "auto") -> str:
    return datetime.now().isoformat(timespec=timespec)
