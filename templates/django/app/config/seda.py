from datetime import datetime

from seda import Seda

from app.config.asgi import application

seda = Seda(application)


@seda.schedule("cron(* * * * ? *)", args=("minutes",))
async def myschedule(timespec: str = "auto") -> None:
    seda.log.info(f"myschedule: {datetime.now().isoformat(timespec=timespec)}")


@seda.task
async def mytask(timespec: str = "auto") -> None:
    seda.log.info(f"mytask: {datetime.now().isoformat(timespec=timespec)}")
