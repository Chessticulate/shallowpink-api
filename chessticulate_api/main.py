"""app.main

Contains the main FastAPI object definition.

Variables:
    chess_app
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from chessticulate_api import models, routers


@asynccontextmanager
async def lifespan():
    """Setup DB"""
    await models.init_db()
    yield


app = FastAPI(lifespan=lifespan)


app.include_router(routers.v1.router)
