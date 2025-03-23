"""
This example demonstrates a FastAPI application with a lifespan context manager.
Instead of using a singleton, it defines variables in the app.state using the lifespan pattern.
The application includes endpoints to get and set a configuration value stored in the app state.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, Request
from fastapi.routing import APIRouter


class AppConfig:
    def __init__(self, initial_value=None):
        self.value = initial_value

    def get_value(self):
        return self.value

    def set_value(self, new_value):
        self.value = new_value


router = APIRouter()


def get_app_config(request: Request) -> AppConfig:
    return request.app.state.app_config


@router.get("/get_config_value")
async def get_value(config=Depends(get_app_config)) -> dict:
    return {"value": config.get_value()}


@router.post("/set_config_value/{new_value}")
async def set_value(new_value: str, config=Depends(get_app_config)) -> dict:
    config.set_value(new_value)
    return {"message": f"Config value updated to: {new_value}"}


@asynccontextmanager
async def lifespan(app: FastAPI):
    app_config = AppConfig(initial_value="Default Config Value")
    app.state.app_config = app_config
    yield
    print("End of app lifespan")


def create_app() -> FastAPI:
    app = FastAPI(lifespan=lifespan)
    app.include_router(router)
    return app


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(create_app(), host="0.0.0.0", port=8000)
