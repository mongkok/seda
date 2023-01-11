import typing as t

from fastapi import APIRouter

from app.api.tasks import mytask

router = APIRouter()


@router.get("/")
async def myendpoint() -> t.Dict[str, t.Any]:
    return {"task": await mytask()}
