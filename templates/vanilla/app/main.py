from datetime import datetime

from seda import Seda

seda = Seda()


@seda.schedule("cron(* * * * ? *)", args=("minutes",))
async def myschedule(timespec: str = "auto") -> None:
    seda.log.info(f"myschedule: {datetime.now().isoformat(timespec=timespec)}")


@seda.task
async def mytask(timespec: str = "auto") -> None:
    seda.log.info(f"mytask: {datetime.now().isoformat(timespec=timespec)}")
