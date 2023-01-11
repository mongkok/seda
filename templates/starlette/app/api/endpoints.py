from starlette.endpoints import HTTPEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.api.tasks import mytask


class MyEndpoint(HTTPEndpoint):
    async def get(self, request: Request) -> JSONResponse:
        return JSONResponse({"task": await mytask()})
