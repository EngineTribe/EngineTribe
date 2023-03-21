from typing import Any, Callable
from fastapi import APIRouter as FastAPIRouter


class APIRouter(FastAPIRouter):
    def add_api_route(
            self, path: str, endpoint: Callable[..., Any], *,
            include_in_schema: bool = True, **kwargs: Any
    ) -> None:
        if path.endswith("/"):
            alternate_path = path[:-1]
        else:
            alternate_path = path + "/"
        super().add_api_route(
            alternate_path, endpoint, include_in_schema=False, **kwargs)
        return super().add_api_route(
            path, endpoint, include_in_schema=include_in_schema, **kwargs)
