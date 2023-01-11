from starlette.routing import Route

from app.api import endpoints

routes = [
    Route("/", endpoint=endpoints.MyEndpoint),
]
