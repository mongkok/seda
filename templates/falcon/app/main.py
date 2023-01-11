from datetime import datetime

import falcon.asgi
from seda import Seda

from app.api import resources

app = falcon.asgi.App()
app.add_route("/", resources.MyResource())
seda = Seda(app)


@seda.schedule("cron(* * * * ? *)", args=("minutes",))
async def myschedule(timespec: str = "auto") -> None:
    seda.log.info(f"myschedule: {datetime.now().isoformat(timespec=timespec)}")


@seda.task
async def mytask(timespec: str = "auto") -> None:
    seda.log.info(f"mytask: {datetime.now().isoformat(timespec=timespec)}")
