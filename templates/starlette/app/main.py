from datetime import datetime

from seda import Seda
from starlette.applications import Starlette
from starlette.routing import Mount

from app.api import routes

app = Starlette(routes=[Mount("", routes=routes)])
seda = Seda(app)


@seda.schedule("cron(* * * * ? *)", args=("minutes",))
async def myschedule(timespec: str = "auto") -> None:
    seda.log.info(f"myschedule: {datetime.now().isoformat(timespec=timespec)}")


@seda.task
async def mytask(timespec: str = "auto") -> None:
    seda.log.info(f"mytask: {datetime.now().isoformat(timespec=timespec)}")
