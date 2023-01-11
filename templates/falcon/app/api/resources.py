import json

import falcon

from app.api.tasks import mytask


class MyResource:
    async def on_get(self, req: falcon.Request, resp: falcon.Response) -> None:
        resp.content_type = "application/json"
        resp.text = json.dumps({"task": await mytask()})
        resp.status = falcon.HTTP_200
