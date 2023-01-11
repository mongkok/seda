from datetime import datetime

from fastapi import FastAPI
from seda import Seda

from app.api import api_router
from app.settings import settings

app = FastAPI(root_path=settings.ROOT_PATH)
app.include_router(api_router)
seda = Seda(app)


@seda.schedule("cron(* * * * ? *)", args=("minutes",))
async def myschedule(timespec: str = "auto") -> None:
    seda.log.info(f"myschedule: {datetime.now().isoformat(timespec=timespec)}")


@seda.task
async def mytask(timespec: str = "auto") -> None:
    seda.log.info(f"mytask: {datetime.now().isoformat(timespec=timespec)}")
